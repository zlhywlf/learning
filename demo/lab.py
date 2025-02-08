from __future__ import annotations
from scrapy.core.engine import ExecutionEngine
from scrapy.core.scheduler import Scheduler
from scrapy.crawler import Crawler, CrawlerProcess
import logging
from typing import TYPE_CHECKING
from typing_extensions import override

from itemadapter import is_item
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure

from scrapy import signals
from scrapy.exceptions import IgnoreRequest
from scrapy.http import Request, Response
from scrapy.utils.log import failure_to_exc_info
from demo.util import sleep

if TYPE_CHECKING:
    from scrapy.crawler import Crawler
    from scrapy.spiders import Spider

logger = logging.getLogger(__name__)


class ExecutionEngineCus(ExecutionEngine):
    """A custom execution engine class that extends Scrapy's ExecutionEngine."""

    @override
    def _next_request(self) -> None:
        Deferred.fromCoroutine(self.task())

    async def task(self) -> None:
        """Asynchronously processes the spider's start requests and handles scheduling of subsequent requests.

        Raises:
            RuntimeError: self.spider is None
        """
        if self.slot is None or self.paused:
            return
        if self.spider is None:
            msg = "spider is None"
            raise RuntimeError(msg)
        while not self._needs_backout() and await self._next_request_from_scheduler() is not None:
            pass
        if self.slot.start_requests is not None and not self._needs_backout():
            try:
                request_or_item = next(self.slot.start_requests)
            except StopIteration:
                self.slot.start_requests = None
            except Exception:
                self.slot.start_requests = None
                logger.exception("Error while obtaining start requests", extra={"spider": self.spider})
            else:
                if isinstance(request_or_item, Request):
                    self.crawl(request_or_item)
                elif is_item(request_or_item):
                    self.scraper.start_itemproc(request_or_item, response=None)
                else:
                    msg = (
                        f"Got {request_or_item!r} among start requests. Only "
                        f"requests and items are supported. It will be "
                        f"ignored."
                    )
                    logger.error(msg)

    @override
    def _schedule_request(self, request: Request, spider: Spider) -> None:
        request_scheduled_result = self.signals.send_catch_log(
            signals.request_scheduled,
            request=request,
            spider=spider,
            dont_log=IgnoreRequest,
        )
        for _, result in request_scheduled_result:
            if isinstance(result, Failure) and isinstance(result.value, IgnoreRequest):
                return
        if self.slot is None:
            msg = "slot is None"
            raise RuntimeError(msg)
        d: Deferred[bool] = Deferred.fromCoroutine(self.slot.scheduler.enqueue_request(request))  # type:ignore[arg-type]
        d.addBoth(
            lambda _: None
            if _
            else self.signals.send_catch_log(signals.request_dropped, request=request, spider=spider)
        )

    @override
    async def _next_request_from_scheduler(self) -> Deferred[Response | Request] | None:  # type:ignore[override]
        def _remove_request(_: Request | Response | Failure) -> None:
            if self.slot is None:
                msg = "slot is None"
                raise RuntimeError(msg)
            self.slot.remove_request(request)

        def _log_error(f: Failure, msg: str) -> None:
            logger.info(msg, exc_info=failure_to_exc_info(f), extra={"spider": self.spider})

        if self.slot is None:
            msg = "slot is None"
            raise RuntimeError(msg)
        if self.spider is None:
            msg = "spider is None"
            raise RuntimeError(msg)
        request = await self.slot.scheduler.next_request()  # type:ignore[misc]
        if request is None:
            return None
        d = self._download(request)
        d.addBoth(self._handle_downloader_output, request)
        d.addErrback(lambda f: _log_error(f, "Error while handling downloader output"))
        d.addBoth(_remove_request)
        d.addErrback(lambda f: _log_error(f, "Error while removing request from slot"))
        d.addBoth(lambda _: self.slot.nextcall.schedule())  # type:ignore[call-overload]
        d.addErrback(lambda f: _log_error(f, "Error while scheduling new request"))
        return d


class CrawlerCus(Crawler):
    """A custom crawler class that extends Scrapy's Crawler."""

    @override
    def _create_engine(self) -> ExecutionEngine:
        return ExecutionEngineCus(self, lambda _: self.stop())


class CrawlerProcessCus(CrawlerProcess):
    """A custom crawler process class that extends Scrapy's CrawlerProcess."""

    @override
    def _create_crawler(self, spidercls: str | type[Spider]) -> Crawler:
        if isinstance(spidercls, str):
            spidercls = self.spider_loader.load(spidercls)
        return CrawlerCus(spidercls, self.settings, init_reactor=True)


class SchedulerLab(Scheduler):
    async def has_pending_requests(self) -> bool:
        return super().has_pending_requests()

    async def enqueue_request(self, request: Request) -> bool:
        await sleep(request.url, 1)
        return super().enqueue_request(request)

    async def next_request(self) -> Request | None:
        return super().next_request()
