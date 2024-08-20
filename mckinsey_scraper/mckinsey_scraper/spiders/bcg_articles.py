import scrapy
import datetime
import re


class BCGArticleSpider(scrapy.Spider):
    name = "bcg_articles"

    custom_settings = {
        "COOKIES_ENABLED": True,
        "LOG_ENABLED": True,
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE_APPEND": True,
        "LOG_FILE": "bcg_articles_"
        + datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        + ".log",
    }

    def __init__(self, start_page=1, end_page=50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_page = int(start_page)
        self.end_page = int(end_page)
        self.filters = {}

    def start_requests(self):
        base_url = "https://www.bcg.com/search"

        yield scrapy.Request(
            url=base_url, callback=self.parse_filters, dont_filter=True
        )

    def parse_filters(self, response):
        # Parse filter options from the sidebar
        filters = {}
        filter_sections = response.xpath(
            '//div[contains(@class, "sk-hierarchical-refinement-list")]'
        )

        for section in filter_sections:
            section_name = (
                section.xpath(
                    './/div[@class="sk-hierarchical-refinement-list__header"]/text()'
                )
                .get()
                .strip()
            )
            options = section.xpath('.//div[@class="filter-link"]')

            filters[section_name] = {
                option.xpath(
                    './/div[@class="sk-hierarchical-refinement-option__text"]/input/@data-display'
                )
                .get()
                .strip(): option.xpath(
                    './/div[@class="sk-hierarchical-refinement-option__text"]/input/@value'
                )
                .get()
                .strip()
                for option in options
            }

        self.display_filters(filters)

        # Ask user to select filters
        self.filters = self.get_user_selected_filters(filters)

        # Construct the base URL with the selected filters
        filter_query = "&".join(
            [f"{key}={value}" for key, value in self.filters.items()]
        )
        base_url = f"https://www.bcg.com/search?{filter_query}&p="

        # Start crawling from the specified start page
        for page in range(self.start_page, self.end_page + 1):
            url = base_url + str(page)
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.handle_error,
                headers={"Referer": "https://www.bcg.com/search"},
                dont_filter=True,
            )

    def display_filters(self, filters):
        print("\nAvailable Filters:")
        for section_name, options in filters.items():
            print(f"\n{section_name}:")
            for i, (option_name, option_value) in enumerate(options.items(), start=1):
                print(f"  {i}. {option_name}")

    def get_user_selected_filters(self, filters):
        selected_filters = {}
        for section_name, options in filters.items():
            while True:
                user_input = input(
                    f"\nSelect a filter from '{section_name}' (or press Enter to skip): "
                )
                if user_input.isdigit() and 1 <= int(user_input) <= len(options):
                    option_name = list(options.keys())[int(user_input) - 1]
                    selected_filters[section_name] = options[option_name]
                    break
                elif user_input == "":
                    break
                else:
                    print("Invalid selection, please try again.")
        return selected_filters

    def parse(self, response):
        # Select all 'Standard Article' result blocks
        articles = response.xpath(
            '//*[@id="global-search"]/div/div/div[2]/div[3]/div//section[@data-display-type="Standard Article"]'
        )

        for article in articles:
            title = article.xpath('.//h2[@class="title"]/a/text()').get().strip()
            date = article.xpath('.//p[@class="subtitle"]/text()').get().strip()
            description = (
                article.xpath(
                    './/div[@class="result-content"]/p[@class="intro"]/text()'
                )
                .get()
                .strip()
            )
            img_url = article.xpath(
                './/div[@class="result-picture"]/a/picture/img/@src'
            ).get()
            hyperlink = article.xpath('.//h2[@class="title"]/a/@href').get()

            # Construct the full image URL if necessary (some images might have relative URLs)
            img_url = response.urljoin(img_url)
            hyperlink = response.urljoin(hyperlink)

            yield {
                "title": title,
                "date": date,
                "description": description,
                "img_url": img_url,
                "hyperlink": hyperlink,
            }

        # Handle pagination
        current_page = int(re.search(r"p=(\d+)", response.url).group(1))
        if current_page < self.end_page:
            next_page = current_page + 1
            next_page_url = f"https://www.bcg.com/search?p={next_page}"
            yield scrapy.Request(
                url=next_page_url,
                callback=self.parse,
                errback=self.handle_error,
                headers={"Referer": "https://www.bcg.com/search"},
                dont_filter=True,
            )

    def handle_error(self, failure):
        self.logger.error(
            f"Request failed with status: {failure.value.response.status}. URL: {failure.request.url}"
        )
