from scrapy.spider import BaseSpider
from scrapy.selector import Selector
from scrapy.http import Request, FormRequest
from scrapy.contrib.loader.processor import Compose, MapCompose, Join
from scrapy import log
from styloko.items import StylokoProduct, StylokoProductLoader
from styloko.utils.text import *
from styloko.utils.tags import *
from styloko.utils.price import price_parser
from styloko.processors.urls import absolute_url, absolute_url_value
from styloko.processors.color import make_colors_list
import urlparse
import re
import copy
import w3lib


# ----------------------------------------------------------------------

RETAILER_DOMAIN = 'mytheresa.com'
RETAILER_NAME = 'mytheresa'
RETAILER_CODE = 'mytheresa'

class MytheresaSpiderProduct(StylokoProduct):
    def __init__(self, *args, **kwargs):
        super(MytheresaSpiderProduct, self).__init__(*args, **kwargs)


class MytheresaSpider(BaseSpider):
    name = RETAILER_NAME
    allowed_domains = ['mytheresa.com']
    HOMEPAGE = 'http://www.mytheresa.com/'
    ALL_DESIGNERS_PAGE = 'http://www.mytheresa.com/en-de/designers.html'
    DEBUG_CHECK_CONSTRAINTS = True

    start_urls = [
        ALL_DESIGNERS_PAGE,
    ]

    # --- fetch all category or brand pages ----------------------------
    XPATH_CATEGORY_PAGES = """
        //div[@id="designer-list"]//dl/dd/ul/li/a/@href
    """

    def parse(self, response):
        sel = Selector(response)
        for category_url in sel.xpath(self.XPATH_CATEGORY_PAGES).extract():
            yield Request(
                urlparse.urljoin(response.url, category_url),
                callback=self.parse_category_page)


    # --- from each category page, fetch all product page links --------
    # this would be the XPath expression to loop on product TD cells or DIVs
    XPATH_PRODUCT_LIST_URL = """
        //h3[@class="product-name"]/a/@href
    """
    

    def parse_category_page(self, response):
        sel = Selector(response)
        for product_url in sel.xpath(self.XPATH_PRODUCT_LIST_URL).extract():
            yield Request(
                urlparse.urljoin(response.url, product_url),
                callback=self.parse_product_page)

     # --- extract product items from product details page --------------
    XPATH_PRODUCT_DETAIL = """
        //div[@class="product-view"]
    """
    XPATH_PRODUCT_NAME = './/div[@class="product-name"]/h1/text()'
    XPATH_PRODUCT_BRAND = './/h2[@class="designer-name"]/a/text()'
    XPATH_PRODUCT_CATEGORIES = '//div[@class="breadcrumbs"]/ul/li/a/text()'
    XPATH_PRODUCT_COLORS = './/span[@class="product-color"]//text()'
    #FIX ME : Add Xpath of SKU
    #XPATH_PRODUCT_SKU = ''
    XPATH_PRODUCT_IMAGE_URLS = './/img[@class="zoom-trigger"]/@src'

    XPATH_PRODUCT_CURRENT_PRICE = './/div[@class="price-box"]/p[@class="special-price"]/span[@class="price"]/text()'
    XPATH_PRODUCT_CURRENT_PRICE1='.//div[@class="price-box"]//span[@class="regular-price"]/span/text()'

    XPATH_PRODUCT_PREVIOUS_PRICE = './/p[@class="old-price"]/span[@class="price"]/text()'

    XPATH_PRODUCT_DESCRIPTION = './/div[@class="overview"]/ul//text()|//div[@class="overview"]/h5/text()'
    XPATH_PRODUCT_REFERENCE_NUMBER = './/h3[@class="sku-number"]/text()'
    #FIXME: Add Xpath for Keywords / Tags 
    XPATH_PRODUCT_KEYWORDS = ''
    # this usually needs to be parsed
    XPATH_PRODUCT_SIZE = './/ul[@class="sizes"]/li//span[@class="lighter"]/text()|.//ul[@class="sizes"]/li//a/text()'

    def parse_product_page(self, response):
        sel = Selector(response)
        for product in sel.xpath(self.XPATH_PRODUCT_DETAIL):

            l = StylokoProductLoader(MytheresaSpiderProduct(), product)
            l.context['response'] = response

            #l.add_xpath('url', self.XPATH_PRODUCT_URL, absolute_url)
            # this could also be response.url
            l.add_value('url', response.url, absolute_url_value)

            l.add_xpath('name', self.XPATH_PRODUCT_NAME)
            l.add_xpath('brand', self.XPATH_PRODUCT_BRAND)
            l.add_xpath('categories', self.XPATH_PRODUCT_CATEGORIES)
            l.add_xpath('reference_number',self.XPATH_PRODUCT_REFERENCE_NUMBER)
            description=sel.xpath(self.XPATH_PRODUCT_DESCRIPTION).extract()
            description=' '.join(''.join(description).split())
            #l.add_xpath('sku',self.XPATH_PRODUCT_SKU)
            l.add_value('description',description)

            im=[]
            images=sel.xpath(self.XPATH_PRODUCT_IMAGE_URLS).extract()
            for image in images:
                img=''.join(image).replace('thumbnail/100x','image/1000x1000')
                im.append(img)
            l.add_value('images',im)

            l.add_xpath('previous_price', self.XPATH_PRODUCT_PREVIOUS_PRICE ,price_parser)
            current_price1=sel.xpath(self.XPATH_PRODUCT_CURRENT_PRICE).extract()
            current_price2=sel.xpath(self.XPATH_PRODUCT_CURRENT_PRICE1).extract()
            if current_price1:
                current_price=current_price1
            elif current_price2:
                current_price=current_price2
            l.add_value('current_price',current_price,price_parser)    
            #l.add_xpath('current_price', self.XPATH_PRODUCT_CURRENT_PRICE,
                #price_parser)

            #l.add_xpath('keywords',self.XPATH_PRODUCT_KEYWORDS)
            # remember to add other color variants as another item
            #.add_xpath('colors', self.XPATH_PRODUCT_COLORS)
            siz=sel.xpath(self.XPATH_PRODUCT_SIZE).extract()
            if siz:
                sizes = []
                for size in siz:
                    if '- add to wishlist' not in size:
                        sizes.append(size)
                l.add_value('sizes',sizes)
            item = l.load_item(check=self.DEBUG_CHECK_CONSTRAINTS)

            yield item
