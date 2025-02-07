from __future__ import annotations
from typing import Any, Generator

from twisted.internet.defer import Deferred, inlineCallbacks, DeferredList
from zope.interface.verify import verifyClass

from scrapy import Spider
from scrapy.crawler import Crawler
from scrapy.interfaces import ISpiderLoader
from scrapy.settings import Settings
from scrapy.utils.misc import load_object

import argparse

from scrapy.exceptions import UsageError
from scrapy.commands import BaseRunSpiderCommand


class Command(BaseRunSpiderCommand):
    requires_project = True

    def __init__(self):
        super().__init__()
        self._crawlers: set[Any] = set()
        self._active: set[Deferred[None]] = set()
        self.bootstrap_failed = False
        self._initialized_reactor: bool = False

    def syntax(self) -> str:
        return "[options] <spider>"

    def short_desc(self) -> str:
        return "Run a spider by demo"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        if len(args) < 1:
            raise UsageError()
        if len(args) > 1:
            raise UsageError("running 'scrapy demo' with more than one spider is not supported")
        assert isinstance(self.settings, Settings)
        cls_path = self.settings.get("SPIDER_LOADER_CLASS")
        loader_cls = load_object(cls_path)
        verifyClass(ISpiderLoader, loader_cls)
        spider = loader_cls.from_settings(self.settings.frozencopy()).load(args[0])
        self.crawl(spider)
        self.start()

        assert self.crawler_process
        # self.crawler_process.crawl(args[0], **opts.spargs)
        # self.crawler_process.start()
        # if self.crawler_process.bootstrap_failed:
        #     self.exitcode = 1

    def crawl(self,crawler_or_spidercls: type[Spider] | str | Crawler) -> Deferred[None]:
        pass

    def start(self) -> None:
        from twisted.internet import reactor

        d = self.join()
        if d.called:
            return
        d.addBoth(self._stop_reactor)

    @inlineCallbacks
    def join(self) -> Generator[Deferred[Any], Any, None]:
        while self._active:
            yield DeferredList(self._active)

    def _stop_reactor(self, _: Any = None) -> None:
        from twisted.internet import reactor

        try:
            reactor.stop()
        except RuntimeError:  # raised if already stopped or in shutdown stage
            pass
