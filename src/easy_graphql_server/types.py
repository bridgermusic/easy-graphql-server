"""
    This module defines `Required` class and `JSONString` type.
"""

from .graphql_types import JSONString # pylint: disable=unused-import
from .operations import Operation


class Required:
    # pylint: disable=too-few-public-methods
    """
        Non-GraphQL wrapper type, to replace NonNull in mappings or when using
        "natural" Python types
    """
    def __init__(self, type_):
        self.type_ = type_


class ModelField:
    """
        Non-GraphQL wrapper type, to use the same type as a field of an already exposed model.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, model_name, field_path=None):
        self.model_name = model_name
        self.field_path = field_path or []

    def __getattr__(self, field_name):
        return self.__class__(
            model_name = self.model_name,
            field_path = self.field_path + [field_name],
        )

    __getitem__ = __getattr__

class ModelInterface:
    """
        Non-GraphQL wrapper type, to describe the interface of an already exposed model.
    """
    # pylint: disable=too-few-public-methods

    def __init__(self, model_name, operation, exclude=None, additional=None):
        self.model_name = model_name
        self.operation = operation
        self.exclude = exclude or set()
        self.additional = additional or {}

    def __add__(self, fields):
        return self.__class__(
            model_name = self.model_name,
            operation = self.operation,
            exclude = self.exclude,
            additional = dict(self.additional, **fields))

    def __sub__(self, fields):
        return self.__class__(
            model_name = self.model_name,
            operation = self.operation,
            exclude = self.exclude | set(fields),
            additional = self.additional)

class Model:
    """
        Non-GraphQL wrapper type, to use the same interface as an already exposed model.
    """

    def __init__(self, model_name):
        self.model_name = model_name

    @property
    def create_input_format(self):
        """
            To use the same type as the input of the create mutation
        """
        return ModelInterface(self.model_name, Operation.CREATE)

    @property
    def update_input_format(self):
        """
            To use the same type as the input of the update mutation
        """
        return ModelInterface(self.model_name, Operation.UPDATE)

    @property
    def output_format(self):
        """
            To use the same type as the output format of the exposed model
        """
        return ModelInterface(self.model_name, Operation.READ)

    @property
    def fields(self):
        """
            A mapping to all the fields of the model, regardless of what is exposed
            for this model
        """
        return ModelField(self.model_name)
