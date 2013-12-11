import re
from styloko.utils.status import *


REGEXES_STATUS = (
    (
        # examples:
        # "41 TEMPORARILY SOLD OUT"
        re.compile(r'TEMPORARILY\s+SOLD\s+OUT$', re.I),
        STATUS_COMING_SOON,
    ),
    (
        # examples
        # 9  SOLD OUT
        # XS SOLD OUT
        re.compile(r'SOLD\s+OUT$', re.I),
        STATUS_SOLD_OUT,
    ),
)
REGEXES_SIZES = (
    # digit size + country digit size
    # examples:
    # "14 (UK16)"
    (
        re.compile(
    '(?P<brand_size>[\d/]+)\s+\((?P<country>[A-Z]{2,3})\s*(?P<country_size>\d+).*\)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
            "country": match.group("country"),
            "country_size": match.group("country_size"),
        },
    ),
    (
        re.compile(
    '(?P<brand_size>[XMLS\d/]+)\s+\((?P<country>[A-Z]{2,3})\s*(?P<country_size>[XMLS\d]+).*\)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
            "country": match.group("country"),
            "country_size": match.group("country_size"),
        },
    ),
    # digit sizes + matching digit size
    # examples:
    # "29/34 (11) SOLD OUT"
    (
        re.compile(r'^(?P<brand_size>[\d\./]+)\s*\((?P<other>[\d\-]+).*\)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # letter sizes + matching digit size(range)
    # Examples: "M(8) SOLD OUT"
    (

        re.compile(r'^(?P<brand_size>[A-Z]+)\s*\((?P<other>[\d\-]+).*\)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # digit size + matching letter size(range) (country?)
    # Examples: "1(8) SOLD OUT"
    (
        re.compile(r'^(?P<brand_size>[\d\./]+)\s*\((?P<other>[A-Z/]+).*\)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # digit sizes
    # examples:
    # 10 - SOLD OUT
    # 25/32
    (
        re.compile(r'^(?P<brand_size>[\d\./]+)(\s*-)?(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # some size SOLD_OUT
    (
        re.compile(r'^(?P<brand_size>[\S]+)\s+(-\s*)?SOLD\s+OUT'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # special names
    (
        re.compile(r'^(?P<brand_size>(SMALL|MED(IUM)?|LARGE))(\s|$)',
            re.IGNORECASE),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # letters and country size (AU)
    # XS/6
    (
        re.compile(r'^(?P<brand_size>[XLMS]+)/(?P<country_size>\d+)(\s|$)',
            re.IGNORECASE),
        lambda match: {
            "brand_size": match.group("brand_size"),
            "country_size": match.group("country_size"),
        },
    ),
    # letter sizes
    (
        re.compile(r'^(?P<brand_size>[XLMS]+)(\s|$)', re.IGNORECASE),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # some digits somwhere...
    (
        re.compile(r'(^|\s)(?P<brand_size>[\d\./]+)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
    # some letters somwhere...
    (
        re.compile(r'(^|\s)(?P<brand_size>[XLMS/\-]+)(\s|$)'),
        lambda match: {
            "brand_size": match.group("brand_size"),
        },
    ),
)

def parse_size(size_string, default_status=STATUS_IN_STOCK, ignore=()):
    size = {}

    if size_string in ignore:
        return
    status = default_status
    for regex, reg_status in REGEXES_STATUS:
        m = regex.search(size_string.strip())
        if m:
            status = reg_status
    size.update({"status": status})

    match_found = False
    for regex, func in REGEXES_SIZES:
        m = regex.search(size_string)
        if m:
            match_found = True
            size.update(func(m))
            break

    if not match_found:
        raise RuntimeError("not regex match found for %s" % size_string)

    return size
