"""
    Definition of `ForeignField`, `RelatedField` and, most importantly, `FieldsInfo`.
"""


class LinkedField:
    # pylint: disable=too-few-public-methods
    """
        Base class for `ForeignField` and `RelatedField`.
    """

    def __init__(self, orm_model, value_field_name, field_name):
        self.orm_model = orm_model
        self.field_name = field_name
        self.value_field_name = value_field_name

    def __repr__(self):
        return (f'<{self.__class__.__name__} orm_model={self.orm_model.__name__} '
            f'field_name={self.field_name} value_field_name={self.value_field_name}>')


class ForeignField(LinkedField): # pylint: disable=too-few-public-methods
    """
        Description of a foreign key field.

        `orm_model` is the ORM model to which the foreign key is pointing.

        `field_name` is the field name on the ORM model that refers the foreign instance.

        `value_field_name` is the actual foreign key, bearing the value of the
        primary key on the other model.
    """

class RelatedField(LinkedField): # pylint: disable=too-few-public-methods
    """
        Description of a "related" field (aka., the opposite of a foreign key field).

        `orm_model` is the ORM model from which the foreign key is pointing.

        `field_name` is the field name on the other ORM model that refers the given instance.

        `value_field_name` is the actual foreign key on the other ORM model, bearing the value
        of the primary key on the given model.
    """


class FieldsInfo: # pylint: disable=too-few-public-methods
    """
        Info about fields for a given ORM model.
    """
    def __init__(self):
        # primary key as `str`
        self.primary = None
        # unique keys as `dict[str,GraphQLScalarType]`
        self.unique = {}
        # value fields as `dict[str,GraphQLType]`
        self.value = {}
        # foreign fields as `dict[str,ForeignField]`
        self.foreign = {}
        # related fields as `dict[str,RelatedField]`
        self.related = {}
        # linked fields as `dict[str,LinkedField]` (self.foreign | self.related)
        self.linked = None
        # mandatory fields upon creation as `set[str]`
        self.mandatory = set()
        # mandatory fields upon creation as `set[str]`
        self.custom = set()

    def compute_linked(self):
        """
            Merge `self.foreign` and `self.related` into `self.linked`
        """
        self.linked = dict(self.foreign, **self.related)
