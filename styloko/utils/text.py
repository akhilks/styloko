import re
import w3lib

def control_characters_cleaner(s):
    text = " ".join(s)

    return " ".join(x.strip() for x in w3lib.html.remove_tags(text).split())

def tidy(s):
    return " ".join(x.strip() for x in s.split())

def substring_replace(haystack, needle, replacement=' ',
        stripchars=u'\n\r\t -./\u2013:'):
    if not needle:
        return haystack
    return re.sub(r'(?:^|\s)(?i)%s(?:\s|:|-|$)' % re.escape(needle), replacement,
        haystack).strip(stripchars)
