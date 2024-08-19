import scrapy
import datetime
import requests
from scrapy.http import HtmlResponse


class McKinseyCapabilitiesSpider(scrapy.Spider):
    name = "mckinsey_capabilities"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "mckinsey_capabilities_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def start_requests(self):
        url = "https://www.mckinsey.com/capabilities"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Select the container holding the capability sections
        container = response.xpath('//*[@id="skipToMain"]/div[2]/div/div/div[1]/div')

        # Find all capability blocks within the container
        blocks = container.xpath(
            './/div[contains(@class, "mdc-c-content-block")]'
        )

        for block in blocks:
            # Extract title, URL, and description
            title = block.xpath(".//h5/a/span/text()").get()
            url = block.xpath(".//h5/a/@href").get()
            full_url = response.urljoin(url)
            description = block.xpath(
                './/div[contains(@class, "mck-c-generic-item__description")]/text()'
            ).get()

            yield {
                "title": title,
                "url": full_url,
                "description": (
                    description.strip() if description else "No description found"
                ),
            }


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www.mckinsey.com/capabilities"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = McKinseyCapabilitiesSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
