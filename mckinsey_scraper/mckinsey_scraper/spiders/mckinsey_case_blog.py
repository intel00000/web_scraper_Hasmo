import scrapy
import json
import datetime
import re
from scrapy.downloadermiddlewares.retry import get_retry_request


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
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.end_page = int(end_page)

    def start_requests(self):
        # First, make a request to the main blog page to get the cookies
        self.base_url = "https://www.mckinsey.com/about-us/new-at-mckinsey-blog"
        yield scrapy.Request(
            url=self.base_url, callback=self.store_cookies, dont_filter=True
        )

    def store_cookies(self, response):
        # store the response object to use it later
        self.base_url_response = response

        # check the response status
        if response.status != 200:
            self.logger.error(
                f"Failed to get cookies from the main blog page. Status: {response.status}"
            )
            return

        # Cookies are now stored in the session, proceed with the API requests
        self.base_url = "https://prd-api.mckinsey.com/v1/blogs/new-at-mckinsey-blog/"
        url = f"{self.base_url}{self.start_page}"
        yield scrapy.Request(
            url=url,
            callback=self.parse_api,
            errback=self.handle_error,
            headers={"Referer": self.base_url_response.url},
            dont_filter=True,
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
            # Extract data from the API response
            item = {
                "title": result.get("title"),
                "description": result.get("description"),
                "body": result.get("body"),
                "display_date": result.get("displaydate"),
                "image_url": result.get("imageurl"),
                "blog_tags": [
                    tag.get("title") for tag in result.get("blogentrytags", [])
                ],
                "url": self.base_url_response.urljoin(result.get("url")),
            }

            # Follow the article URL to get the full article content, set the referer to the base URL
            yield scrapy.Request(
                url=item["url"],
                callback=self.parse_article,
                meta=item,
                headers={"Referer": self.base_url_response.url},
                dont_filter=True,
            )

        # If there is a next page link, continue following pagination, if the page is within the specified range
        next_link = data["links"].get("next")
        if next_link:
            # find the page number from the next link, format https://prd-api.mckinsey.com/v1/blogs/new-at-mckinsey-blog/page_number
            next_page_number = int(re.search(r"\d+$", next_link).group())
            if next_page_number > self.end_page:
                self.logger.info(
                    f"Reached the end page {self.end_page}. Stopping the spider."
                )
                return
            else:
                next_page_url = response.urljoin(next_link)
                yield scrapy.Request(
                    url=next_page_url,
                    callback=self.parse_api,
                    errback=self.handle_error,
                    headers={"Referer": self.base_url_response.url},
                    dont_filter=True,
                )

    def parse_article(self, response):
        # Extract all text content from <p> and <h> tags
        article_text = " ".join(
            response.xpath("//p | //h1 | //h2 | //h3 | //h4 | //h5 | //h6").extract()
        )

        # generate the dictionary to store the data
        item = {
            "title": response.meta["title"],
            "description": response.meta["description"],
            "display_date": response.meta["display_date"],
            "image_url": response.meta["image_url"],
            "blog_tags": response.meta["blog_tags"],
            "url": response.meta["url"],
            "article_text": article_text,
        }

        # Yield the combined data to pipeline
        yield item

    def handle_error(self, failure):
        if failure.value.response.status_code == 403:
            self.logger.warning(f"Retrying 403 error for URL: {failure.request.url}")
            retry_req = get_retry_request(
                failure.request, reason="403 Forbidden", spider=self
            )
            if retry_req:
                yield retry_req
        else:
            self.logger.error(
                f"Request failed with status: {failure.value.response.status}. URL: {failure.request.url}"
            )
