"""
    Easy_GraphQL is an interface to easily expose a database in GraphQL via ORM models.
"""

# backwards compatibility with older Python version
if not hasattr(dict, '__ior__'):
    def dict__ior__(self, other):
        """ backwards compatibility with older Python version, dict |= other_dict """
        for key, value in other.items():
            self[key] = value
    dict.__ior__ = dict__ior__

from .types import *
from .schema import Schema
