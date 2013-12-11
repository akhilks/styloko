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

RETAILER_DOMAIN = 'matchesfashion.com'
RETAILER_NAME = 'matchesfashion'
RETAILER_CODE = 'matchesfashion'

class MatchesfashionSpiderProduct(StylokoProduct):
    def __init__(self, *args, **kwargs):
        super(MatchesfashionSpiderProduct, self).__init__(*args, **kwargs)

class MatchesfashionSpider(BaseSpider):
    name = RETAILER_NAME
    allowed_domains = ['matchesfashion.com']
    HOMEPAGE = 'http://www.matchesfashion.com/'
    ALL_DESIGNERS_PAGE = 'http://www.matchesfashion.com/designer/womens#indexes'
    DEBUG_CHECK_CONSTRAINTS = True

    start_urls = [
        ALL_DESIGNERS_PAGE,
    ]

    # --- fetch all category or brand pages ----------------------------
    XPATH_CATEGORY_PAGES = """
        //div[@class="indexes-list"]
            //ol/li
                /a/@href
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
    //div[@class="products"]/div
        /a[contains(@href,"/product/")]
            /@href
    """
    

    def parse_category_page(self, response):
        sel = Selector(response)

        for product_url in sel.xpath(self.XPATH_PRODUCT_LIST_URL).extract():
            yield Request(
                urlparse.urljoin(response.url, product_url),
                callback=self.parse_product_page)

        


    # --- extract product items from product details page --------------
    XPATH_PRODUCT_DETAIL = """
        //div[@class="product-details"]
    """
    XPATH_PRODUCT_NAME = './/div[@class="info"]/h3[@class="description"]/text()'
    XPATH_PRODUCT_BRAND = '//h2[@class="designer"]/a/text()'
    XPATH_PRODUCT_CATEGORIES = './/span/strong/a/text()'
    #FIX ME : Add Xpath of SK
    XPATH_PRODUCT_IMAGE_URLS = './/div[@class="image-list"]//img/@src'

    XPATH_PRODUCT_CURRENT_PRICE = './/div[@class="indicative-price"]/div[last()]/text()'

    XPATH_PRODUCT_DESCRIPTION = './/div[@class="scroll"]/p/text()'
    XPATH_PRODUCT_REFERENCE_NUMBER = './/div[@class="info"]/h3[@class="description"]/text()'
    #FIXME: Add Xpath for Keywords / Tags 
    # this usually needs to be parsed
    XPATH_PRODUCT_SIZE = './/div[@class="sizes"]/select/option[not(text()="SELECT SIZE")]/text()'

    def parse_product_page(self, response):
        sel = Selector(response)

        for product in sel.xpath(self.XPATH_PRODUCT_DETAIL):

            l = StylokoProductLoader(MatchesfashionSpiderProduct(), product)
            l.context['response'] = response

            #l.add_xpath('url', self.XPATH_PRODUCT_URL, absolute_url)
            # this could also be response.url
            l.add_value('url', response.url, absolute_url_value)
            name = sel.xpath(self.XPATH_PRODUCT_NAME).re('(.+) \(')
            l.add_value('name',name)
            l.add_xpath('brand', self.XPATH_PRODUCT_BRAND)
            l.add_xpath('categories', self.XPATH_PRODUCT_CATEGORIES)

            l.add_value('reference_number',sel.xpath(self.XPATH_PRODUCT_REFERENCE_NUMBER).re('\((\d+)\)'))
            #l.add_xpath('sku',self.XPATH_PRODUCT_SKU)
            l.add_xpath('description', self.XPATH_PRODUCT_DESCRIPTION,
                Join(u"\n"),
                unicode.strip)

            l.add_xpath('images', self.XPATH_PRODUCT_IMAGE_URLS,
                absolute_url)

            #l.add_xpath('previous_price', self.XPATH_PRODUCT_CURRENT_PRICE,price_parser)
            l.add_xpath('current_price', self.XPATH_PRODUCT_CURRENT_PRICE,
                price_parser)

            
            #l.add_xpath('keywords',self.XPATH_PRODUCT_KEYWORDS)
            # remember to add other color variants as another item
            #l.add_xpath('colors', self.XPATH_PRODUCT_COLORS)

            l.add_xpath('sizes', self.XPATH_PRODUCT_SIZE)

            item = l.load_item(check=self.DEBUG_CHECK_CONSTRAINTS)

            yield item
