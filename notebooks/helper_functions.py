import gspread
import time
import datetime
import random
from oauth2client.service_account import ServiceAccountCredentials
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Set up the Google Sheets and Drive API credentials and scope
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials_path = os.path.join(os.getcwd(), "..", "credentials.json")


class GoogleSheetsPipeline:
    def __init__(self, spreadsheet_name="Web Scraping Data", worksheet_name="Data"):
        self.spreadsheet_name = spreadsheet_name
        self.worksheet_name = worksheet_name
        self.spreadsheet = None
        self.worksheet = None
        self.credentials = None
        self.gspread_client = None
        self.maximum_backoff = 32
        self.init_rows = 100
        self.init_cols = 20

    def open_connection(self):
        # Load the Google Sheets and Drive API credentials
        self.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        self.gspread_client = gspread.authorize(self.credentials)

        # Access Google Sheets, first try opening the spreadsheet, if it doesn't exist, create a new one
        try:
            self.spreadsheet = self.retry_api_call(
                self.gspread_client.open, self.spreadsheet_name
            )
        except gspread.SpreadsheetNotFound:
            self.spreadsheet = self.retry_api_call(
                self.gspread_client.create, self.spreadsheet_name
            )

        # Set permissions
        self.retry_api_call(
            self.spreadsheet.share, None, perm_type="anyone", role="writer"
        )

        # Access or create worksheet
        try:
            self.worksheet = self.retry_api_call(
                self.spreadsheet.worksheet, self.worksheet_name
            )
            # find the next available row
            next_row = self.find_next_available_row(self.worksheet)
            if next_row > self.worksheet.row_count // 2:
                self.retry_api_call(self.worksheet.resize, self.max_rows, self.max_cols)
            # find the next available column
            next_col = self.find_next_available_column(self.worksheet)
            if next_col > self.worksheet.col_count // 2:
                self.retry_api_call(self.worksheet.resize, self.max_rows, self.max_cols)
        except gspread.WorksheetNotFound:
            self.worksheet = self.retry_api_call(
                self.spreadsheet.add_worksheet,
                title=self.worksheet_name,
                rows=self.init_rows,
                cols=self.init_cols,
            )

    def find_next_available_row(self, worksheet):
        str_list = self.retry_api_call(worksheet.col_values, 1)
        str_list = list(filter(None, str_list))
        return len(str_list) + 1

    def find_next_available_column(self, worksheet):
        str_list = self.retry_api_call(worksheet.row_values, 1)
        str_list = list(filter(None, str_list))
        return len(str_list) + 1

    def find_column_by_header(self, worksheet, header_name):
        headers = self.retry_api_call(worksheet.row_values, 1)
        try:
            return headers.index(header_name) + 1
        except ValueError:
            return None

    def find_row_by_title(self, worksheet, title, title_column):
        titles = self.retry_api_call(worksheet.col_values, title_column)
        try:
            return titles.index(title) + 1
        except ValueError:
            return None

    def update_worksheet(self, data):
        if not isinstance(data, dict):
            print(f"Invalid data format: {data}. Expected a dictionary.")
            return

        existing_headers = self.retry_api_call(self.worksheet.row_values, 1)
        header_indices = {
            header: index + 1 for index, header in enumerate(existing_headers)
        }

        headers = list(data.keys())
        new_headers = [header for header in headers if header not in header_indices]

        if new_headers:
            existing_headers.extend(new_headers)
            cell_list = self.retry_api_call(
                self.worksheet.range, 1, 1, 1, len(existing_headers)
            )
            for i, cell in enumerate(cell_list):
                cell.value = existing_headers[i]
            self.retry_api_call(self.worksheet.update_cells, cell_list)
            header_indices = {
                header: index + 1 for index, header in enumerate(existing_headers)
            }

        title_column = self.find_column_by_header(self.worksheet, "title")
        if title_column is None:
            title_column = 1
            self.retry_api_call(self.worksheet.update_cell, 1, 1, "title")
            header_indices["title"] = 1

        title = data.get("title", "")
        row_num = self.find_row_by_title(self.worksheet, title, title_column)

        if row_num is None:
            row_num = self.find_next_available_row(self.worksheet)

        # Check if we need to resize the worksheet
        if (
            row_num > self.worksheet.row_count // 2
            and len(existing_headers) > self.worksheet.col_count // 2
        ):
            self.retry_api_call(
                self.worksheet.resize,
                self.worksheet.row_count * 2,
                self.worksheet.col_count * 2,
            )
        elif row_num > self.worksheet.row_count // 2:
            self.retry_api_call(
                self.worksheet.resize,
                self.worksheet.row_count * 2,
                self.worksheet.col_count,
            )
        elif len(existing_headers) > self.worksheet.col_count // 2:
            self.retry_api_call(
                self.worksheet.resize,
                self.worksheet.row_count,
                self.worksheet.col_count * 2,
            )

        row_data = [""] * len(existing_headers)

        for header, value in data.items():
            col_num = header_indices.get(header)
            if col_num is not None:
                row_data[col_num - 1] = (
                    ",".join(value) if isinstance(value, list) else value
                )

        cell_list = self.retry_api_call(
            self.worksheet.range, row_num, 1, row_num, len(existing_headers)
        )

        for i, cell in enumerate(cell_list):
            # cap the char of cell value to 50000
            if row_data[i] is not None:
                cell.value = row_data[i][:50000]
            else:
                cell.value = ""

        self.retry_api_call(self.worksheet.update_cells, cell_list)

    def retry_api_call(self, func, *args, max_retries=15, **kwargs):
        """Handles retrying API calls with exponential backoff."""
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except gspread.exceptions.APIError as e:
                if e.response.status_code == 429:
                    retries += 1
                    # cap the sleep time at the maximum backoff
                    sleep_time = min(
                        (2**retries) + random.randint(0, 1000) / 1000,
                        self.maximum_backoff,
                    )
                    print(
                        f"Rate limit exceeded, retrying in {sleep_time:.2f} seconds..."
                    )
                    time.sleep(sleep_time)
                else:
                    raise e
        else:
            print("Max retries exceeded for API call.")
            return None

    def process_data(self, data_list):
        for item in data_list:
            self.update_worksheet(item)

    def close_connection(self):
        print(
            f"GoogleSheetsPipeline finished processing and saved data to {self.spreadsheet.url}"
        )


def file_exporter(name, data):
    # Define the timestamp and file paths
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    json_output_file_path = os.path.join(
        os.getcwd(), "..", "data", name + f"_{timestamp}.json"
    )
    csv_output_file_path = os.path.join(
        os.getcwd(), "..", "data", name + f"_{timestamp}.csv"
    )

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Step 3: Export to JSON and CSV
    df.to_json(json_output_file_path, orient="records", indent=4)
    df.to_csv(csv_output_file_path, index=False)

    print(
        f"Data has been exported to {json_output_file_path} and {csv_output_file_path}"
    )


def parse_article(article_url):
    article_data = {"article_download_link": "", "article_text": "", "article_imgs": []}

    # Check if the link is to a PDF
    if article_url.endswith(".pdf"):
        article_data["article_download_link"] = article_url
        return article_data

    # Fetch the article
    response = requests.get(article_url)
    if response.status_code != 200:
        print(f"Failed to fetch the article: {article_url}")
        return article_data

    soup = BeautifulSoup(response.content, "html.parser")

    # locate the main text body
    content_inner_wrapper = soup.find("div", class_="content-inner-inner-wrapper")
    if not content_inner_wrapper:
        print(f"No content found in article: {article_url}")
        return article_data

    # Extract text from all sections
    article_text = []
    sections = content_inner_wrapper.find_all("div", class_="container-text")
    for section in sections:
        paragraphs = section.find_all("p")
        for paragraph in paragraphs:
            article_text.append(paragraph.get_text(strip=True))

    # Combine all text into a single string
    article_data["article_text"] = " ".join(article_text)

    # Extract all inline images
    figures = content_inner_wrapper.find_all("figure", {"data-zoom": True})
    for figure in figures:
        img_url = figure.get("data-zoom")
        if img_url:
            article_data["article_imgs"].append(img_url)

    return article_data


from openai import OpenAI
from dotenv import load_dotenv

# Load the environment variables from the .env file
env_path = os.path.join(os.getcwd(), "..", ".env")

# Define the word count limit as a macro
WORD_COUNT_LIMIT = 50  # You can adjust this as needed


class OpenAIPipeline:
    def __init__(self):
        self.client = None
        load_dotenv(dotenv_path=env_path)
        # Set the OpenAI API key
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    def process_item(self, item):
        article_text = item.get("article_text", "")
        if article_text:
            summary = self.summarize_content(article_text)
            item["summary"] = summary
            print(f"Generated summary: {summary}")
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
