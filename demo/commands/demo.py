from __future__ import annotations
from scrapy.settings import Settings

import argparse


from demo.lab import CrawlerProcessCus
from scrapy.commands.crawl import Command as CrawlCommand


class Command(CrawlCommand):

    def short_desc(self) -> str:
        return "Run a spider by demo"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        assert isinstance(self.settings, Settings)
        self.crawler_process = CrawlerProcessCus(self.settings)
        super().run(args, opts)
