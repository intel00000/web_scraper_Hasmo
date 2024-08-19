# Scrapy settings for mckinsey_scraper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "mckinsey_scraper"

SPIDER_MODULES = ["mckinsey_scraper.spiders"]
NEWSPIDER_MODULE = "mckinsey_scraper.spiders"


# Crawl responsibly by identifying yourself (and your website) on the user-agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 9_9_1; en-US) Gecko/20100101 Firefox/52.9",
    "Mozilla/5.0 (Windows NT 6.1;) Gecko/20100101 Firefox/51.7",
    "Mozilla/5.0 (Linux i583 x86_64) Gecko/20100101 Firefox/47.6",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) Gecko/20130401 Firefox/70.5",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 8_7_1) Gecko/20130401 Firefox/67.4",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 7_2_7; en-US) Gecko/20100101 Firefox/65.4",
    "Mozilla/5.0 (U; Linux x86_64) Gecko/20100101 Firefox/54.7",
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 8_6_7; en-US) Gecko/20100101 Firefox/64.2",
    "Mozilla/5.0 (Linux i683 x86_64; en-US) Gecko/20100101 Firefox/62.8",
    "Mozilla/5.0 (Linux; Linux x86_64; en-US) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/53.0.3548.145 Safari/603",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; WOW64) AppleWebKit/602.19 (KHTML, like Gecko) Chrome/51.0.3302.125 Safari/535",
    "Mozilla/5.0 (Linux; Linux x86_64) AppleWebKit/600.29 (KHTML, like Gecko) Chrome/53.0.3889.268 Safari/533",
    "Mozilla/5.0 (Linux; Linux x86_64) AppleWebKit/533.48 (KHTML, like Gecko) Chrome/54.0.1347.218 Safari/536",
    "Mozilla/5.0 (Linux; Linux x86_64; en-US) AppleWebKit/602.21 (KHTML, like Gecko) Chrome/51.0.1089.205 Safari/600",
    "Mozilla/5.0 (Windows; U; Windows NT 10.0; Win64; x64; en-US) AppleWebKit/600.38 (KHTML, like Gecko) Chrome/53.0.1859.361 Safari/534",
    "Mozilla/5.0 (Windows; U; Windows NT 6.2; Win64; x64; en-US) AppleWebKit/535.2 (KHTML, like Gecko) Chrome/50.0.1583.338 Safari/536",
    "Mozilla/5.0 (Linux; Linux x86_64) AppleWebKit/602.38 (KHTML, like Gecko) Chrome/51.0.3859.347 Safari/602",
    "Mozilla/5.0 (Windows NT 10.4; WOW64; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/53.0.2542.273 Safari/600",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_0_8) AppleWebKit/535.21 (KHTML, like Gecko) Chrome/50.0.2746.191 Safari/600",
]

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en",
}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    "mckinsey_scraper.middlewares.MckinseyScraperSpiderMiddleware": 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    "mckinsey_scraper.middlewares.MckinseyScraperDownloaderMiddleware": 543,
# }
DOWNLOADER_MIDDLEWARES = {
    "myproject.middlewares.RandomUserAgentMiddleware": 400,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    "mckinsey_scraper.pipelines.MckinseyScraperPipeline": 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = "httpcache"
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
