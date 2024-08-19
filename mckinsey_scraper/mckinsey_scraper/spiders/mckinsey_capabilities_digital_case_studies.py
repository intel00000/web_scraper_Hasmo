import scrapy
from scrapy.http import HtmlResponse
import datetime
import requests


class McKinseyDigitalCaseStudiesSpider(scrapy.Spider):
    name = "mckinsey_capabilities_digital_case_studies"

    custom_settings = {
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "mckinsey_capabilities_digital_case_studies_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def start_requests(self):
        url = "https://www.mckinsey.com/capabilities/mckinsey-digital/case-studies"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        main_container = response.xpath(
            "/html/body/div[1]/main/div[2]/div/div/div[2]/div"
        )
        containers = main_container.xpath(
            '//div[contains(@class, "mdc-u-grid mdc-u-grid-gutter-lg")]'
        )

        for container in containers:
            title = container.xpath(
                './/h5[@data-component="mdc-c-heading"]/a/span/text()'
            ).get()
            article_url = container.xpath(
                './/h5[@data-component="mdc-c-heading"]/a/@href'
            ).get()
            image_src = container.xpath(".//picture/img/@src").get()
            image_url = response.urljoin(image_src) if image_src else None
            description = container.xpath(
                './/div[@data-component="mdc-c-description"]/div/text()'
            ).get()
            date = container.xpath(".//time/@datetime").get()

            # Skip the row if there is no title and link
            if not title and not article_url:
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
    url = "https://www.mckinsey.com/capabilities/mckinsey-digital/case-studies"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = McKinseyDigitalCaseStudiesSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
