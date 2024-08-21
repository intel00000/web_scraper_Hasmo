import scrapy
import datetime
import requests
from scrapy.http import HtmlResponse


class DeloitteInsightsSpider(scrapy.Spider):
    name = "deloitte_insights"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "deloitte_insights_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
        "ITEM_PIPELINES": {
            "deloitte_scraper.pipelines.ExportPipeline": 300,
        },
    }

    def start_requests(self):
        url = "https://www2.deloitte.com/us/en/insights/industry.html"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Locate the filter section
        filter_section = response.xpath('//section[@class="filter-section"]')

        if filter_section:
            # Look for the div containing the page content
            pages = filter_section.xpath('.//div[@class="page"]')

            for page in pages:
                # Find all article blocks within the page
                article_blocks = page.xpath(
                    './/div[contains(@class, "aem-Grid--default--12 custom-row")]/div[contains(@class, "col-md-4")]'
                )

                for block in article_blocks:
                    # Extract the title
                    title = block.xpath('.//h3[@class="element-heading"]/text()').get()

                    # Extract the description
                    description = block.xpath(
                        './/p[@class="element-content"]/text()'
                    ).get()

                    # Extract the tag
                    tag = block.xpath('.//h5[@class="element-read"]/text()').get()

                    # Extract the link and construct the full URL
                    href = block.xpath('.//a[@class="cmp-promo-tracking"]/@href').get()
                    full_url = response.urljoin(href)

                    yield {
                        "title": title,
                        "description": description,
                        "tag": tag,
                        "link": full_url,
                    }


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www2.deloitte.com/us/en/insights/industry.html"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = DeloitteInsightsSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
