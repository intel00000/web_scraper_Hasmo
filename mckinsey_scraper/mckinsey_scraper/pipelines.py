# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class MckinseyScraperPipeline:
    def process_item(self, item, spider):
        return item


import datetime
from scrapy.exporters import JsonLinesItemExporter, CsvItemExporter

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


class ExportPipeline:
    def open_spider(self, spider):
        # Use the spider's name in the file names
        json_output_file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            "raw",
            f"{spider.name}_{timestamp}.json",
        )
        csv_output_file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "data",
            "raw",
            f"{spider.name}_{timestamp}.csv",
        )
        self.json_output_file = open(json_output_file_path, "wb")
        self.csv_output_file = open(csv_output_file_path, "wb")

        # Initialize the exporters
        self.json_exporter = JsonLinesItemExporter(
            self.json_output_file, encoding="utf-8", indent=4
        )
        self.csv_exporter = CsvItemExporter(self.csv_output_file, encoding="utf-8")

        # Start exporting
        self.json_exporter.start_exporting()
        self.csv_exporter.start_exporting()

    def process_item(self, item, spider):
        # Export the data
        self.json_exporter.export_item(item)
        self.csv_exporter.export_item(item)
        return item

    def close_spider(self, spider):
        # Finish exporting and close the files
        self.json_exporter.finish_exporting()
        self.json_output_file.close()
        self.csv_exporter.finish_exporting()
        self.csv_output_file.close()
        spider.logger.info("ExportPipeline closed the files.")


from openai import OpenAI
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")

# Define the word count limit as a macro
WORD_COUNT_LIMIT = 50  # You can adjust this as needed


class OpenAIPipeline:
    def __init__(self):
        self.client = None

    def open_spider(self, spider):
        load_dotenv(dotenv_path=env_path)
        # Set the OpenAI API key
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    def process_item(self, item, spider):
        article_text = item.get("article_text", "")
        if article_text:
            summary = self.summarize_content(article_text)
            item["summary"] = summary
            spider.logger.info(f"Generated summary: {summary}")
        else:
            item["summary"] = "No article text found."

        return item

    def summarize_content(self, article_text):
        try:
            # Prepare the prompt for summarization
            prompt = (
                f"Summarize the following content in {WORD_COUNT_LIMIT} words or fewer, "
                "you will only return summary, do not include extra information:\n\n"
                f"{article_text}"
            )

            # Call the OpenAI API
            chat_completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=WORD_COUNT_LIMIT,
                temperature=0.7,
                service_tier="default",
                stream=False,
            )

            # Extract the summary from the response
            summary = chat_completion.choices[0].message.content.strip()
            return summary

        except Exception as e:
            print(f"Failed to generate summary: {e}")
            return "Failed to generate summary."


import gspread
import time
from oauth2client.service_account import ServiceAccountCredentials

# Set up the Google Sheets and Drive API credentials and scope
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials_path = os.path.join(os.path.dirname(env_path), "credentials.json")


# GoogleSheetsPipeline class for exporting data to Google Sheets
class GoogleSheetsPipeline:
    def __init__(self):
        self.spider = None

        self.spreadsheet_name = "Web Scraping Data"
        self.spreadsheet = None

        self.worksheet_name = "Data"
        self.worksheet = None

        self.credentials = None
        self.gspread_client = None

    def open_spider(self, spider):
        self.spider = spider
        self.worksheet_name = f"{spider.name}_Data"

        # Load the Google Sheets and Drive API credentials
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        self.gspread_client = gspread.authorize(self.credentials)

        # Access Google Sheets, first try opening the spreadsheet, if it doesn't exist, create a new one
        try:
            self.spreadsheet = self.gspread_client.open(self.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            self.spreadsheet = self.gspread_client.create(self.spreadsheet_name)

        # Set permissions
        self.spreadsheet.share(None, perm_type="anyone", role="writer")

        try:
            self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(
                title=self.worksheet_name, rows="100", cols="20"
            )

    def find_next_available_row(self, worksheet):
        str_list = list(filter(None, worksheet.col_values(1)))
        return len(str_list) + 1

    def find_column_by_header(self, worksheet, header_name):
        headers = worksheet.row_values(1)
        try:
            return headers.index(header_name) + 1
        except ValueError:
            return None

    def find_row_by_title(self, worksheet, title, title_column):
        titles = worksheet.col_values(title_column)
        try:
            return titles.index(title) + 1
        except ValueError:
            return None

    def update_worksheet(self, worksheet, data):
        if not isinstance(data, dict):
            self.spider.logger.error(
                f"Invalid data format: {data}. Expected a dictionary."
            )
            return

        existing_headers = worksheet.row_values(1)
        header_indices = {
            header: index + 1 for index, header in enumerate(existing_headers)
        }

        headers = list(data.keys())
        new_headers = [header for header in headers if header not in header_indices]

        if new_headers:
            existing_headers.extend(new_headers)
            cell_list = worksheet.range(1, 1, 1, len(existing_headers))
            for i, cell in enumerate(cell_list):
                cell.value = existing_headers[i]
            worksheet.update_cells(cell_list)
            header_indices = {
                header: index + 1 for index, header in enumerate(existing_headers)
            }

        title_column = self.find_column_by_header(worksheet, "title")
        if title_column is None:
            title_column = 1
            worksheet.update_cell(1, 1, "title")
            header_indices["title"] = 1

        title = data.get("title", "")
        row_num = self.find_row_by_title(worksheet, title, title_column)

        if row_num is None:
            row_num = self.find_next_available_row(worksheet)

        row_data = [""] * len(existing_headers)

        for header, value in data.items():
            col_num = header_indices.get(header)
            if col_num is not None:
                row_data[col_num - 1] = (
                    ",".join(value) if isinstance(value, list) else value
                )

        cell_list = worksheet.range(row_num, 1, row_num, len(existing_headers))

        for i, cell in enumerate(cell_list):
            cell.value = row_data[i]

        worksheet.update_cells(cell_list)
        time.sleep(3)

    def process_item(self, item, spider):
        if isinstance(item, dict):
            self.update_worksheet(self.worksheet, item)
            return item
        else:
            spider.logger.error(
                f"Unexpected item format: {item}. Expected a dictionary."
            )
            return None

    def close_spider(self, spider):
        spider.logger.info(
            f"GoogleSheetsPipeline finished processing and saved data to {self.spreadsheet.url}"
        )
