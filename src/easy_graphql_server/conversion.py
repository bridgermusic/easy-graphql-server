"""
    Helper functions to convert (almost) anything into a GraphQL type, object type or argument.
"""


import inspect
import re
import enum
import datetime
import decimal

from graphql.type.definition import GraphQLType, GraphQLInputField # pylint: disable=
from graphql import \
    GraphQLEnumType, GraphQLEnumValue, \
    GraphQLField, GraphQLArgument, \
    GraphQLObjectType, GraphQLInputObjectType

from . import types, graphql_types, introspection


PYTHON_GRAPHQL_TYPES_MAPPING = {
    # boolean
    bool: graphql_types.Boolean,
    # integers
    int: graphql_types.Int,
    # other numbers
    float: graphql_types.Float,
    decimal.Decimal: graphql_types.Decimal,
    # texts
    str: graphql_types.String,
    # date
    datetime.date: graphql_types.Date,
    datetime.datetime: graphql_types.DateTime,
    datetime.time: graphql_types.Time,
}


_enums_cache = {}


def to_graphql_enum_key(name, capitalize=True):
    """
        Convert an enum name to its GraphQL-compatible counterpart

        (only uppercase letters, underscores and digits, cannot start with a digit)
    """
    key = re.sub(r'(?:^\d|[^a-zA-Z0-9])', '_', name)
    if capitalize:
        return key.upper()
    return key

def to_graphql_enum_from_choices(prefix, choices, description=None, capitalize=True, schema=None):
    # pylint: disable=unused-argument
    """
        Create a `GraphQLEnumType` from a list of choices.

        Choices must presented as a list of key-value pairs.
    """
    if prefix in _enums_cache:
        graphql_type = _enums_cache[prefix]
    else:
        graphql_type = _enums_cache[prefix] = GraphQLEnumType(f'{prefix}__enum_type', {
            to_graphql_enum_key(key, capitalize): GraphQLEnumValue(key, value)
            for key, value in choices
        }, description=description)
    return graphql_type

def to_graphql_type(type_, prefix, for_input=False, schema=None):
    """
        Returns a GraphQL type given a `GraphQLType`, a Python native type,
        a mapping, a single-item list or a subclass of `enum.Enum`.
    """
    # if this is already a graphql type, return it as is
    if introspection.is_instance_or_subclass(type_, GraphQLType):
        return type_
    # mapping
    if isinstance(type_, dict):
        return to_graphql_objecttype(type_, prefix, for_input=for_input, schema=schema)
    if inspect.isclass(type_):
        # convert native Python types
        if type_ in PYTHON_GRAPHQL_TYPES_MAPPING:
            return PYTHON_GRAPHQL_TYPES_MAPPING[type_]
        # enum
        if issubclass(type_, enum.Enum):
            return to_graphql_enum_from_choices(
                prefix = prefix,
                choices = [(key, value.value) for key, value in type_.__members__.items()],
                schema = schema)
    # list
    if isinstance(type_, list) and len(type_) == 1:
        return graphql_types.List(
            to_graphql_type(type_[0], prefix, for_input=for_input, schema=schema)
        )
    # mandatory
    if isinstance(type_, types.Required):
        return graphql_types.NonNull(
            to_graphql_type(type_.type_, prefix, for_input=for_input, schema=schema)
        )
    # existing model interface
    if isinstance(type_, types.ModelInterface):
        model_config = schema.get_model_config(name=type_.model_name)
        if model_config is None:
            raise ValueError(f'No model in schema with name `{type_.model_name}` '
                '(consider changing the order of expositions declaration)')
        mapping = model_config.get_type_mapping(
            operation = type_.operation,
            with_custom_fields = False)
        if not type_.exclude and not type_.additional:
            return to_graphql_type(
                type_ = mapping,
                prefix = model_config.name,
                for_input = for_input,
                schema = schema)
        for field_name in type_.exclude:
            mapping.pop(field_name, None)
        mapping.update(type_.additional)
        return to_graphql_type(
            type_ = mapping,
            prefix = prefix,
            for_input = for_input,
            schema = schema)
    # existing model field
    if isinstance(type_, types.ModelField):
        model_config = schema.get_model_config(name=type_.model_name)
        if model_config is None:
            raise ValueError(f'No model in schema with name `{type_.model_name}` '
                '(consider changing the order of expositions declaration)')
        mapping = model_config.get_type_mapping(with_custom_fields = False)
        try:
            for field_name in type_.field_path:
                mapping = mapping[field_name]
        except KeyError as error:
            raise ValueError(
                f'Invalid field path `{".".join(type_.field_path)}` '
                f'for model named `{type_.model_name}`') from error
        return to_graphql_type(
            type_ = mapping,
            prefix = prefix,
            for_input = for_input,
            schema = schema)
    # oops.
    if isinstance(type_, types.Model):
        raise ValueError('Could not convert `easy_graphql_server.Model` instance '
            'to graphql type, use instead `Model(...).output_format`, '
            '`Model(...).create_input_format` or `Model(...).update_input_format`')
    raise ValueError(f'Could not convert {type_} to graphql type')


_objecttype_cache = {}

def to_graphql_objecttype(type_, prefix, for_input=False, schema=None):
    """
        Returns a `GraphQLInputObjectType` or a `GraphQLObjectType` from a given type.

        Possible input `type_` are `GraphQLObjectType`, or a `dict` mapping of strings
        to types that are supported by `to_graphql_type()`.

        Function returns a `GraphQLObjectType` that uses `GraphQLField` when `for_input == False`,
        a `GraphQLInputObjectType` with `GraphQLInputField` when `for_input == True`.
    """
    # already a field
    if isinstance(type_, GraphQLObjectType):
        return type_
    # in cache
    cache_key = (prefix, for_input)
    if cache_key in _objecttype_cache:
        return _objecttype_cache[cache_key]
    # mapping
    if isinstance(type_, dict):
        if for_input:
            object_type_class = GraphQLInputObjectType
            object_name = f'{prefix}__input_type'
            field_class = GraphQLInputField
        else:
            object_type_class = GraphQLObjectType
            object_name = f'{prefix}__output_type'
            field_class = GraphQLField
        object_type = object_type_class(object_name, lambda : {
            key: field_class(to_graphql_type(
                type_ = value,
                prefix = f'{prefix}__{key}',
                for_input = for_input,
                schema = schema))
            for key, value in type_.items()
        })
        _objecttype_cache[cache_key] = object_type
        return object_type
    # otherwise
    return GraphQLInputField(type_) if for_input else GraphQLField(type_)

def to_graphql_argument(type_, prefix, schema=None):
    """
        Returns a `GraphQLArgument`, taking as argument either a `GraphQLArgument`
        or `dict` mapping of `str` to types that are supported by `to_graphql_type()`.
    """
    # already a field
    if isinstance(type_, GraphQLArgument):
        return type_
    # mapping
    if isinstance(type_, dict):
        return {
            key: (
                value
                if isinstance(value, GraphQLArgument) else
                GraphQLArgument(to_graphql_type(
                    type_ = value,
                    prefix = f'{prefix}__{key}',
                    for_input = True,
                    schema = schema))
            )
            for key, value in type_.items()
        }
    # otherwise
    raise ValueError(f'Could not convert `{type_}` of type `{type(type_)}` to GraphQL argument, '
        'expecting either a instance of `GraphQLArgument` or `dict`')
