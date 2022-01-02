"""
    Definition of `SqlAlchemyModelManager` class.
"""

from ._manager import ModelManager


# pylint:disable=W0223 # Methods are abstract in class 'ModelManager' but not overridden


class SqlAlchemyModelManager(ModelManager):
    """
        ModelManager class for SqlAlchemy ORM.
    """

    # remove Pylint disabling above class declaration when overridding methods
