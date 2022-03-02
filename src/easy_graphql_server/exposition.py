"""
    Abstract classes for later subclassing and exposition
"""


class Exposed: # pylint: disable=too-few-public-methods
    """
        Base class for `ExposedQuery`, `ExposedMutation` and `ExposedModel`
    """

class ExposedQuery(Exposed): # pylint: disable=too-few-public-methods
    """
        Abstract base class for exposing a query
    """

class ExposedMutation(Exposed): # pylint: disable=too-few-public-methods
    """
        Abstract base class for exposing a mutation
    """

class ExposedModel(Exposed): # pylint: disable=too-few-public-methods
    """
        Abstract base class for exposing a model
    """

class CustomField(Exposed): # pylint: disable=too-few-public-methods
    """
        Abstract base class for exposing a custom field for a model
    """
