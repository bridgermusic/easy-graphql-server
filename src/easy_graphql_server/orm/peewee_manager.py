"""
    Definition of `PeeweeModelManager` class.
"""

from ._manager import ModelManager


# pylint:disable=W0223 # Methods are abstract in class 'ModelManager' but not overridden

class PeeweeModelManager(ModelManager):
    """
        ModelManager class for Peewee ORM.
    """

    # remove Pylint disabling above class declaration when overridding methods
