"""
    This module defines `Mandatory` class and `JSONString` type.
"""


from .graphql_types import JSONString # pylint: disable=W0611 # Unused import


class Mandatory:
    # pylint: disable=R0903 # Too few public methods
    """
        Non-GraphQL wrapper type, to replace NonNull in mappings or when using
        "natural" Python types
    """
    def __init__(self, type_):
        self.type_ = type_
