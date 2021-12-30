"""
    Definition of `to_graphql_type_from_django_field`, method converting
    Django ORM model fields to GraphQL type.
"""

import django.db.models
import django.contrib.postgres

from .. import types
from .. import convert


DJANGO_GRAPHQL_TYPES_MAPPING = {
    # boolean
    django.db.models.fields.BooleanField: types.Boolean,
    # integers
    django.db.models.fields.AutoField: types.Int,
    django.db.models.fields.IntegerField: types.Int,
    django.db.models.fields.BigIntegerField: types.Int,
    django.db.models.fields.SmallIntegerField: types.Int,
    # non-integer numbers
    django.db.models.fields.FloatField: types.Float,
    django.db.models.fields.DecimalField: types.Decimal,
    # texts
    django.db.models.fields.CharField: types.String,
    django.db.models.fields.TextField: types.String,
    django.db.models.fields.URLField: types.String,
    # date/time
    django.db.models.fields.DateField: types.Date,
    django.db.models.fields.DateTimeField: types.DateTime,
    django.db.models.fields.TimeField: types.Time,
    # other things
    django.db.models.fields.json.JSONField: types.JSONString,
}


def to_graphql_type_from_django_field(django_field):
    """
        Convert Django ORM model fields to GraphQL type.
    """
    # enum
    if getattr(django_field, 'choices', None):
        graphql_type = convert.to_graphql_enum_from_choices(
            prefix = f'{django_field.model.__name__}__{django_field.name}',
            choices = django_field.choices,
            description = django_field.description,
        )
    # scalar
    elif isinstance(django_field, tuple(DJANGO_GRAPHQL_TYPES_MAPPING)):
        graphql_type = DJANGO_GRAPHQL_TYPES_MAPPING[type(django_field)]
    # list
    elif isinstance(django_field, django.contrib.postgres.fields.array.ArrayField):
        graphql_type = types.List(to_graphql_type_from_django_field(django_field.base_field))
    # unrecognized
    else:
        raise ValueError(f'Could not convert {django_field} to graphql type')
    # result
    return graphql_type
