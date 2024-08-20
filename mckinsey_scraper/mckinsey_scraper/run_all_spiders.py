import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from twisted.internet import asyncioreactor

asyncioreactor.install()

from twisted.internet import reactor, defer
from scrapy.crawler import CrawlerRunner
from scrapy.utils.project import get_project_settings
from scrapy.utils.log import configure_logging
from scrapy.spiderloader import SpiderLoader


def run_all_spiders_sequentially():
    settings = get_project_settings()
    configure_logging(settings)
    runner = CrawlerRunner(settings)

    # Dynamically discover all spiders in the project
    spider_loader = SpiderLoader.from_settings(settings)
    spider_names = spider_loader.list()

    @defer.inlineCallbacks
    def crawl():
        for spider_name in spider_names:
            print(f"Running spider: {spider_name}")
            yield runner.crawl(spider_name)
        reactor.stop()

    crawl()
    reactor.run()  # the script will block here until the last crawl call is finished


if __name__ == "__main__":
    run_all_spiders_sequentially()
