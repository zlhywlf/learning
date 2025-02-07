BOT_NAME = "demo"
SPIDER_MODULES = ["scrapy.utils.spider", "demo.spider"]
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0"
)
ROBOTSTXT_OBEY = False
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
COMMANDS_MODULE = "demo.commands"
# DUPEFILTER_CLASS = "mercury.crawlers.scrapy.filter.RedisFilter"
SCHEDULER = "demo.lab.SchedulerLab"
