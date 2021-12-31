"""
    Definition of `SqlAlchemyManager` class.
"""

from ._manager import Manager


class SqlAlchemyManager(Manager): # pylint:disable=W0223 # Methods are abstract in class 'Manager' but not overridden
    """
        Manager class for SqlAlchemy ORM.
    """
