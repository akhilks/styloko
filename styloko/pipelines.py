from styloko.exceptions import InconsistentItem

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

class XmlExportPipeline(object):

    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open('%(spider)s_products%(ts)s.xml' %{'spider':DROP_URL+'/'+spider.name,'ts':datetime.datetime.now().strftime("%Y_%m_%d_T_%H_%M")}, 'wb')
        self.files[spider] = file
        file.write('<?xml version="1.0" encoding="utf-8"?>\n<products>\n')

    def spider_closed(self, spider):
        self.files[spider].write('\n</products>')
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.files[spider].write(producttoxml(item))
        return item


def producttoxml(item):
    item = dict(item)
    for k in item.keys():
        if item[k]:
            i = item[k]
            if isinstance(i,list):
                item[k] = [escape(x) for x in item[k] if isinstance(x,str) or isinstance(x,unicode)]
            elif isinstance(i,str) or isinstance(i,unicode):
                item[k] = escape(i)

    product = "<product "
    if 'reference_number' in item.keys():
        if item['reference_number']:
            product+='id="%s" '%item['reference_number']
    if 'sku' in item.keys():
        if item['sku']:
            product+='sku=%s'%item['sku']
    product+='>\n'
    product+='<url>%(url)s</url><name>%(name)s</name>'%{'name':item['name'],'url':item['url']}
    if 'description' in item.keys():
        if item['description']:
            product+='<description>%s</description>'%item['description']
    product+='<brand>%(brand)s</brand><prices><current>%(current_price)f</current>'%{'brand':item['brand'],'current_price':item['price']}
    if 'previous_price' in item.keys():
        if item['previous_price']:
            product+='<previous>%f</previous>'%item['previous_price']
    product+='</prices>'
    if 'images' in item.keys():
        if item['images']:
            product+='<images>'
            for image in item['images']:
                product+='<image>%s</image>'%image
            product+='</images>'
    if 'categories' in item.keys():
        if item['categories']:
            product+='<categories>'
            for c in item['categories']:
                product+='<category>%s</category>'%c
            product+='</categories>'
    if 'keywords' in item.keys():
        if item['keywords']:
            product+='<keywords>%s</keywords>'%(",".join(item['keywords']))
    if 'sizes' in item.keys():
        if item['sizes']:
            product+='<sizes>'
            for s in item['sizes']:
                product+='<size>%s</size>'%s
            product+='</sizes>'
    if 'colors' in item.keys():
        if item['colors']:
            product+='<colors>'
            for c in product['colors']:
                product+='<color>%s</color>'%c
            product+='</colors>'
    product+='</product>\n'
    return product.encode('ascii', 'xmlcharrefreplace')

