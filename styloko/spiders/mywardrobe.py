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

RETAILER_DOMAIN = 'my-wardrobe.com'
RETAILER_NAME = 'mywardrobe'
RETAILER_CODE = 'mywardrobe'

class MywardrobeSpiderProduct(StylokoProduct):
    def __init__(self, *args, **kwargs):
        super(MywardrobeSpiderProduct, self).__init__(*args, **kwargs)

class MywardrobeSpider(BaseSpider):
    name = RETAILER_NAME
    allowed_domains = ['my-wardrobe.com']
    HOMEPAGE = 'http://www.my-wardrobe.com/'
    DESIGNERS_PAGE = 'http://www.my-wardrobe.com/core/call_backs/set_user_currency.php?c=GBP&rdt=aHR0cDovL3d3dy5teS13YXJkcm9iZS5jb20vd29tZW5zd2Vhci9mYXNoaW9uLWRlc2lnbmVycw=='
    DEBUG_CHECK_CONSTRAINTS = True

    start_urls = [
        DESIGNERS_PAGE
    ]

    # --- fetch all category or brand pages ----------------------------
    XPATH_CATEGORY_PAGES = """
        //*[@id="designer-page"]/div[2]
            /div[@class="list-of-designers"]/div
                /h3/a/@href
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
        //div[@class="item-container"]/a[1]/@href
    """

    def parse_category_page(self, response):
        sel = Selector(response)

        for product_url in sel.xpath(self.XPATH_PRODUCT_LIST_URL).extract():
            yield Request(
                product_url,
                callback=self.parse_product_page)


    # --- extract product items from product details page --------------
    XPATH_PRODUCT_DETAIL = """
        //div[@class="main_wrapper"]
    """
    XPATH_PRODUCT_NAME = './/*[@id="details"]/h1/text()'
    XPATH_PRODUCT_BRAND = './/*[@id="details"]/h2/a/text()'
    XPATH_PRODUCT_CATEGORIES = '//*[@id="bottom-line"]/div[1]/li[position()>1]/a/text()'
    #XPATH_PRODUCT_COLOR = './/span[@class="product-color"]//text()'


    XPATH_PRODUCT_IMAGE_JAVASCRIPT = './/div[@id="product-images"]/script[1]/text()'

    XPATH_PRODUCT_CURRENT_PRICE = './/*[@id="details"]/div[2]/text()'
    #XPATH_PRODUCT_PREVIOUS_PRICE = './/span[@class="product-price-discount"]//text()'

    XPATH_PRODUCT_DESCRIPTION = './/*[@id="information"]/ul[2]/li[2]/text()'
    XPATH_PRODUCT_REFERENCE_NUMBER = '//p[@class="barcode"]/text()'
    # this usually needs to be parsed
    XPATH_PRODUCT_SIZE = './/*[@id="ns_item_id"]/option/text()'

    def parse_product_page(self, response):
        sel = Selector(response)

        for product in sel.xpath(self.XPATH_PRODUCT_DETAIL):

            l = StylokoProductLoader(MywardrobeSpiderProduct(), product)
            l.context['response'] = response

            #l.add_xpath('url', self.XPATH_PRODUCT_URL, absolute_url)
            # this could also be response.url
            l.add_value('url', response.url, absolute_url_value)

            ref_no = sel.xpath(self.XPATH_PRODUCT_REFERENCE_NUMBER).re('\d+')   
            l.add_value('reference_number',ref_no)
            l.add_xpath('name', self.XPATH_PRODUCT_NAME)
            l.add_xpath('brand', self.XPATH_PRODUCT_BRAND)
            l.add_xpath('categories',self.XPATH_PRODUCT_CATEGORIES)

            l.add_xpath('description', self.XPATH_PRODUCT_DESCRIPTION,
                Join(u"\n"),
                unicode.strip)

            PRODUCT_IMAGES = sel.xpath(self.XPATH_PRODUCT_IMAGE_JAVASCRIPT).extract()[0]
            l.add_value('images', re.findall(r'highRes\[.\] =\s*\'(.*?)\';',PRODUCT_IMAGES,re.DOTALL|re.MULTILINE))

            l.add_xpath('current_price', self.XPATH_PRODUCT_CURRENT_PRICE,price_parser)
       
            l.add_xpath('sizes', self.XPATH_PRODUCT_SIZE)

            item = l.load_item(check=self.DEBUG_CHECK_CONSTRAINTS)

            yield item
