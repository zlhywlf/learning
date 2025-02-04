from __future__ import annotations
from typing import Any

from twisted.internet.defer import Deferred
from zope.interface.verify import verifyClass

from scrapy.interfaces import ISpiderLoader
from scrapy.settings import Settings
from scrapy.utils.misc import load_object


class CrawlerProcess:
    def __init__(self,settings: Settings,spidercls:str):
        cls_path = settings.get("SPIDER_LOADER_CLASS")
        loader_cls = load_object(cls_path)
        verifyClass(ISpiderLoader, loader_cls)
        self._spider = loader_cls.from_settings(settings.frozencopy()).load(spidercls)
        self.settings: Settings = settings
        self._crawlers: set[Any] = set()
        self._active: set[Deferred[None]] = set()
        self.bootstrap_failed = False
        self._initialized_reactor: bool = False