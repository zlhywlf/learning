from __future__ import annotations

from twisted.internet.defer import Deferred

from scrapy import Spider
from scrapy.core.engine import ExecutionEngine
from scrapy.crawler import Crawler, CrawlerProcess


async def task() -> None:
    print("hello world")


class ExecutionEngineLab(ExecutionEngine):
    def _next_request(self) -> None:
        Deferred.fromCoroutine(task())


class CrawlerLab(Crawler):
    def _create_engine(self) -> ExecutionEngine:
        return ExecutionEngineLab(self, lambda _: self.stop())


class CrawlerProcessLab(CrawlerProcess):
    def _create_crawler(self, spidercls: str | type[Spider]) -> Crawler:
        if isinstance(spidercls, str):
            spidercls = self.spider_loader.load(spidercls)
        return CrawlerLab(spidercls, self.settings, True)
