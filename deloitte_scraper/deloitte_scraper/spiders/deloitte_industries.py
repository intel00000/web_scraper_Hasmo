import scrapy
import datetime
import requests
from scrapy.http import HtmlResponse


class DeloitteIndustriesSpider(scrapy.Spider):
    name = "deloitte_industries"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": name
        + "_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
        "ITEM_PIPELINES": {
            "deloitte_scraper.pipelines.GoogleSheetsPipeline": 200,
            "deloitte_scraper.pipelines.ExportPipeline": 300,
        },
    }

    def start_requests(self):
        url = "https://www2.deloitte.com/us/en.html"
        yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    def parse(self, response):
        # Look for the "Services" link by its unique attribute `data-sub="Services"`
        services_link = response.xpath('//a[@data-sub="Industries"]')

        if services_link:
            # The "Services" link has a sibling div that contains the actual menu
            services_menu = services_link.xpath(
                './following-sibling::div[@class="cmp-pr-nav__menu"]'
            )
            if services_menu:
                # Extract the sections that represent each service
                service_sections = services_menu.xpath(
                    './/ul[@class="cmp-pr-nav__menu__links-section aem-Grid aem-Grid--12"]/li'
                )

                for section in service_sections:
                    service_name = section.xpath(".//h4/a/text()").get()
                    service_href = response.urljoin(
                        section.xpath(".//h4/a/@href").get()
                    )
                    subservices = []

                    # Extract subservices and their full URLs
                    subservice_items = section.xpath(".//ul/li")
                    if subservice_items:
                        for subservice in subservice_items:
                            subservice_name = subservice.xpath(".//a/text()").get()
                            subservice_href = response.urljoin(
                                subservice.xpath(".//a/@href").get()
                            )
                            subservices.append(
                                f"{subservice_name.strip()}: {subservice_href}"
                            )

                    # Join the subservices into a single string to fit the existing pipeline
                    subservices_str = ", ".join(subservices)

                    # Yield the service and subservices in the required format
                    yield {
                        "title": service_name,
                        "service": service_name,
                        "service_href": service_href,
                        "subservices": subservices_str,
                    }


# For testing in a local environment
if __name__ == "__main__":
    url = "https://www2.deloitte.com/us/en.html"
    r = requests.get(url)
    response = HtmlResponse(url=url, body=r.text, encoding="utf-8")

    # Instantiate the spider
    spider = DeloitteIndustriesSpider()

    # Manually call the parse method to test
    for item in spider.parse(response):
        print(item)
