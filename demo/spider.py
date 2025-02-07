from typing import Any

import scrapy
from scrapy import signals
from scrapy.crawler import Crawler
from scrapy.exceptions import DontCloseSpider


def spider_idle():
    raise DontCloseSpider


class QuotesSpider(scrapy.Spider):
    name = "quotes"
    start_urls = [
        "https://quotes.toscrape.com/page/1/",
        "https://quotes.toscrape.com/page/2/",
        "https://quotes.toscrape.com/page/3/",
        "https://quotes.toscrape.com/page/4/",
        "https://quotes.toscrape.com/page/5/",
        "https://quotes.toscrape.com/page/6/",
    ]

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": quote.css("span.text::text").get(),
                "author": quote.css("small.author::text").get(),
                "tags": quote.css("div.tags a.tag::text").getall(),
            }

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args: Any, **kwargs: Any):
        crawler.signals.connect(spider_idle, signal=signals.spider_idle)
        return super().from_crawler(crawler, *args, **kwargs)
