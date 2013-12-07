from scrapy.exceptions import DropItem

# --- In-pipeline exceptions -------------------------------------------

class InconsistentItem(DropItem):
    pass


# --- Item validation exceptions ---------------------------------------

class MissingField(RuntimeError):
    """
    raised when the spider can't determine the appropriate value
    for a mandatory or highly required field
    """
    pass

class MissingBrand(MissingField):
    pass


class StylokoValidationError(AssertionError):
    pass


class MissingRequiredField(StylokoValidationError):
    pass


class InvalidFieldType(StylokoValidationError):
    pass
