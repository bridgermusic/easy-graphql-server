"""
    Definition of `DjangoModelManager` class.
"""

import django.db.models
import django.db.transaction
import django.contrib.postgres

from .. import types
from .. import convert
from ._manager import ModelManager
from ._fields import FieldsInfo, ForeignField, RelatedField


class DjangoModelManager(ModelManager):
    """
        ModelManager class for Django ORM.
    """

    # metadata extraction

    def get_fields_info(self):
        # pylint: disable=W0212 # Access to a protected member _meta of a client class
        """
            Retrieve fields info for a given Django model.
        """
        # initialize result
        fields_info = FieldsInfo()
        # primary key
        fields_info.primary = self.orm_model._meta.pk.name
        # value & foreign fields_info
        for field in self.orm_model._meta.fields:
            # is it a foreign key?
            if isinstance(field, django.db.models.fields.related.ForeignKey):
                # field to which the foreign key is referring
                related_field = field.foreign_related_fields[0]
                # value field
                fields_info.value[field.attname] = self._to_graphql_type_from_field(related_field)
                # foreign field
                fields_info.foreign[field.name] = ForeignField(
                    orm_model = related_field.model,
                    field_name = field.name,
                    value_field_name = field.attname)
            # if not, it is a regular value field
            else:
                # value field
                fields_info.value[field.name] = self._to_graphql_type_from_field(field)
            # can it serve as a unique identifier?
            if field.unique:
                fields_info.unique[field.attname] = fields_info.value[field.attname]
        # related fields_info
        for related in self.orm_model._meta.related_objects:
            fields_info.related[related.name] = RelatedField(
                orm_model = related.related_model,
                field_name = related.field.name,
                value_field_name = related.field.attname)
        # return result
        return fields_info

    # CRUD operations on ORM model instances

    def create_one(self, graphql_selection=None, **data):
        # related things
        related_data = {}
        for field_name in list(data.keys()):
            if field_name in self.fields_info.foreign:
                data[field_name] = self._create_linked(field_name, data.pop(field_name))
            elif field_name in self.fields_info.related:
                related_data[field_name] = data.pop(field_name)
        # instance itself
        instance = self.orm_model(**data)
        # validation
        instance.full_clean()
        # save
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            for child_data in children_data:
                child_instance = self._create_linked(field_name, child_data, instance)
                getattr(instance, field_name).add(child_instance)
        # in case related data needs cleaning
        instance.clean()
        instance.clean_fields()
        # result
        if graphql_selection is None:
            return instance
        return self._instance_to_dict(instance, graphql_selection)

    def read_one(self, graphql_selection, **filters):
        instance = self._read(graphql_selection, **filters).get()
        return self._instance_to_dict(instance, graphql_selection)

    def read_many(self, graphql_selection, **filters):
        return [
            self._instance_to_dict(instance, graphql_selection)
            for instance
            in self._read(graphql_selection, **filters).all()
        ]

    def update_one(self, graphql_selection=None, _=None, **filters):
        data = _ or {}
        # retrieve the instance to update
        instance = self._read(graphql_selection or {}, **filters).get()
        # related things
        related_data = {}
        for field_name in list(data.keys()):
            # foreign fields
            if field_name in self.fields_info.foreign:
                child_data = data.pop(field_name)
                # if child_data is null, the reference will be deleted
                if child_data is not None:
                    child_model_config = self.model_config.schema.get_model_config_from_orm_model(
                        orm_model = self.fields_info.foreign[field_name].orm_model)
                    child_identifier = child_data.pop(
                        child_model_config.orm_model_manager.fields_info.primary, None)
                    # if no identifier provided, create a new instance
                    if child_identifier is None:
                        data[field_name] = child_model_config.orm_model_manager.create_one(
                            **child_data)
                    # if identifier provided, update existing instance
                    else:
                        data[field_name] = child_model_config.orm_model_manager.update_one(
                            _ = child_data,
                            **{child_model_config.orm_model_manager.fields_info.primary:
                                child_identifier})
            # related fields
            elif field_name in self.fields_info.related:
                related_data[field_name] = data.pop(field_name)
        # direct attributes
        for key, value in data.items():
            setattr(instance, key, value)
        # validation
        instance.full_clean()
        # save
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            related_field = self.fields_info.related[field_name]
            child_model_config = self.model_config.schema.get_model_config_from_orm_model(
                orm_model = related_field.orm_model)
            children_identifiers = []
            # create & update
            for child_data in children_data:
                child_identifier = child_data.pop(
                    child_model_config.orm_model_manager.fields_info.primary, None)
                # create if no identifier provided
                if child_identifier is None:
                    child_instance = child_model_config.orm_model_manager.create_one(
                        **dict({related_field.value_field_name: instance.pk}, **child_data))
                # update if identifier provided
                else:
                    child_instance = child_model_config.orm_model_manager.update_one(**{
                        child_model_config.orm_model_manager.fields_info.primary: child_identifier,
                        '_': child_data})
                # store identifier
                children_identifiers.append(child_instance.pk)
            # delete omitted children
            for child_instance in getattr(instance, field_name).all():
                if child_instance.pk not in children_identifiers:
                    child_instance.delete()
        instance.clean()
        instance.clean_fields()
        # result
        return instance

    def delete_one(self, graphql_selection, **filters):
        instance = self._read(graphql_selection, **filters).get()
        result = self._instance_to_dict(instance, graphql_selection)
        instance.delete()
        return result

    # methods should be executed within an atomic database transaction

    @staticmethod
    def execute_within_transaction(method):
        def decorated(*args, **kwargs):
            with django.db.transaction.atomic():
                return method(*args, **kwargs)
        return decorated

    # helpers for reading

    def _read(self, graphql_selection, **filters):
        return self.build_queryset(graphql_selection).filter(**filters)

    @classmethod
    def _instance_to_dict(cls, instance, graphql_selection):
        result = {}
        for key, graphql_subselection in graphql_selection.items():
            value = getattr(instance, key)
            # value field
            if graphql_subselection is None:
                result[key] = value
            # related field
            elif type(value).__name__ == 'RelatedManager':
                result[key] = [
                    cls._instance_to_dict(child_instance, graphql_subselection)
                    for child_instance in value.all()
                ]
            # foreign field
            elif value is not None:
                result[key] = cls._instance_to_dict(value, graphql_subselection)
        return result

    def build_queryset(self, graphql_selection):
        """
            Build queryset for given GraphQL selection
        """
        base_queryset, only, prefetch_related, select_related = (
            self.build_queryset_parts(graphql_selection)
        )
        return (base_queryset
            .only(*only)
            .prefetch_related(*prefetch_related)
            .select_related(*select_related)
        )

    def build_queryset_parts(self, graphql_selection, field_prefix=''): # pylint: disable=R0914 # Too many local variables
        """
            Build queryset parts for given GraphQL selection

            Parts are returned as a tuple of these four values:
             - the base queryset
             - a list of the only fields to select
             - a list of what should be passed to `QuerySet.prefetch_related()`
             - a list of what should be passed to `QuerySet.select_related()`
        """
        schema = self.model_config.schema
        # initialize result
        base_queryset = self.orm_model.objects
        only = []
        prefetch_related = []
        select_related = []
        # browse fields in GraphQL selection
        for field_name, graphql_subselection in graphql_selection.items():
            # no subselection, this is a direct field
            if graphql_subselection is None:
                only.append(field_prefix + field_name)
            # there is a subselection, and it is a foreign key
            elif field_name in self.fields_info.foreign:
                foreign_field = self.fields_info.foreign[field_name]
                only.append(field_prefix + foreign_field.value_field_name)
                select_related.append(field_prefix + field_name)
                foreign_orm_model_manager = schema.get_model_config_from_orm_model(
                    foreign_field.orm_model).orm_model_manager
                # pylint: disable=W0612 # Unused variable '_'
                _, foreign_only, foreign_prefetch_related, foreign_select_related = (
                    foreign_orm_model_manager.build_queryset_parts(
                        graphql_subselection, f'{field_prefix}{field_name}__')
                )
                only += foreign_only
                prefetch_related += foreign_prefetch_related
                select_related += foreign_select_related
            # there is a subselection, and it is a related field
            elif field_name in self.fields_info.related:
                related_field = self.fields_info.related[field_name]
                related_model_config = schema.get_model_config_from_orm_model(
                    related_field.orm_model)
                prefetch_related.append(
                    django.db.models.Prefetch(
                        field_name,
                        queryset = related_model_config.orm_model_manager.build_queryset(
                            dict({related_field.value_field_name: None}, **graphql_subselection)
                        )
                    )
                )
        # return resulting queryset
        return base_queryset, only, prefetch_related, select_related

    # helpers for creation

    def _create_linked(self, linked_field_name, linked_data, root_instance=None):
        linked_field = self.fields_info.linked[linked_field_name]
        if isinstance(linked_field, RelatedField) and root_instance is not None:
            linked_data[linked_field.value_field_name] = root_instance.pk
        linked_model_config = self.model_config.schema.get_model_config_from_orm_model(
            orm_model = linked_field.orm_model)
        return linked_model_config.orm_model_manager.create_one(**linked_data)

    # Django field conversion to GraphQL type

    GRAPHQL_TYPES_MAPPING = {
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

    @classmethod
    def _to_graphql_type_from_field(cls, field):
        """
            Convert Django ORM model fields to GraphQL type.
        """
        # enum
        if getattr(field, 'choices', None):
            graphql_type = convert.to_graphql_enum_from_choices(
                prefix = f'{field.model.__name__}__{field.name}',
                choices = field.choices,
            )
        # scalar
        elif isinstance(field, tuple(cls.GRAPHQL_TYPES_MAPPING)):
            graphql_type = cls.GRAPHQL_TYPES_MAPPING[type(field)]
        # list
        elif isinstance(field, django.contrib.postgres.fields.array.ArrayField):
            graphql_type = types.List(cls._to_graphql_type_from_field(field.base_field))
        # unrecognized
        else:
            raise ValueError(f'Could not convert {field} to graphql type')
        # result
        return graphql_type
