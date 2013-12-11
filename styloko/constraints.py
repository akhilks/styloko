"""
Item Constrains
---------------

This module provides several classes that can be used as conditions to check
certain item constraints. Conditions are just callables that receive a dict and
*may* raise an AssertionError if the condition is not met.

And define the constraints attribute in your item:

    class Product(Item):
        name = Field()
        price = Field()
        colors = Field()

        constraints = [
            RequiredFields('name', 'price'),
            IsPrice('price'),
            IsList('colors'),
            MinLen(10, 'name'),
        ]

"""

import re
from functools import partial
from styloko.utils import *
from styloko.exceptions import *


class RequiredFields(object):
    """Assert that the specified fields are populated and non-empty"""

    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            v = item.get(f)
            if not v:
                raise MissingRequiredField("missing field: %s" % f)


class IsType(object):
    """Assert that the specified fields are of the given type"""

    def __init__(self, type, *fields):
        self.type = type
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            if f in item:
                v = item.get(f)
                if not isinstance(v, self.type):
                    raise InvalidFieldType(
                        "field %r is not a %s: %r" % \
                            (f, self.type.__name__, v))


class IsListType(object):
    """Assert that the specified fields are a list of elements the given type"""

    def __init__(self, type, *fields):
        self.type = type
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            if f in item:
                l = item.get(f)
                if not isinstance(v, (list, tuple)):
                    raise InvalidFieldType(
                        "field %r is not a list or tuple: %r" % \
                            (f, l))
                if not all([isinstance(v, self.type) for v in l]):
                    raise InvalidFieldType(
                        "not all elements in field %r are of type %s: %r" % \
                            (f, self.type.__name__, v))


IsFloat = partial(IsType, float)
IsString = partial(IsType, basestring)
IsUnicode = partial(IsType, unicode)
IsList = partial(IsType, list)
IsDict = partial(IsType, dict)


class IsURL(object):
    """Assert that the specified fields are full URLs"""

    REGEX_PREFIX = re.compile(r'^https?://')
    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            v = item.get(f)
            if v is None:
                continue
            if not isinstance(v, basestring):
                raise InvalidFieldType(
                    "field %r is not a string: %r" % (f, v))
            if not self.REGEX_PREFIX.search(v):
                raise InvalidFieldType(
                    "field %r (%s) does not start with 'http://' or 'https://'" % (f, v))

class IsNumber(object):
    """Assert that the specified fields are string and contain only numbers"""

    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            v = item.get(f)
            if v is None:
                continue
            if not isinstance(v, basestring):
                raise InvalidFieldType(
                    "field %r is not a string: %r" % (f, v))
            if not v.strip().isdigit():
                raise InvalidFieldType(
                    "field %r contains non-numeric chars: %r" % (f, v))


class IsPrice(object):
    """Assert that the specified fields are string and look like a price"""

    def __init__(self, *fields):
        self.fields = fields

    REGEX_DIGITS = re.compile(r'^[0-9\., ]+$')
    def __call__(self, item):
        for f in self.fields:
            v = item.get(f)
            if v:
                if not isinstance(v, float):
                    raise InvalidFieldType(
                        "field %r's ' is not a float: %r" % (f, v))

class InStringEnum(object):
    """Assert that the specified fields are of the given type"""

    def __init__(self, string_enum, *fields):
        self.enum = string_enum
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:
            if f in item:
                v = item.get(f)
                if not (v in self.enum):
                    raise InvalidFieldType(
                        """field %r's 'item' subfield is not valid: %r;
expected value in %r""" % (f, v, self.enum))


class IsValidSizesList(object):
    """
    Assert that the specified fields are string and look
    like a size-object list
    """

    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:

            l = item.get(f)
            if not l:
                continue
            if not isinstance(l, (list, tuple)):
                raise InvalidFieldType(
                    "field %r is not a list or tuple: %r" % \
                        (f, l))

            # All values in 'sizes' field
            for v in l:
                self.test_list_element(f, v)

    def test_list_element(self, f, v):
        #Must be a dictionary with key.
        if not isinstance(v, dict):
            raise InvalidFieldType("field %r is not a dict %r" % (f, v))

        #Must be have the key 'status'
        if not v.get("status"):
            raise InvalidFieldType(
                "field %r has no 'status' subfield: %r" % (f, v))

        # Must have atleast one of 'brand_size'
        # or ('country_size' and 'country') keys
        if not (
                v.get("brand_size") or
                (v.get("country") and v.get("country_size"))
               ):
            raise InvalidFieldType(
                ("field %r has no 'brand_size' or "
                 "'country' and 'country_size' subfield(s): %r") % (f, v))

        # 'country' key's value must be from KNOWN_COUNTRY_CODES
        if v.get("country") and not(v.get("country") in ALLOWED_COUNTRY_CODES):
            raise InvalidFieldType(
                "field %r's 'country' code is not valid: %r" % (f, v))

        # 'status' key's value must be from KNOWN_SIZE_STATUS
        if not (v.get("status") in ALLOWED_SIZE_STATUSES):
            raise InvalidFieldType(
                "field %r's 'status' code is not valid: %r" % (f, v))


class IsValidTags(object):
    """
    Assert that the specified fields are string and look
    like a size-object list
    """

    def __init__(self, *fields):
        self.fields = fields

    def __call__(self, item):
        for f in self.fields:

            l = item.get(f)
            if not l:
                continue
            if not isinstance(l, (list, tuple)):
                raise InvalidFieldType(
                    "field %r is not a list or tuple: %r" % \
                        (f, l))

            # All values in 'sizes' field
            for v in l:
                self.test_list_element(f, v)

    def test_list_element(self, f, v):
        if not v in ALLOWED_TAGS:
            raise InvalidFieldType(
                "field %r's value is not a valid tag: %r" % (f, v))
