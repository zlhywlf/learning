from __future__ import annotations
from scrapy.core.engine import ExecutionEngine
from scrapy.core.scheduler import Scheduler
from scrapy.crawler import Crawler, CrawlerProcess
import logging
from typing import TYPE_CHECKING, Any

from itemadapter import is_item
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from scrapy import signals
from scrapy.exceptions import CloseSpider, DontCloseSpider, IgnoreRequest
from scrapy.http import Request, Response
from scrapy.utils.log import failure_to_exc_info
from demo.util import sleep

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from scrapy.spiders import Spider

logger = logging.getLogger(__name__)


class ExecutionEngineLab(ExecutionEngine):
    def _next_request(self) -> None:
        Deferred.fromCoroutine(self.task())

    async def task(self) -> None:
        if self.slot is None:
            return
        assert self.spider is not None
        if self.paused:
            return
        while (
                not self._needs_backout()
                and await self._next_request_from_scheduler() is not None
        ):
            pass

        if self.slot.start_requests is not None and not self._needs_backout():
            try:
                request_or_item = next(self.slot.start_requests)
            except StopIteration:
                self.slot.start_requests = None
            except Exception:
                self.slot.start_requests = None
                logger.error(
                    "Error while obtaining start requests",
                    exc_info=True,
                    extra={"spider": self.spider},
                )
            else:
                if isinstance(request_or_item, Request):
                    self.crawl(request_or_item)
                elif is_item(request_or_item):
                    self.scraper.start_itemproc(request_or_item, response=None)
                else:
                    logger.error(
                        f"Got {request_or_item!r} among start requests. Only "
                        f"requests and items are supported. It will be "
                        f"ignored."
                    )

        if await self.spider_is_idle() and self.slot.close_if_idle:
            await self._spider_idle()

    def crawl(self, request: Request) -> None:
        """Inject the request into the spider <-> downloader pipeline"""
        if self.spider is None:
            raise RuntimeError(f"No open spider to crawl: {request}")
        d = Deferred.fromCoroutine(self._schedule_request(request, self.spider))
        d.addBoth(lambda _: self.slot.nextcall.schedule())

    async def _schedule_request(self, request: Request, spider: Spider) -> None:
        request_scheduled_result = self.signals.send_catch_log(
            signals.request_scheduled,
            request=request,
            spider=spider,
            dont_log=IgnoreRequest,
        )
        for handler, result in request_scheduled_result:
            if isinstance(result, Failure) and isinstance(result.value, IgnoreRequest):
                return
        if not (await self.slot.scheduler.enqueue_request(request)):  # type: ignore[union-attr]
            self.signals.send_catch_log(
                signals.request_dropped, request=request, spider=spider
            )

    async def _spider_idle(self) -> None:
        assert self.spider is not None  # typing
        expected_ex = (DontCloseSpider, CloseSpider)
        res = self.signals.send_catch_log(
            signals.spider_idle, spider=self.spider, dont_log=expected_ex
        )
        detected_ex = {
            ex: x.value
            for _, x in res
            for ex in expected_ex
            if isinstance(x, Failure) and isinstance(x.value, ex)
        }
        if DontCloseSpider in detected_ex:
            return
        if await self.spider_is_idle():
            ex = detected_ex.get(CloseSpider, CloseSpider(reason="finished"))
            assert isinstance(ex, CloseSpider)  # typing
            self.close_spider(self.spider, reason=ex.reason)

    async def spider_is_idle(self) -> bool:
        if self.slot is None:
            raise RuntimeError("Engine slot not assigned")
        if not self.scraper.slot.is_idle():  # type: ignore[union-attr]
            return False
        if self.downloader.active:  # downloader has pending requests
            return False
        if self.slot.start_requests is not None:  # not all start requests are handled
            return False
        if await self.slot.scheduler.has_pending_requests():
            return False
        return True

    async def _next_request_from_scheduler(self) -> Deferred[None] | None:
        assert self.slot is not None
        assert self.spider is not None

        request = await self.slot.scheduler.next_request()
        if request is None:
            return None

        d: Deferred[Response | Request] = self._download(request)
        d.addBoth(self._handle_downloader_output, request)
        d.addErrback(lambda f: logger.info("Error while handling downloader output", exc_info=failure_to_exc_info(f),
                                           extra={"spider": self.spider}))

        def _remove_request(_: Any) -> None:
            assert self.slot
            self.slot.remove_request(request)

        d2: Deferred[None] = d.addBoth(_remove_request)
        d2.addErrback(lambda f: logger.info("Error while removing request from slot", exc_info=failure_to_exc_info(f),
                                            extra={"spider": self.spider}))
        slot = self.slot
        d2.addBoth(lambda _: slot.nextcall.schedule())
        d2.addErrback(lambda f: logger.info("Error while scheduling new request", exc_info=failure_to_exc_info(f),
                                            extra={"spider": self.spider}))
        return d2


class CrawlerLab(Crawler):
    def _create_engine(self) -> ExecutionEngine:
        return ExecutionEngineLab(self, lambda _: self.stop())


class CrawlerProcessLab(CrawlerProcess):
    def _create_crawler(self, spidercls: str | type[Spider]) -> Crawler:
        if isinstance(spidercls, str):
            spidercls = self.spider_loader.load(spidercls)
        return CrawlerLab(spidercls, self.settings, True)


class SchedulerLab(Scheduler):
    async def has_pending_requests(self) -> bool:
        return super().has_pending_requests()

    async def enqueue_request(self, request: Request) -> bool:
        await sleep(request.url,1)
        return super().enqueue_request(request)

    async def next_request(self) -> Request | None:
        return super().next_request()
