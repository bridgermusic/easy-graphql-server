import re
import enum


class CaseManager:

    @classmethod
    def convert_and_join(cls, *names):
        return cls.join(
            cls.convert(name)
            for name in names
        )

    @staticmethod
    def convert(name):
        raise NotImplementedError()

    @staticmethod
    def join(name):
        raise NotImplementedError()


class PascalCaseManager(CaseManager):

    @staticmethod
    def convert(name):
        return re.sub(
            r'(?:^|_)([a-zA-Z])([^_]+)',
            lambda m: m.group(1).upper() + m.group(2),
            name
        )

    @staticmethod
    def join(*names):
        return ''.join(
            name[0].upper() + name[1:]
            for name in names
        )


class SnakeCaseManager(CaseManager):

    @staticmethod
    def convert(name):
        return re.sub(
            r'([a-z])([A-Z])',
            lambda m: f'{m.group(1)}_{m.group(2)}',
            name
        ).lower()

    @staticmethod
    def join(*names):
        return '_'.join(names)


@enum.unique
class Casing(enum.Enum):
    PASCAL = PascalCaseManager
    SNAKE = SnakeCaseManager
