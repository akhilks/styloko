from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request, FormRequest
from scrapy.contrib.loader.processor import Compose, MapCompose, Join
from scrapy import log
from scrunchscraper.items import StylokoProduct, StylokoProductLoader
from scrunchscraper.utils.text import *
from scrunchscraper.utils.tags import *
from scrunchscraper.processors.urls import absolute_url, absolute_url_value
from scrunchscraper.processors.color import make_colors_list
import urlparse
import re
import copy
import w3lib


# ----------------------------------------------------------------------

RETAILER_DOMAIN = '$domain'
RETAILER_NAME = '$name'
RETAILER_CODE = '$name'

class ${classname}Product(ScrunchProduct):
    def __init__(self, *args, **kwargs):
        super(${classname}Product, self).__init__(*args, **kwargs)
        self["retailer"] = RETAILER_CODE

class $classname(BaseSpider):
    name = RETAILER_NAME
    allowed_domains = ['$domain']
    HOMEPAGE = 'http://www.$domain/'

    DEBUG_CHECK_CONSTRAINTS = True

    start_urls = [
        HOMEPAGE,
    ]

    # --- fetch all category or brand pages ----------------------------
    XPATH_CATEGORY_PAGES = """
        //ul[@id="nav"]
            /li[@class="category"]
                //a/@href
    """

    def parse(self, response):
        hxs = HtmlXPathSelector(response)

        for category_url in hxs.select(self.XPATH_CATEGORY_PAGES).extract():
            yield Request(
                urlparse.urljoin(response.url, category_url),
                callback=self.parse_category_page)


    # --- from each category page, fetch all product page links --------
    # this would be the XPath expression to loop on product TD cells or DIVs
    XPATH_PRODUCT_LIST_URL = """
        //div[@id="product-list"]
            //div[@class="product"]
                //a[@class="product-url"]/@href
    """
    XPATH_NEXT_PAGES = """
        //div[@id="pagination"]
            //a[@title="Next"]/@href
    """

    def parse_category_page(self, response):
        hxs = HtmlXPathSelector(response)

        for product_url in hxs.select(self.XPATH_PRODUCT_LIST_URL).extract():
            yield Request(
                urlparse.urljoin(response.url, product_url),
                callback=self.parse_product_page)

        for next_page_url in hxs.select(self.XPATH_NEXT_PAGES).extract():
            yield Request(
                urlparse.urljoin(response.url, next_page_url),
                callback=self.parse_category_page)


    # --- extract product items from product details page --------------
    XPATH_PRODUCT_DETAIL = """
        //div[@id="product-details"]
    """
    XPATH_PRODUCT_NAME = './/span[@class="product-title"]//text()'
    XPATH_PRODUCT_BRAND = './/span[@class="product-brand"]//text()'
    XPATH_PRODUCT_CATEGORY = './/span[@class="product-category"]//text()'
    XPATH_PRODUCT_COLOR = './/span[@class="product-color"]//text()'
    # other colors variants need to spawn a new item
    XPATH_PRODUCT_OTHER_COLOR = './/span[@class="product-alt-color"]//text()'

    XPATH_PRODUCT_URL = './/a[@class="product-url"]/@href'
    XPATH_PRODUCT_IMAGE_URL = './/img[@class="product-image"]/@src'
    XPATH_PRODUCT_OTHER_IMAGE_URL = './/img[@class="product-alt-image"]/@src'

    XPATH_PRODUCT_PRICE = './/span[@class="product-price"]//text()'
    XPATH_PRODUCT_PRICE_DISCOUNT = './/span[@class="product-price-discount"]//text()'

    XPATH_PRODUCT_DESCRIPTION = './/span[@class="product-description"]//text()'

    # this usually needs to be parsed
    XPATH_PRODUCT_SIZE = './/select[@class="product-size"]/option//text()'

    def parse_product_page(self, response):
        hxs = HtmlXPathSelector(response)

        for product in hxs.select(self.XPATH_PRODUCT_DETAIL):

            l = ScrunchProductLoader(${classname}Product(), product)
            l.context['response'] = response

            #l.add_xpath('url', self.XPATH_PRODUCT_URL, absolute_url)
            # this could also be response.url
            l.add_value('url', response.url, absolute_url_value)

            l.add_xpath('title', self.XPATH_PRODUCT_TITLE)
            l.add_xpath('label', self.XPATH_PRODUCT_BRAND)
            l.add_xpath('category', self.XPATH_PRODUCT_CATEGORY,
                MapCompose(Join(u', '), unicode.lower))

            l.add_xpath('description', self.XPATH_PRODUCT_DESCRIPTION,
                Join(u"\n"),
                unicode.strip)

            # if you can determine the target gender
            l.add_xpath('gender', self.XPATH_PRODUCT_GENDER)

            # if you can determine the target age type
            l.add_xpath('age_type', self.XPATH_PRODUCT_AGE_TYPE)

            l.add_xpath('main_image_url', self.XPATH_PRODUCT_IMAGE_URL,
                absolute_url)
            l.add_xpath('image_urls', self.XPATH_PRODUCT_OTHER_IMAGE_URL,
                absolute_url)

            l.add_xpath('price', self.XPATH_PRODUCT_PRICE, price_processor)
            l.add_xpath('discounted_price', self.XPATH_PRODUCT_PRICE_DISCOUNT,
                price_processor)

            # remember to add other color variants as another item
            l.add_xpath('colors', self.XPATH_PRODUCT_COLOR,
                MapCompose(unicode.lower))

            l.add_xpath('sizes', self.XPATH_PRODUCT_SIZE,
                MapCompose(unicode.lower))

            item = l.load_item(check=self.DEBUG_CHECK_CONSTRAINTS)

            color_variants = product.select(self.XPATH_PRODUCT_OTHER_COLOR).extract()

            yield item

            if color_variants:
                for color_variant in color_variants:
                    item_variant = copy.deepcopy(item)
                    item_variant['colors'] = [color_variant]
                    yield item_variant
