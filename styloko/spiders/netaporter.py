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

RETAILER_DOMAIN = 'net-a-porter.com'
RETAILER_NAME = 'netaporter'
RETAILER_CODE = 'netaporter'

class NetaporterSpiderProduct(StylokoProduct):
    def __init__(self, *args, **kwargs):
        super(NetaporterSpiderProduct, self).__init__(*args, **kwargs)
        #self["retailer"] = RETAILER_CODE

class NetaporterSpider(BaseSpider):
    name = RETAILER_NAME
    allowed_domains = ['net-a-porter.com']
    HOMEPAGE = 'http://www.net-a-porter.com/'
    ALL_DESIGNERS_PAGE = 'http://www.net-a-porter.com/Shop/AZDesigners?cm_sp=topnav-_-designers-_-designeraz'
    DEBUG_CHECK_CONSTRAINTS = True
    LOCALE_CHANGE_URL = 'http://www.net-a-porter.com/intl/home.nap?channel=INTL&country=GB&channel=INTL&country=GB'
    start_urls = [
        LOCALE_CHANGE_URL
    ]

    # --- fetch all category or brand pages ----------------------------
    XPATH_CATEGORY_PAGES = """
       //   div[@class="designer_list_col"]
        /ul/li
            /a/@href
    """
    def parse(self,response):
        return Request(self.ALL_DESIGNERS_PAGE,callback=self.all_designers_page)
    
    def all_designers_page(self, response):
        sel = Selector(response)

        for category_url in sel.xpath(self.XPATH_CATEGORY_PAGES).extract():
            yield Request(
                urlparse.urljoin(response.url, category_url),
                callback=self.parse_category_page)


    # --- from each category page, fetch all product page links --------
    # this would be the XPath expression to loop on product TD cells or DIVs
    XPATH_PRODUCT_LIST_URL = """
        //div[@class="product-images"]
            //a/@href
    """

    def parse_category_page(self, response):
        sel = Selector(response)

        for product_url in sel.xpath(self.XPATH_PRODUCT_LIST_URL).extract():
            yield Request(
                urlparse.urljoin(response.url, product_url),
                callback=self.parse_product_page)

        

    # --- extract product items from product details page --------------
    XPATH_PRODUCT_DETAIL = """
        //div[@id="content"]
    """
    XPATH_PRODUCT_NAME = './/div[@id="product-details"]/h2/text()'
    XPATH_PRODUCT_BRAND = './/div[@id="product-details"]/h1/a/text()'
    XPATH_PRODUCT_CATEGORIES = '//script[contains(text(),analyticsPageData)]/text()'
   
    #FIX ME : Add Xpath of SKU
   
    XPATH_PRODUCT_IMAGE_URLS = './/div[@id="thumbnails-container"]/img/@src'

    XPATH_PRODUCT_CURRENT_PRICE = './/div[@id="price"]/text()'
 

    XPATH_PRODUCT_DESCRIPTION = './/div[@class="tabBody2 tabContent"]//ul/li/text()'
    XPATH_PRODUCT_REFERENCE_NUMBER = '//div[@id="tab2-question"]/span[@class="product-code"]/text()'
    #FIXME: Add Xpath for Keywords / Tags 

    # this usually needs to be parsed
    XPATH_PRODUCT_SIZE = './/select[@id="sku"]/option[not(@value=-1)]/text()'

    def parse_product_page(self, response):
        sel = Selector(response)

        for product in sel.xpath(self.XPATH_PRODUCT_DETAIL):

            l = StylokoProductLoader(NetaporterSpiderProduct(), product)
            l.context['response'] = response

            #l.add_xpath('url', self.XPATH_PRODUCT_URL, absolute_url)
            # this could also be response.url
            l.add_value('url', response.url, absolute_url_value)

            l.add_xpath('name', self.XPATH_PRODUCT_NAME,control_characters_cleaner)
            l.add_xpath('brand', self.XPATH_PRODUCT_BRAND)
            cat = sel.xpath(self.XPATH_PRODUCT_CATEGORIES).re('subsection\d\:.+\"(\w+)\"')
            l.add_value('categories',cat)
            ref_no = sel.xpath(self.XPATH_PRODUCT_REFERENCE_NUMBER).re('\d+')   
            l.add_value('reference_number',ref_no)

            l.add_xpath('description', self.XPATH_PRODUCT_DESCRIPTION,
                Join(u"\n"),
                unicode.strip)

            PRODUCT_IMAGES = sel.xpath(self.XPATH_PRODUCT_IMAGE_URLS).extract()
            l.add_value('images', ' '.join(PRODUCT_IMAGES).replace('xs','pp').replace('//','http://').split())


            
            l.add_xpath('current_price', self.XPATH_PRODUCT_CURRENT_PRICE,
                price_parser)

            
            # remember to add other color variants as another item
            
            l.add_xpath('sizes', self.XPATH_PRODUCT_SIZE,MapCompose(lambda x:"".join(x.split())))

            item = l.load_item(check=self.DEBUG_CHECK_CONSTRAINTS)

            yield item
