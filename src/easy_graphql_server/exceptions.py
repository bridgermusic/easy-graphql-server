"""
    Definition of easily serializable exceptions, meant to be thrown from the GraphQL API.
"""

import re

from graphql import GraphQLError
from graphql.language.ast import Node

from . import custom_json


class BaseError(Exception):
    """
        Base exception for `easy_graphql_server`
    """
    def __init__(self, error, payload):
        message = custom_json.dumps({
            'error': error,
            'payload': payload,
        })
        Exception.__init__(self, message)


_graphqlerror__init__ = GraphQLError.__init__
def graphqlerror__init__(self, message, nodes=None, source=None, positions=None, path=None,
        original_error=None, extensions=None):
    """
        Patch for the constructor of GraphQLError class, defined in graphql-core.

        Gives more details, in the same format as BaseError output.
    """
    if original_error is None or not isinstance(original_error, BaseError):
        error = None
        # parse original error message
        possible_errors = (
            ('MISSING_ARGUMENT',
                r"^Field '(?P<parent_type_name>.*?)\.(?P<expected_field_name>.*?)' of required type "
                r"'(?P<expected_type>.*?)' was not provided\."),
            ('MISSING_ARGUMENT',
                r"^Field '(?P<parent_type_name>.*?)' argument '(?P<expected_argument_name>.*?)' of type "
                r"'(?P<expected_type>.*?)' is required, but it was not provided\."),
            ('UNEXPECTED_ARGUMENT',
                r"^Field '(?P<unexpected_argument_name>.*?)' is not defined by type '(?P<parent_type_name>.*?)'\."),
            ('UNEXPECTED_ARGUMENT',
                r"^Unknown argument '(?P<unexpected_argument_name>.*?)' on field '(?:Mutation|Query)\.(?P<method_name>.*?)'\."),
            ('METHOD_NOT_FOUND',
                r"^Cannot query field '(?P<method_name>.*?)' on type '(?:Mutation|Query)'\.$"),
            ('METHOD_NOT_FOUND',
                r"^Cannot query field '(?P<method_name>.*?)' on type '(?:Mutation|Query)'\. Did you mean "
                r"(?P<suggestions>.*?)\?$"),
            ('UNEXPECTED_QUERIED_FIELD',
                r"^Cannot query field '(?P<unexpected_field_name>.*?)' on type '(?P<parent_type_name>.*?)'\.$"),
            ('UNEXPECTED_QUERIED_FIELD',
                r"^Cannot query field '(?P<unexpected_field_name>.*?)' on type '(?P<parent_type_name>.*?)'\. Did you "
                r"mean (?P<suggestions>.*?)\?$"),
            ('WRONGLY_TYPED_ARGUMENT',
                r"^Expected value of type '(?P<expected_field_type>.*?)', found (?P<provided_field_value>.*?)\."),
            ('SYNTAX_ERROR',
                r"^Syntax error: (?P<message>.*?)$"),
            ('WRONG_ENUM_VALUE',
                r"^Value '(?P<provided_field_value>.*?)' does not exist in '(?P<enum_type>.*?)' enum\.$"),
        )
        for possible_error, regex in possible_errors:
            match = re.search(regex, message)
            if match:
                error = possible_error
                payload = match.groupdict() or {}
                break
        if error is None:
            error = 'GRAPHQL'
            payload = {'message': message}
        # parse suggestions
        if error in ('UNEXPECTED_QUERIED_FIELD', 'METHOD_NOT_FOUND'):
            if 'suggestions' in payload:
                payload['suggestions'] = re.findall(r"'([^']+)'", payload['suggestions'])
            else:
                payload['suggestions'] = []
        # build path when possible
        if isinstance(nodes, Node):
            token = nodes.loc.start_token
            if token.kind.value == 'Name':
                path = [token.value]
            ready = False
            while token.prev:
                token = token.prev
                if token.kind.value in '({':
                    ready = True
                elif ready and token.kind.value == 'Name':
                    if path:
                        path.append(token.value)
                    else:
                        path = [token.value]
                    ready = False
            payload['path'] = path = path[::-1]
        # compute message for path
        if error and payload:
            message = custom_json.dumps({
                'error': error,
                'payload': payload,
            })
    return _graphqlerror__init__(
        self, message, nodes, source, positions, path, original_error, extensions)
setattr(GraphQLError, '__init__', graphqlerror__init__)


class InternalError(BaseError):
    """
        Internal coding error
    """
    def __init__(self, exception=None):
        if isinstance(exception, Exception):
            # extract traceback
            tracebacks = []
            traceback = getattr(exception, '__traceback__')
            while traceback:
                tracebacks.append(traceback)
                traceback = traceback.tb_next
            # build payload
            exception_class = type(exception)
            payload = {
                'class': (
                    exception_class.__qualname__
                    if exception_class.__module__ == 'builtins' else
                    f'{exception_class.__module__}.{exception_class.__qualname__}'
                ),
                'args': exception.args,
                'traceback': [
                    f'{traceback.tb_frame.f_code.co_filename}:{traceback.tb_lineno}'
                    for traceback in tracebacks
                ]
            }
        else:
            payload = {}
        BaseError.__init__(self, 'INTERNAL', payload)

class UnauthenticatedError(BaseError):
    """
        Thrown when authentication is required for a query, but not provided.
    """
    def __init__(self):
        BaseError.__init__(self, 'UNAUTHENTICATED', {})

class NotFoundError(BaseError):
    """
        Thrown when an item was not found in database.
    """
    def __init__(self, filters):
        BaseError.__init__(self, 'NOT_FOUND', {
            'filters': filters,
        })

class ForbiddenError(BaseError):
    """
        Thrown when an authenticated user is not allowed to perform an operation
        on a specific item.
    """
    def __init__(self, operation, authenticated_user, path):
        BaseError.__init__(self, 'FORBIDDEN', {
            'operation': operation.name,
            'authenticated_user': str(authenticated_user),
            'path': path,
        })

class ValidationError(BaseError):
    """
        Thrown when attempting to save wrong data into database.
    """
    def __init__(self, issues):
        BaseError.__init__(self, 'VALIDATION', issues)

class DuplicateError(BaseError):
    """
        Thrown when an item is seen as duplicate in database.
    """
    def __init__(self, path):
        BaseError.__init__(self, 'DUPLICATE', {
            'path': path,
        })

class IntegrityError(BaseError):
    """
        Thrown when an item cannot be removed without compromising the database.
    """
    def __init__(self, path):
        BaseError.__init__(self, 'INTEGRITY', {
            'path': path,
        })
