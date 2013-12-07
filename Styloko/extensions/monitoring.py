from scrapy import signals, log
from scrapy.exceptions import NotConfigured
from scrapy.utils.reqser import request_to_dict, request_from_dict
import time

# borrowed from scrapy-sentry project
def response_to_dict(response, spider, include_request=True, **kwargs):
    """Returns a dict based on a response from a spider"""
    d = {
        'time': time.time(),
        'status': response.status,
        'url': response.url,
        'headers': dict(response.headers),
        'body': response.body,
      }
    if include_request:
        d['request'] = request_to_dict(response.request, spider)
    return d


class StatsNotifier(object):

    SETTING_ENABLED = 'SENTRY_NOTIFICATIONS_ENABLED'
    SETTING_DSN = 'SENTRY_DSN'

    def __init__(self, stats, settings, *args, **kwargs):
        self.stats = stats
        self.items_scraped = 0
        self.items_dropped = 0

        self.settings = settings
        self.sentry_enabled = False

        if (self.settings.get(self.SETTING_ENABLED, False)
            and self.settings.get(self.SETTING_DSN)):
                self.sentry_client = self.get_sentry_client()
                if self.sentry_client:
                    self.sentry_enabled = True
        else:
            self.sentry_client = None

    def get_sentry_client(self):
        try:
            import raven
            log.msg("Monitoring: initializing raven with DSN [%s]" % self.settings.get(self.SETTING_DSN))
            return raven.Client(self.settings.get(self.SETTING_DSN))
        except:
            log.msg("DSN: [%s]" % self.settings.get(self.SETTING_DSN))
            return None

    @classmethod
    def from_crawler(cls, crawler):
        # first check if the extension should be enabled and raise
        # NotConfigured otherwise

        #if not crawler.settings.getbool(cls.SETTING_ENABLED):
            #raise NotConfigured

        # instantiate the extension object
        ext = cls(crawler.stats, crawler.settings)

        # connect the extension object to signals
        #crawler.signals.connect(ext.spider_opened, signal=signals.spider_opened)
        #crawler.signals.connect(ext.spider_closed, signal=signals.spider_closed)

        crawler.signals.connect(ext.spider_error, signal=signals.spider_error)
        crawler.signals.connect(ext.item_dropped, signal=signals.item_dropped)

        #crawler.signals.connect(ext.item_scraped, signal=signals.item_scraped)

        # return the extension object
        return ext

    def spider_opened(self, spider):
        spider.log("opened spider %s" % spider.name)

    def spider_closed(self, spider):
        spider.log("closed spider %s" % spider.name)

    def item_scraped(self, item, response, spider):
        self.items_scraped += 1
        spider.log("scraped %d items" % self.items_scraped)

    def item_dropped(self, item, spider, exception):

        # FIXME: look what exception was fetched
        #        and notify interested parties
        self.items_dropped += 1
        spider.log("dropped %d items" % self.items_dropped)

        if self.sentry_enabled:
            msg = self.sentry_client.captureMessage(repr(exception))

            ident = self.sentry_client.get_ident(msg)
            l = spider.log if spider else log.msg
            l("Sentry Exception ID '%s'" % ident, level=log.INFO)

            return ident

    # borrowed from scrapy-sentry project
    def spider_error(self, failure, response, spider, signal=None, sender=None, *args, **kwargs):

        if self.sentry_enabled:
            import StringIO
            traceback = StringIO.StringIO()
            failure.printTraceback(file=traceback)

            message = signal
            extra = {
                    'sender': sender,
                    'spider': spider.name,
                    'signal': signal,
                    'failure': failure,
                    'response': response_to_dict(response, spider, include_request=True),
                    'traceback': "\n".join(traceback.getvalue().split("\n")[-5:]),
                }
            msg = self.sentry_client.captureMessage(
                message=u"[{}] {}".format(spider.name, repr(failure.value)),
                extra=extra) #, stack=failure.stack)

            ident = self.sentry_client.get_ident(msg)

            l = spider.log if spider else log.msg
            l("Sentry Exception ID '%s'" % ident, level=log.INFO)

            return ident
