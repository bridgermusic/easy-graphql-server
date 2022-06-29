"""
    Definition of ORM managers.
"""

import enum
import inspect
import re


@enum.unique
class ORM(enum.Enum):
    """
        Enumeration of available ORM managers.

        Only Django is supported so far.
    """

    UNKNOWN = 0
    DJANGO = 1
    SQLALCHEMY = 2
    PEEWEE = 3

    @classmethod
    def identify(cls, orm_model):
        """
            Identify which ORM the passed model belongs to.
        """
        if inspect.isclass(orm_model):
            inherited_classes_names = tuple(map(
                lambda cls: re.sub(r'^builtins\.', '', f'{cls.__module__}.{cls.__name__}'),
                orm_model.__mro__))
            for inherited_class_name in inherited_classes_names:
                if inherited_class_name.startswith('django.'):
                    return cls.DJANGO
                if inherited_class_name.startswith('peewee.'):
                    return cls.PEEWEE
                if inherited_class_name.startswith('sqlalchemy.'):
                    return cls.SQLALCHEMY
        return cls.UNKNOWN

    @classmethod
    def get_manager_class(cls, orm_model):
        """
            Returns manager class corresponding to a given model.
        """
        # pylint: disable=import-outside-toplevel
        # managers are directly imported below `if` clauses, so we don't have to install
        # all ORMs for `easy_graphql_server` to function
        orm = cls.identify(orm_model)
        if orm == cls.UNKNOWN:
            raise ValueError(
                f'Unrecognized ORM for model, is neither Django, SQLAlchemy or Peewee: {orm_model}')
        if orm == cls.DJANGO:
            from .django_manager import DjangoModelManager
            return DjangoModelManager
        if orm == cls.SQLALCHEMY:
            from .sqlalchemy_manager import SqlAlchemyModelManager
            return SqlAlchemyModelManager
        if orm == cls.PEEWEE:
            from .peewee_manager import PeeweeModelManager
            return PeeweeModelManager
        raise ValueError('This should not happen.')

    @classmethod
    def get_manager(cls, orm_model, model_config, restrict_queried_fields):
        """
            Returns manager object corresponding to a given model.
        """
        manager_class = cls.get_manager_class(orm_model)
        return manager_class(orm_model, model_config, restrict_queried_fields)
