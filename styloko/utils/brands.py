from styloko.exceptions import MissingBrand

def find_matching_brand(text_to_match, brand_list):

    if not brand_list:
        return None

    brands_length_desc = sorted(list(brand_list), key=len, reverse=True)

    for b in brands_length_desc:
        if b.lower() in text_to_match.lower():
            return b
    raise MissingBrand(u"no brand match for %r" % text_to_match)
