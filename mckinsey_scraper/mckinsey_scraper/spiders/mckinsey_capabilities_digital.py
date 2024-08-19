import scrapy
import datetime
import requests
from scrapy.http import HtmlResponse


class McKinseyDigitalSpider(scrapy.Spider):
    name = "mckinsey_capabilities_digital"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "mckinsey_capabilities_digital_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def start_requests(self):
        url = (
            "https://www.mckinsey.com/capabilities/mckinsey-digital/how-we-help-clients"
        )
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Locate the specific mck-o-container that contains the "What we offer" section
        container = response.xpath('//*[@id="skipToMain"]/div[2]/div/div/div[5]/div')

        # Extract the heading and description
        heading = container.xpath(".//h2//text()").get()
        sub_heading = container.xpath(".//h3//text()").get()
        description = container.xpath(
            './/div[contains(@class, "mdc-c-description")]/div/p//text()'
        ).get()

        # Extract the individual offer blocks within this container
        blocks = container.xpath(
            './/div[contains(@class, "GeneralUp_mck-c-general-up__generic-item")]'
        )

        for block in blocks:
            # Extract title, URL, and description for each offer
            title = block.xpath(".//h5/a/span/text()").get()
            url = block.xpath(".//h5/a/@href").get()
            full_url = response.urljoin(url)
            block_description = block.xpath(
                './/div[contains(@class, "mck-c-generic-item__description")]//text()'
            ).getall()
            block_description = " ".join(
                [text.strip() for text in block_description if text.strip()]
            )

            yield {
                "section_heading": heading,
                "sub_heading": sub_heading,
                "section_description": description,
                "title": title,
                "url": full_url,
                "description": block_description,
            }


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www.mckinsey.com/capabilities/mckinsey-digital/how-we-help-clients"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = McKinseyDigitalSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
