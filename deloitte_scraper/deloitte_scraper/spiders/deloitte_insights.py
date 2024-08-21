import scrapy
import datetime
import time
from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

    def __init__(self, *args, **kwargs):
        super(DeloitteInsightsSpider, self).__init__(*args, **kwargs)
        # Initialize Selenium WebDriver
        service = Service()
        self.driver = webdriver.Chrome(service=service)

    def start_requests(self):
        url = "https://www2.deloitte.com/us/en/insights/industry.html"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Use Selenium to load the page and wait for the content to load
        self.driver.get(response.url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "page"))
        )

        # Get the page source after content is loaded
        page_source = self.driver.page_source

        # Create a Scrapy response from the Selenium page source
        selenium_response = HtmlResponse(
            url=response.url, body=page_source, encoding="utf-8"
        )

        # Continue with the regular parsing as before
        filter_section = selenium_response.xpath('//section[@class="filter-section"]')

        if filter_section:
            pages = filter_section.xpath('.//div[@class="page"]')

            for page in pages:
                article_blocks = page.xpath(
                    './/div[contains(@class, "aem-Grid--default--12 custom-row")]/div[contains(@class, "col-md-4")]'
                )

                for block in article_blocks:
                    title = block.xpath('.//h3[@class="element-heading"]/text()').get()
                    description = block.xpath(
                        './/p[@class="element-content"]/text()'
                    ).get()
                    tag = block.xpath('.//h5[@class="element-read"]/text()').get()
                    href = block.xpath('.//a[@class="cmp-promo-tracking"]/@href').get()
                    full_url = response.urljoin(href)

                    yield scrapy.Request(
                        url=full_url,
                        callback=self.parse_article,
                        meta={
                            "title": title,
                            "description": description,
                            "tag": tag,
                            "link": full_url,
                        },
                    )

    def parse_article(self, response):
        article_blocks = response.xpath('//div[@class="cmp-text "]/p')[
            1:
        ]  # Skipping the first block
        article_text = " ".join(article_blocks.xpath("text()").getall())

        yield {
            "title": response.meta["title"],
            "description": response.meta["description"],
            "tag": response.meta["tag"],
            "link": response.meta["link"],
            "article_text": article_text,
        }

    def closed(self, reason):
        # Close the Selenium WebDriver when the spider is closed
        self.driver.quit()


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www2.deloitte.com/us/en/insights/industry.html"
    # Manually running Selenium for testing without Scrapy
    service = Service(
        "path_to_chromedriver"
    )  # Update with the path to your ChromeDriver
    driver = webdriver.Chrome(service=service)
    driver.get(url)
    time.sleep(5)  # Wait for content to load
    print(driver.page_source)
    driver.quit()
