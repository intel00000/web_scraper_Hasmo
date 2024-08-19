import scrapy
from scrapy.http import HtmlResponse
import datetime
import requests


class McKinseyDigitalInsightsSpider(scrapy.Spider):
    name = "mckinsey_capabilities_digital_insights"

    custom_settings = {
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "mckinsey_capabilities_digital_insights_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def start_requests(self):
        url = "https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        main_container = response.xpath("/html/body/div[1]/main/div[2]")

        # Find all article blocks within the container
        blocks = main_container.xpath(
            './/div[contains(@class, "GeneralUp_mck-c-general-up__generic-item")]'
        )

        for block in blocks:
            title = block.xpath(".//h5/a/span/text()").get()
            article_url = block.xpath(".//h5/a/@href").get()
            image_src = block.xpath(".//picture/img/@src").get()
            image_url = response.urljoin(image_src) if image_src else None
            description = block.xpath(
                './/div[contains(@class, "mck-c-generic-item__description")]/text()'
            ).get()
            date = block.xpath(".//time/@datetime").get()

            # Skip blocks without title, description, or hyperlink
            if not title or not description or not article_url:
                continue

            # Construct full URL for the article
            article_full_url = response.urljoin(article_url)

            # Yield a request to follow the article link and parse the full article
            yield scrapy.Request(
                url=article_full_url,
                callback=self.parse_article,
                meta={
                    "title": title.strip() if title else "No title found",
                    "description": (
                        description.strip() if description else "No description found"
                    ),
                    "url": article_full_url,
                    "image_url": image_url,
                    "date": date if date else "No date found",
                },
                dont_filter=True,
            )

    def parse_article(self, response):
        # Extract all text content from <p> and <h> tags
        paragraphs = response.xpath(
            "//p//text() | //h1//text() | //h2//text() | //h3//text() | //h4//text() | //h5//text() | //h6//text()"
        ).getall()
        article_text = " ".join([p.strip() for p in paragraphs if p.strip()])

        item = {
            "title": response.meta["title"],
            "description": response.meta["description"],
            "url": response.meta["url"],
            "image_url": response.meta["image_url"],
            "date": response.meta["date"],
            "article_text": article_text,
        }

        # Yield the combined data to be processed by the pipeline
        yield item


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www.mckinsey.com/capabilities/mckinsey-digital/our-insights"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = McKinseyDigitalInsightsSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
