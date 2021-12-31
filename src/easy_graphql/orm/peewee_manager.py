"""
    Definition of `PeeweeManager` class.
"""

from ._manager import Manager


class PeeweeManager(Manager): # pylint:disable=W0223 # Methods are abstract in class 'Manager' but not overridden
    """
        Manager class for Peewee ORM.
    """
