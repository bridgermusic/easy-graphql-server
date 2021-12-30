"""
    Base elements to manage specific ORM engines.
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


class OrmModelFields: # pylint: disable=R0903 # Too few public methods
    """
        Base class for description of the fields of an ORM model.
    """
    def __init__(self, orm_model): # pylint: disable=W0613 # Unused argument 'orm_model'
        self.primary = None
        self.unique = {}
        self.value = {}
        self.foreign = {}
        self.related = {}


class OrmModelManager:
    """
        Base class for ORM model manager.

        Useful for `ModelConfig` when exposing GraphQL methods.
    """

    model_fields_class = OrmModelFields

    def __init__(self, orm_model, model):
        self.orm_model = orm_model
        self.model = model
        self.fields = self.get_fields()

    def get_fields(self):
        """
            Compute fields using the class derived from `OrmModelFields`
            corresponding to the given ORM.
        """
        return self.model_fields_class(self.orm_model)

    def get_filters(self):
        """
            Return available filters for the model.
        """
        raise NotImplementedError(
            'Classes inheriting `OrmModelManager` should override `get_filters()` method')
