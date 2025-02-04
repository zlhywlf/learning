import argparse
from scrapy.exceptions import UsageError
from scrapy.commands import BaseRunSpiderCommand
from demo.crawler import CrawlerProcess
from scrapy.settings import Settings

class Command(BaseRunSpiderCommand):
    requires_project = True

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
        CrawlerProcess(self.settings, args[0])
        assert self.crawler_process
        # self.crawler_process.crawl(args[0], **opts.spargs)
        # self.crawler_process.start()
        # if self.crawler_process.bootstrap_failed:
        #     self.exitcode = 1