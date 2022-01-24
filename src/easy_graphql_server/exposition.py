"""
    Abstract classes for later subclassing and exposition
"""


class Exposed: # pylint: disable=R0903 # Too few public methods
    """
        Base class for `ExposedQuery`, `ExposedMutation` and `ExposedModel`
    """

class ExposedQuery(Exposed): # pylint: disable=R0903 # Too few public methods
    """
        Abstract base class for exposing a query
    """

class ExposedMutation(Exposed): # pylint: disable=R0903 # Too few public methods
    """
        Abstract base class for exposing a mutation
    """

class ExposedModel(Exposed): # pylint: disable=R0903 # Too few public methods
    """
        Abstract base class for exposing a model
    """

class CustomField(Exposed): # pylint: disable=R0903 # Too few public methods
    """
        Abstract base class for exposing a custom field for a model
    """
