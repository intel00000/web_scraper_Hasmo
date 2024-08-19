import json
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# Load environment variables from the .env file
env_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path=env_path)

# Set up the Google Sheets and Drive API credentials and scope
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]
credentials_path = os.path.join(os.path.dirname(env_path), "credentials.json")

# Load the Google Sheets and Drive API credentials
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
client = gspread.authorize(creds)


# Function to create or get the Google Sheet and worksheet
def setup_google_sheet(sheet_name, worksheet_name):
    try:
        # Open the spreadsheet
        sheet = client.open(sheet_name)
    except gspread.SpreadsheetNotFound:
        # If the spreadsheet doesn't exist, create it
        sheet = client.create(sheet_name)

    try:
        # Select the worksheet
        worksheet = sheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        # If the worksheet doesn't exist, create it
        worksheet = sheet.add_worksheet(title=worksheet_name, rows="100", cols="20")

    return worksheet


# Function to update the worksheet with the scraped data
def update_worksheet(worksheet, data):
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
    for header, value in data.items():
        if header in header_indices:
            col_num = header_indices[header]
            worksheet.update_cell(
                2, col_num, ",".join(value) if isinstance(value, list) else value
            )
        else:
            # Add new headers and update data in new columns
            new_col_num = len(existing_headers) + 1
            worksheet.update_cell(1, new_col_num, header)
            worksheet.update_cell(
                2, new_col_num, ",".join(value) if isinstance(value, list) else value
            )
            # Update the existing headers and indices to include the new header
            existing_headers.append(header)
            header_indices[header] = new_col_num


def main():
    # Load the JSON file
    input_file = "sample_input.json"  # Replace with your JSON file path
    output_file = "sample_output_with_summaries.json"  # Output file path
    items = []

    with open(input_file, "r", encoding="utf-8") as f:
        try:
            content = json.load(f)  # Try to load the entire file as a list of dicts
            if isinstance(
                content, dict
            ):  # If the content is a single dictionary, make it a list
                items.append(content)
            elif isinstance(content, list):
                items.extend(content)  # If it's a list of dicts, add all items
            else:
                print(
                    f"Unexpected data format: {content}. Expected a list or dictionary."
                )
        except json.JSONDecodeError:
            # If loading the entire file fails, try line by line processing
            f.seek(0)  # Reset the file pointer to the beginning
            for line in f:
                try:
                    item = json.loads(line.strip())  # Parse each line as a JSON object
                    items.append(item)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON on line: {line}. Error: {e}")

    # Access Google Sheets
    # first try opening the spreadsheet, if it doesn't exist, create a new one
    try:
        spreadsheet = client.open("Web Scraping Data")  # Opens an existing spreadsheet
    except gspread.SpreadsheetNotFound:
        spreadsheet = client.create("Web Scraping Data")
    # adjust the access permissions as needed
    spreadsheet.share(None, perm_type="anyone", role="writer")
    # find the worksheet by title
    try:
        worksheet = spreadsheet.worksheet("Data")
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet("Data", 100, 20)

    # Process each item in the JSON file
    for item in items:
        if isinstance(item, dict):  # Ensure the item is a dictionary
            update_worksheet(worksheet, item)
        else:
            print(
                "Unexpected item format in JSON file. Each item should be a dictionary."
            )

    print(f"Data saved to Google Sheets: {spreadsheet.url}")


if __name__ == "__main__":
    main()
