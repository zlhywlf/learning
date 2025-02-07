from __future__ import annotations
from scrapy.settings import Settings

import argparse


from demo.lab import CrawlerProcessLab
from scrapy.commands.crawl import Command as CrawlCommand


class Command(CrawlCommand):

    def short_desc(self) -> str:
        return "Run a spider by demo"

    def run(self, args: list[str], opts: argparse.Namespace) -> None:
        assert isinstance(self.settings, Settings)
        self.crawler_process = CrawlerProcessLab(self.settings)
        super().run(args, opts)
