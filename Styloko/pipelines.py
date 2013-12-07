from Styloko.exceptions import InconsistentItem

class ConsistencyPipeline(object):

    @classmethod
    def from_crawler(cls, crawler):
        try:
            pipe = cls.from_settings(crawler.settings)
        except AttributeError:
            pipe = cls()
        pipe.crawler = crawler
        return pipe

    @classmethod
    def from_settings(cls, settings):
        return cls(settings)

    def process_item(self, item, spider):
        try:
            item.check()
            return item
        except AssertionError, e:
            raise InconsistentItem(str(e))
