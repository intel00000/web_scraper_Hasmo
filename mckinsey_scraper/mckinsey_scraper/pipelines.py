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


class ExportPipeline:
    def open_spider(self, spider):
        # Use the spider's name in the file names
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
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


import os
import datetime
import gspread
from google.oauth2.service_account import Credentials

# Set the Google Sheets scope and credentials
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
SERVICE_ACCOUNT_FILE = os.path.join("configs", "credentials.json")

# Load the Google Sheets API credentials
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)


class GoogleSheetsPipeline:
    def open_spider(self, spider):
        # Initialize the Google Sheets client
        self.client = gspread.authorize(credentials)

        # Check or create a folder named after the BOT_NAME
        drive_service = build("drive", "v3", credentials=credentials)
        folder_name = spider.settings.get("BOT_NAME", "ScrapyBot")
        folder_id = self.get_or_create_folder(drive_service, folder_name)

        # Create a new Google Spreadsheet with the same name as the ExportPipeline output file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.spreadsheet_name = f"{spider.name}_{timestamp}"
        self.spreadsheet = self.client.create(self.spreadsheet_name)
        self.spreadsheet.share(
            spider.settings.get("SERVICE_ACCOUNT_EMAIL"),
            perm_type="user",
            role="writer",
        )
        self.worksheet = self.spreadsheet.get_worksheet(0)

        # Flag to track if we've added headers
        self.headers_added = False

    def get_or_create_folder(self, drive_service, folder_name):
        # Search for the folder in Google Drive
        response = (
            drive_service.files()
            .list(
                q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'",
                spaces="drive",
            )
            .execute()
        )

        files = response.get("files", [])
        if not files:
            # Folder doesn't exist, create it
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            file = (
                drive_service.files().create(body=file_metadata, fields="id").execute()
            )
            folder_id = file.get("id")
        else:
            # Folder exists, use the existing folder
            folder_id = files[0]["id"]

        return folder_id

    def process_item(self, item, spider):
        # Convert item to a list of values ordered by headers
        if not self.headers_added:
            headers = list(item.keys())
            self.worksheet.append_row(headers)
            self.headers_added = True

        # Append the item as a new row in the sheet
        row = [item.get(header) for header in self.worksheet.row_values(1)]
        self.worksheet.append_row(row)

        return item
