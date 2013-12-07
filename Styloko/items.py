from scrapy.item import Item, Field
from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import TakeFirst, MapCompose, Join, Identity
from scrapy.utils.misc import arg_to_iter
from scrapy.utils.python import flatten
from scrunchscraper.constraints import *
import time
import uuid


class StylokoProduct(Item):

    def __init__(self, *args, **kwargs):
        super(StylokoProduct, self).__init__(*args, **kwargs)
        
    # essential fields
    _essential_fields = (
        'brand',
        'url',
        'images',
        'name',
    )

    _important_fields = (
        'price',
        'sizes',
        'colors',
        'categories',
        'description',
    )

    _constraints = [
        RequiredFields(*_essential_fields),
        IsString('uuid', 'label', 'title', 'retailer'),
        #IsURL('url', 'main_image_url'),
        IsPrice('price', 'discounted_price',),
        IsValidGender('gender'),
        IsValidAgeType('age_type'),
        IsValidSizesList('sizes'),
        IsValidProductStatus('product_status'),
        IsList('colors'),
        IsValidTags('tags'),
    ]

    def check(self):
        try:
            for c in self._constraints:
                c(self)
        except AssertionError, e:
            #raise DropItem(str(e))
            raise
        return self

    # --- mandatory ------------------------------
    brand = Field()             # brand of the product
    url = Field()               # canonical URL of the product
    name = Field()  		# product name
    description = Field()       # product description
    categories = Field()          # category, use comma as separator for hierarchies

    # --- optional ------------------------------
    price = Field()             # price as dict {"value": float, "currency": currencycode}
    colors = Field(output_processor=Identity())            # list of strings
    reference_number = Field()
    sizes = Field(output_processor=Identity())
    sku = Field()               # id of the product specified by the retailer
    previous_price = Field() 
    keywords = Field(output_processor=Identity())              # If the product has a tag associated with it - List of Strings
    images = Field(output_processor=Identity())        # URL list of all images for the product
    

class StylokoProductLoader(XPathItemLoader):

    default_output_processor = TakeFirst()

    def load_item(self, check=False):
        item = super(StylokoProductLoader, self).load_item()
        if check:
            item.check()
        return item

    def add_css(self, field_name, css, *processors, **kw):
        values = self._get_cssvalues(css, **kw)
        self.add_value(field_name, values, *processors, **kw)

    def replace_css(self, field_name, css, *processors, **kw):
        values = self._get_values(css, **kw)
        self.replace_value(field_name, values, *processors, **kw)

    def get_xpath(self, css, *processors, **kw):
        values = self._get_cssvalues(css, **kw)
        return self.get_value(values, *processors, **kw)

    def _get_cssvalues(self, csss, **kw):
        csss = arg_to_iter(csss)
        return flatten([self.selector.css(css).extract() for css in csss])
