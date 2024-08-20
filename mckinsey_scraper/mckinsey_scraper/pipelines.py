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
        self.json_output_file = open(f"{spider.name}_{timestamp}.json", "wb")
        self.csv_output_file = open(f"{spider.name}_{timestamp}.csv", "wb")

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
load_dotenv(dotenv_path=env_path)

# Set the OpenAI API key
client = OpenAI(
    # This is the default and can be omitted
    api_key=os.getenv("OPENAI_API_KEY"),
)

# Define the word count limit as a macro
WORD_COUNT_LIMIT = 50  # You can adjust this as needed


class OpenAIPipeline:
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
            chat_completion = client.chat.completions.create(
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

# Load the Google Sheets and Drive API credentials
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
gspread_client = gspread.authorize(creds)


# GoogleSheetsPipeline class for exporting data to Google Sheets
class GoogleSheetsPipeline:
    def open_spider(self, spider):
        self.worksheet_name = "Web Scraping Data"
        self.spreadsheet_name = f"{spider.name}_Data"

        # Access or create the Google Sheet
        try:
            self.spreadsheet = gspread_client.open(self.spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            self.spreadsheet = gspread_client.create(self.spreadsheet_name)

        # Set permissions
        self.spreadsheet.share(None, perm_type="anyone", role="writer")

        # Access or create the worksheet
        try:
            self.worksheet = self.spreadsheet.worksheet(self.worksheet_name)
        except gspread.WorksheetNotFound:
            self.worksheet = self.spreadsheet.add_worksheet(
                title=self.worksheet_name, rows="100", cols="20"
            )

    def process_item(self, item, spider):
        self.update_worksheet(self.worksheet, item)
        return item

    def find_next_available_row(self, worksheet):
        str_list = list(
            filter(None, worksheet.col_values(1))
        )  # Find all non-empty rows in column 1
        return len(str_list) + 1

    def update_worksheet(self, worksheet, data):
        # Ensure data is a dictionary
        if not isinstance(data, dict):
            print(f"Unexpected data format: {data}. Expected a dictionary.")
            return

        # Get the existing headers from the first row
        existing_headers = worksheet.row_values(1)
        header_indices = {
            header: index + 1 for index, header in enumerate(existing_headers)
        }

        # Determine which headers are new and which already exist
        headers = list(data.keys())
        new_headers = [header for header in headers if header not in header_indices]

        # Update the existing headers with data
        next_row = self.find_next_available_row(worksheet)

        # If there are new headers, add them to the sheet
        if new_headers:
            for header in new_headers:
                new_col_num = len(existing_headers) + 1
                worksheet.update_cell(1, new_col_num, header)
                existing_headers.append(header)
                header_indices[header] = new_col_num

        # Prepare the row data to update all cells in a single request
        row_data = []
        for header in existing_headers:
            value = data.get(header, "")
            row_data.append(",".join(value) if isinstance(value, list) else value)

        # Prepare the cell range to update
        cell_list = worksheet.range(next_row, 1, next_row, len(existing_headers))

        # Assign values to the cell list
        for i, cell in enumerate(cell_list):
            cell.value = row_data[i]

        # Batch update the cells
        worksheet.update_cells(cell_list)
        time.sleep(1)  # Delay to respect API rate limits
