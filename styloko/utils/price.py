import re

REGEX_DOLLAR_PRICE_001 = re.compile(r'^\$\s*(?P<value>[\d,\. ]+)$')
REGEX_DOLLAR_PRICE_002 = re.compile(
    r"""\$\s*(?P<value>[\d,\. ]+)
        (?P<currency_code>USD|NZD|AUD)""", re.VERBOSE)
REGEX_DOLLAR_PRICE_003 = re.compile(
    r"""\$\s*(?P<currency_code>USD?|NZD?|AUD?)
    (?P<value>[\d,\. ]+)""", re.VERBOSE)

REGEX_DOLLAR_PRICE_004 = re.compile(
    r"""(?P<currency_code>USD|NZD|AUD)\s*\$?\s*(?P<value>[\d,\. ]+)""", re.VERBOSE)

REGEX_DOLLAR_PRICE_005 = re.compile(
    r"""(?P<currency_code_short>US|NZ|AU)\s*\$?\s*(?P<value>[\d,\. ]+)""", re.VERBOSE)

CURRENCY_SHORTCODE_MAP = {
    u'US': 'USD',
    u'NZ': 'NZD',
    u'AU': 'AUD',
}

CURRENCY_SIGN_MAP = {
    u'$': '?',  # U+0024 DOLLAR SIGN, this can be USD, AUD, NZD etc...
    u'\u00a3': 'GBP',   # U+00A3 POUND SIGN
    u'\u00a5': 'JPY',   # U+00A5 YEN SIGN
    u'\u20ac': 'EUR',   # U+20AC EURO SIGN
}
REGEX_CURRENCY_SIGN_START = re.compile(
    u"""(?P<currency_sign>[%(curr_signs)s])
        \s*(?P<value>\d[\d,\. ]+)""" % {
            'curr_signs': ''.join(CURRENCY_SIGN_MAP.keys()).replace('$', '\$')
        },
    re.VERBOSE|re.UNICODE)

REGEX_CURRENCY_SIGN_END = re.compile(
    u"""(?P<value>\d[\d,\. ]+)
        (?P<currency_sign>[%(curr_signs)s])""" % {
            'curr_signs': re.escape(''.join(CURRENCY_SIGN_MAP.keys()))
        },
    re.VERBOSE|re.UNICODE)

REGEX_NUMBER = re.compile(r'^\s*(?P<value>[\d,\. ]+)\s*$')

REGEXES = (
    # regex, matching currency
    #(REGEX_AUD_PRICE_001, 'AUD'),
    #(REGEX_AUD_PRICE_002, 'AUD'),
    (REGEX_DOLLAR_PRICE_002, '?'),
    (REGEX_DOLLAR_PRICE_003, '?'),
    (REGEX_DOLLAR_PRICE_004, '?'),
    (REGEX_DOLLAR_PRICE_005, '?'),
    (REGEX_DOLLAR_PRICE_001, '?'),
    (REGEX_CURRENCY_SIGN_START, '?'),
    (REGEX_CURRENCY_SIGN_END, '?'),
    (REGEX_NUMBER, '?'),
)

REGEX_PRICE_VALUE_NORMALIZE = re.compile(r'(?P<thousands>\d+),'
                                            '(?P<value>\d{3})(,|\.)'
                                            '(?P<cents>\d{2})(\s|$)')
REGEX_PRICE_VALUE_NORMALIZE_ALT = re.compile(r'(?P<thousands>\d+),'
                                            '(?P<value>\d{3})(\s|$)')
def parse_price(price_string):
    price_string = REGEX_PRICE_VALUE_NORMALIZE.sub(
        '\g<thousands>\g<value>.\g<cents>', price_string)
    price_string = REGEX_PRICE_VALUE_NORMALIZE_ALT.sub(
        '\g<thousands>\g<value>.00', price_string)
    price_string = price_string.replace(',', '').strip()

    for r, currency in REGEXES:
        m = r.search(price_string)
        if m:
            try:
                try:
                    if m.group('currency_sign'):
                        currency = CURRENCY_SIGN_MAP.get(
                            m.group('currency_sign'))
                except IndexError:
                    pass

                try:
                    if m.group('currency_code_short'):
                        currency = CURRENCY_SHORTCODE_MAP.get(
                            m.group('currency_code_short'))
                except IndexError:
                    pass

                try:
                    if m.group('currency_code'):
                        currency = m.group('currency_code')
                except IndexError:
                    pass

                return {
                    "currency": currency,
                    "value": float(
                        m.group("value").replace(
                            ',', '.').replace(
                            ' ', ''))
                }
            except:
                # pass
                raise


def price_processor(iter_price):
    for p in iter_price:
        yield parse_price(p)

def price_parser(iter_price):
    for p in iter_price:
        price = parse_price(p)
        yield price['value']
# ----------------------------------------------------------------------

def run_tests():
    tests = (

        (u'$1,097.74 USD', {'currency': 'USD', 'value': 1097.74}),
        (u'$823.31 USD', {'currency': 'USD', 'value': 823.31}),
        (u'$130.87 USD', {'currency': 'USD', 'value': 130.87}),
        (u'$130.87NZD', {'currency': 'NZD', 'value': 130.87}),

        (u'$150.00', {'currency': '?', 'value': 150.0}),
        (u'$ 150.00', {'currency': '?', 'value': 150.0}),
        (u' $43.35  ', {'currency': '?', 'value': 43.35}),
        (u'$5,200', {'currency': '?', 'value': 5200.00}),


        (u'Now \xa327.50', {'currency': 'GBP', 'value': 27.5}),
        (u'Now \xa3 27.50', {'currency': 'GBP', 'value': 27.5}),
        (u'\xa3509.06 GBP', {'currency': 'GBP', 'value': 509.06}),

        (u'AU$129.95', {'currency': 'AUD', 'value': 129.95}),
        (u'AU $129.95', {'currency': 'AUD', 'value': 129.95}),
        (u'AUD $169.00', {'currency': 'AUD', 'value': 169.0}),

        (u'Price $179.95', {'currency': '?', 'value': 179.95}),
        (u'PRICE $200.00', {'currency': '?', 'value': 200.00}),

        (u'\u20ac288.16', {'currency': 'EUR', 'value': 288.16}),

        (u'\u00a3 59,99', {'currency': 'GBP', 'value': 59.99}),

        (u'800.00 \u00a5', {'currency': 'JPY', 'value': 800.0}),
        (u'800.00\u00a5', {'currency': 'JPY', 'value': 800.0}),

        (u'0,00 \u20ac EUR', {'currency': 'EUR', 'value': 0.0}),

        (u'AUD 59.00', {'currency': 'AUD', 'value': 59.0}),

        (u'169.00', {'currency': '?', 'value': 169.0}),
        (u'0,00', {'currency': '?', 'value': 0.0}),

    )

    for t, r in tests:
        print("%s --> gave: %r, expected: %r" % (
            t, parse_price(t), r)
        )
        assert parse_price(t) == r
    return 0

if __name__ == '__main__':
    run_tests()
