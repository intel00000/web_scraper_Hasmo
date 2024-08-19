# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter


class MckinseyScraperPipeline:
    def process_item(self, item, spider):
        return item

from scrapy.exporters import JsonLinesItemExporter, CsvItemExporter
import datetime

class McKinseyExportPipeline:

    def __init__(self):
        # Initialize JSON exporter
        self.json_output_file = open(
            "mckinsey_case_blog_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".json",
            "wb",
        )
        self.json_exporter = JsonLinesItemExporter(
            self.json_output_file, encoding="utf-8", indent=4
        )

        # Initialize CSV exporter
        self.csv_output_file = open(
            "mckinsey_case_blog_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".csv",
            "wb",
        )
        self.csv_exporter = CsvItemExporter(self.csv_output_file, encoding="utf-8")

        # Start exporting
        self.json_exporter.start_exporting()
        self.csv_exporter.start_exporting()

    def process_item(self, item, spider):
        # Export item to JSON
        self.json_exporter.export_item(item)

        # Export item to CSV
        self.csv_exporter.export_item(item)

        return item

    def close_spider(self, spider):
        # Finish exporting and close the files
        self.json_exporter.finish_exporting()
        self.json_output_file.close()
        self.csv_exporter.finish_exporting()
        self.csv_output_file.close()