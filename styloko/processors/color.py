import re

REGEX_SLASH = re.compile(r'|'.join([",", " and ", "&", "/", r'\|', "-"]))
REGEX_UNWANTED = re.compile(r'[ \.\-_]', re.IGNORECASE)


def make_colors_list(color_name):
    color_list = REGEX_SLASH.split(color_name)
    color_list = map(unicode.lower, color_list)
    color_list = map(lambda c: REGEX_UNWANTED.sub('', c), color_list)
    return color_list

