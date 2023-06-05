"""
    easy_graphql_server is an interface to easily expose a database in GraphQL via ORM models.
"""

from .exceptions import (
    DuplicateError,
    ForbiddenError,
    IntegrityError,
    NotFoundError,
    UnauthenticatedError,
    ValidationError,
)
from .exposition import CustomField, ExposedModel, ExposedMutation, ExposedQuery
from .operations import Operation
from .schema import Schema
from .types import JSONString, Model, Required

__version__ = "0.1.0"

CREATE = Operation.CREATE
READ = Operation.READ
UPDATE = Operation.UPDATE
DELETE = Operation.DELETE
