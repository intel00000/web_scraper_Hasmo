import scrapy
from scrapy.http import HtmlResponse
from scrapy.exporters import JsonLinesItemExporter, CsvItemExporter
import requests
import json
import datetime


class McKinseyCaseBlogSpider(scrapy.Spider):
    name = "mckinsey_case_blog"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "mckinsey_case_blog_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def __init__(self, start_page=1, end_page=1, *args, **kwargs):
        super(McKinseyCaseBlogSpider, self).__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.end_page = int(end_page)
        # export to json file
        self.json_output_file = open(
            "mckinsey_case_blog_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".json",
            "wb",
        )
        self.json_exporter = JsonLinesItemExporter(
            self.json_output_file, encoding="utf-8", indent=4
        )
        # export to csv file
        self.csv_output_file = open(
            "mckinsey_case_blog_"
            + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".csv",
            "wb",
        )
        self.csv_exporter = CsvItemExporter(self.csv_output_file, encoding="utf-8")

        self.json_exporter.start_exporting()
        self.csv_exporter.start_exporting()

    def start_requests(self):
        # First, make a request to the main blog page to get the cookies
        initial_url = "https://www.mckinsey.com/about-us/new-at-mckinsey-blog"
        yield scrapy.Request(url=initial_url, callback=self.store_cookies)

    def store_cookies(self, response):
        # check the response status
        if response.status != 200:
            self.logger.error(
                f"Failed to get cookies from the main blog page. Status: {response.status}"
            )
            return
        # Cookies are now stored in the session, proceed with the API requests
        base_url = "https://prd-api.mckinsey.com/v1/blogs/new-at-mckinsey-blog/"
        for page_num in range(self.start_page, self.end_page + 1):
            url = f"{base_url}{page_num}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_api,
                errback=self.handle_error,
            )

    def parse_api(self, response):
        if response.status != 200:
            self.logger.info(
                f"Page {response.url} does not exist. Stopping the spider."
            )
            return

        # Load JSON data
        data = json.loads(response.text)

        for result in data["results"]:
            # Extract basic data from the API response
            title = result.get("title")
            description = result.get("description")
            body = result.get("body")
            display_date = result.get("displaydate")
            image_url = result.get("imageurl")
            blog_tags = [tag.get("title") for tag in result.get("blogentrytags", [])]
            article_url = response.urljoin(result.get("url"))

            # Follow the article URL to get the full article content
            yield scrapy.Request(
                url=article_url,
                callback=self.parse_article,
                meta={
                    "title": title,
                    "description": description,
                    "body": body,
                    "display_date": display_date,
                    "image_url": image_url,
                    "blog_tags": blog_tags,
                    "url": article_url,
                },
            )

        # If there is a next page link, continue following pagination
        next_link = data["links"].get("next")
        if next_link:
            next_page_url = response.urljoin(next_link)
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse_api,
                errback=self.handle_error,
                dont_filter=True,
            )

    def parse_article(self, response):
        # Extract all text content from <p> and <h> tags
        paragraphs = response.xpath(
            "//p//text() | //h1//text() | //h2//text() | //h3//text() | //h4//text() | //h5//text() | //h6//text()"
        ).getall()
        article_text = " ".join([p.strip() for p in paragraphs if p.strip()])

        # Gather meta data passed from the initial API response
        title = response.meta["title"]
        description = response.meta["description"]
        body = response.meta["body"]
        display_date = response.meta["display_date"]
        image_url = response.meta["image_url"]
        blog_tags = response.meta["blog_tags"]
        url = response.meta["url"]

        # Yield the combined data
        yield {
            "title": title,
            "description": description,
            "body": body,
            "display_date": display_date,
            "image_url": image_url,
            "blog_tags": blog_tags,
            "url": url,
            "article_text": article_text,
        }

    def handle_error(self, failure):
        self.logger.error(
            f"Request failed with status: {failure.value.response.status}. URL: {failure.request.url}"
        )
