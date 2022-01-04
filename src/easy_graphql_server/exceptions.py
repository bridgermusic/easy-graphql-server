"""
    Definition of easily serializable exceptions, meant to be thrown from the GraphQL API.
"""

import json


class BaseError(Exception):
    """
        Base exception for `easy_graphql_server`
    """
    def __init__(self, error, payload):
        message = json.dumps({
            'error': error,
            'payload': payload,
        })
        Exception.__init__(self, message)


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
