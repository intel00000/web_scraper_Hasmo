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


import openai
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv(dotenv_path="../../.env")

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

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
            chat_completion = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": prompt}],
                max_tokens=WORD_COUNT_LIMIT,
                temperature=0.7,
            )

            # Extract the summary from the response
            summary = chat_completion.choices[0].message["content"].strip()
            return summary

        except Exception as e:
            print(f"Failed to generate summary: {e}")
            return "Failed to generate summary."
