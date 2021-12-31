"""
    Helper functions to convert (almost) anything into a GraphQL type, object type or argument.
"""


import inspect
import re
import enum
import datetime
import decimal

# Had to disable pylint below, because "No name '...' in module '...'"
from graphql.type.definition import GraphQLType, GraphQLInputField # pylint: disable=E0611
from graphql import \
    GraphQLEnumType, GraphQLEnumValue, \
    GraphQLField, GraphQLArgument, \
    GraphQLObjectType, GraphQLInputObjectType

from . import types


PYTHON_GRAPHQL_TYPES_MAPPING = {
    # boolean
    bool: types.Boolean,
    # integers
    int: types.Int,
    # other numbers
    float: types.Float,
    decimal.Decimal: types.Decimal,
    # texts
    str: types.String,
    # date
    datetime.date: types.Date,
    datetime.datetime: types.DateTime,
    datetime.time: types.Time,
}


_enums_cache = {}

def _is_instance_or_class(thing, klass):
    return isinstance(thing, klass) or (inspect.isclass(thing) and issubclass(thing, klass))

def to_graphql_enum_from_choices(prefix, choices, description=None, capitalize=True):
    """
        Create a `GraphQLEnumType` from a list of choices.

        Choices must presented as a list of key-value pairs.
    """
    if prefix in _enums_cache:
        graphql_type = _enums_cache[prefix]
    else:
        transform = lambda string: string.upper() if capitalize else lambda string: string
        graphql_type = _enums_cache[prefix] = GraphQLEnumType(f'{prefix}__enum_type', {
            transform(re.sub(r'(?:^\d|[^a-zA-Z0-9])', '_', key)): GraphQLEnumValue(key, value)
            for key, value in choices
        }, description=description)
    return graphql_type

def to_graphql_type(type_, prefix, for_input=False):
    """
        Returns a GraphQL type given a `GraphQLType`, a Python native type,
        a mapping, a single-item list or a subclass of `enum.Enum`.
    """
    # if this is already a graphql type, return it as is
    if _is_instance_or_class(type_, GraphQLType):
        return type_
    # mapping
    if isinstance(type_, dict):
        return to_graphql_objecttype(type_, prefix, for_input=for_input)
    if inspect.isclass(type_):
        # convert native Python types
        if type_ in PYTHON_GRAPHQL_TYPES_MAPPING:
            return PYTHON_GRAPHQL_TYPES_MAPPING[type_]
        # enum
        if issubclass(type_, enum.Enum):
            return to_graphql_enum_from_choices(prefix, [
                (key, value.value)
                for key, value in type_.__members__.items()
            ])
    # list
    if isinstance(type_, list) and len(type_) == 1:
        return types.List(
            to_graphql_type(type_[0], prefix, for_input=for_input)
        )
    # oops.
    raise ValueError(f'Could not convert {type_} to graphql type')


_objecttype_cache = {}

def to_graphql_objecttype(type_, prefix, for_input=False):
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
            object_type = GraphQLInputObjectType(f'{prefix}__input_type', lambda : {
                key: GraphQLInputField(
                    to_graphql_type(
                        type_ = value,
                        prefix = f'{prefix}__{key}',
                        for_input = for_input))
                for key, value in type_.items()
            })
        else:
            object_type = GraphQLObjectType(f'{prefix}__output_type', lambda : {
                key: GraphQLField(to_graphql_type(value, f'{prefix}__{key}', for_input=for_input))
                for key, value in type_.items()
            })
        _objecttype_cache[cache_key] = object_type
        return object_type
    # otherwise
    return GraphQLInputField(type_) if for_input else GraphQLField(format)

def to_graphql_argument(type_, prefix):
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
            key: GraphQLArgument(to_graphql_type(value, prefix, for_input=True))
            for key, value in type_.items()
        }
    # otherwise
    raise ValueError(f'Could not convert `{type_}` of type `{type(type_)}` to GraphQL argument, '
        'expecting either a instance of `GraphQLArgument` or `dict`')
