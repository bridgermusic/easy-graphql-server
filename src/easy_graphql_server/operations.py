"""
    Basic operations on ORM models are defined here.
"""


import enum


@enum.unique
class Operation(enum.Enum):
    """
        Basic operations that can be performed on an ORM model.
    """

    CREATE = 'create'
    READ = 'read'
    UPDATE = 'update'
    DELETE = 'delete'
    FILTER = 'filter'
