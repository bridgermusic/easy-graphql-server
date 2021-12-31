"""
    Definition of `ForeignField`, `RelatedField` and, most importantly, `FieldsInfo`.
"""


class LinkedField:
    # pylint: disable=R0903 # Too few public methods
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


class ForeignField(LinkedField): # pylint: disable=R0903 # Too few public methods
    """
        Description of a foreign key field.

        `orm_model` is the ORM model to which the foreign key is pointing.

        `field_name` is the field name on the ORM model that refers the foreign instance.

        `value_field_name` is the actual foreign key, bearing the value of the
        primary key on the other model.
    """

class RelatedField(LinkedField): # pylint: disable=R0903 # Too few public methods
    """
        Description of a "related" field (aka., the opposite of a foreign key field).

        `orm_model` is the ORM model from which the foreign key is pointing.

        `field_name` is the field name on the other ORM model that refers the given instance.

        `value_field_name` is the actual foreign key on the other ORM model, bearing the value
        of the primary key on the given model.
    """


class FieldsInfo: # pylint: disable=R0903 # Too few public methods
    """
        Info about fields for a given ORM model.
    """
    def __init__(self):
        self.primary = None
        self.unique = {}
        self.value = {}
        self.foreign = {}
        self.related = {}
