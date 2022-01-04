"""
    Here are defined some managers to help dealing with case.
"""


import re
import enum


class CaseManager:
    """
        Base case manager, inherited by `PascalCaseManager` and `SnakeCaseManager`
    """

    @classmethod
    def convert_and_join(cls, *names):
        """
            Convert names, and then join them together using the corresponding convention.
        """
        return cls.join(
            cls.convert(name)
            for name in names
        )

    @staticmethod
    def convert(name):
        """
            This method should be overriden in classes inheriting from `CaseManager`.
        """
        raise NotImplementedError()

    @staticmethod
    def join(name):
        """
            This method should be overriden in classes inheriting from `CaseManager`.
        """
        raise NotImplementedError()


class PascalCaseManager(CaseManager):
    """
        Case manager for Pascal casing convention.
    """

    @staticmethod
    def convert(name):
        """
            Convert a name to Pascal case.
        """
        return re.sub(
            r'(?:^|_)([a-zA-Z])([^_]+)',
            lambda m: m.group(1).upper() + m.group(2),
            name
        )

    @staticmethod
    def join(*names):
        """
            Join names using Pascal case convention.
        """
        return ''.join(
            name[0].upper() + name[1:]
            for name in names
        )


class SnakeCaseManager(CaseManager):
    """
        Case manager for snake casing convention.
    """

    @staticmethod
    def convert(name):
        """
            Convert a name to snake case.
        """
        return re.sub(
            r'([a-z])([A-Z])',
            lambda m: f'{m.group(1)}_{m.group(2)}',
            name
        ).lower()

    @staticmethod
    def join(*names):
        """
            Join names using snake case convention.
        """
        return '_'.join(names)


@enum.unique
class Casing(enum.Enum):
    """
        This enum lists available casing styles, and also provides with
        corresponding case managers.
    """
    PASCAL = PascalCaseManager
    SNAKE = SnakeCaseManager
