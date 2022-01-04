"""
    Definition of `DjangoModelManager` class.
"""

import django.db.models
import django.db.transaction
try:
    import django.contrib.postgres.fields
    postgres_support = True
except ImportError:
    postgres_support = False
import django.core.exceptions

from .. import types
from .. import convert
from .. import exceptions
from ..operations import Operation
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
            # is it mandatory?
            if not field.blank:
                fields_info.mandatory |= {field.name, field.attname}
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

    def create_one(self, authenticated_user, graphql_path, graphql_selection=None, **data):
        # related things
        related_data = {}
        for field_name in list(data.keys()):
            if field_name in self.fields_info.foreign:
                foreign_field = self.fields_info.foreign[field_name]
                foreign_model_config = self.model_config.schema.get_model_config_from_orm_model(
                    orm_model = foreign_field.orm_model)
                foreign_model_config.orm_model_manager.create_one(
                    authenticated_user = authenticated_user,
                    graphql_path = graphql_path + [field_name],
                    **data.pop(field_name))
            elif field_name in self.fields_info.related:
                related_data[field_name] = data.pop(field_name)
        # instance itself
        instance = self.orm_model(**data)
        # save
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            for related_index, related_data in enumerate(children_data):
                related_field = self.fields_info.related[field_name]
                related_data[related_field.value_field_name] = instance.pk
                related_model_config = self.model_config.schema.get_model_config_from_orm_model(
                    orm_model = related_field.orm_model)
                related_instance = related_model_config.orm_model_manager.create_one(
                    authenticated_user = authenticated_user,
                    graphql_path = graphql_path + [related_index, field_name],
                    **related_data)
                getattr(instance, field_name).add(related_instance)
        # validation
        try:
            instance.full_clean()
        except django.core.exceptions.ValidationError as exception:
            self._reraise_validation_error(graphql_path, exception)
        # result
        if graphql_selection is None:
            return instance
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            enforce_permissions = True,
        )

    def read_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        instance = self._read_one(graphql_selection, **filters)
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            enforce_permissions = True,
        )

    def read_many(self, authenticated_user, graphql_path, graphql_selection, **filters):
        return [
            self._instance_to_dict(
                authenticated_user = authenticated_user,
                instance = instance,
                graphql_selection = graphql_selection,
                graphql_path = graphql_path,
                enforce_permissions = False,
            )
            for instance
            in self._read(graphql_selection, **filters).all()
            if self.model_config.check_permissions(
                operation = Operation.READ,
                instance = instance,
                authenticated_user = authenticated_user,
            )
        ]

    def update_one(self, authenticated_user, graphql_path, graphql_selection=None, _=None, **filters):
        data = _ or {}
        # retrieve the instance to update
        instance = self._read_one(graphql_selection or {}, **filters)
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
                            authenticated_user = authenticated_user,
                            graphql_path = graphql_path + [field_name],
                            **child_data)
                    # if identifier provided, update existing instance
                    else:
                        data[field_name] = child_model_config.orm_model_manager.update_one(
                            authenticated_user = authenticated_user,
                            graphql_path = graphql_path + [field_name],
                            _ = child_data,
                            **{child_model_config.orm_model_manager.fields_info.primary:
                                child_identifier})
            # related fields
            elif field_name in self.fields_info.related:
                related_data[field_name] = data.pop(field_name)
        # direct attributes
        for key, value in data.items():
            setattr(instance, key, value)
        # save
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            related_field = self.fields_info.related[field_name]
            child_model_config = self.model_config.schema.get_model_config_from_orm_model(
                orm_model = related_field.orm_model)
            children_identifiers = []
            # create & update
            for child_index, child_data in enumerate(children_data):
                child_identifier = child_data.pop(
                    child_model_config.orm_model_manager.fields_info.primary, None)
                # create if no identifier provided
                if child_identifier is None:
                    child_instance = child_model_config.orm_model_manager.create_one(
                        authenticated_user = authenticated_user,
                        graphql_path = graphql_path + [child_index, field_name],
                        **dict({related_field.value_field_name: instance.pk}, **child_data))
                # update if identifier provided
                else:
                    child_instance = child_model_config.orm_model_manager.update_one(
                        authenticated_user = authenticated_user,
                        graphql_path = graphql_path + [child_index, field_name],
                        _ = child_data,
                        **{child_model_config.orm_model_manager.fields_info.primary:
                            child_identifier})
                # store identifier
                children_identifiers.append(child_instance.pk)
            # delete omitted children
            for child_instance in getattr(instance, field_name).all():
                if child_instance.pk not in children_identifiers:
                    child_instance.delete()
        # validation (raise an easy_graphql_server exception instead of a Django one)
        try:
            instance.full_clean()
        except django.core.exceptions.ValidationError as exception:
            self._reraise_validation_error(graphql_path, exception)
        # result
        if graphql_selection is None:
            return instance
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            enforce_permissions = True,
        )

    def delete_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        instance = self._read_one(graphql_selection, **filters)
        result = self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            enforce_permissions = True,
        )
        instance.delete()
        return result

    # methods should be executed within an atomic database transaction

    @staticmethod
    def decorate(method):
        """
            Every exposed method will have to go through this decorator.
        """
        def decorated(*args, **kwargs):
            with django.db.transaction.atomic():
                return method(*args, **kwargs)
        return decorated

    # helpers for reading

    def _read(self, graphql_selection, **filters):
        return self.build_queryset(graphql_selection).filter(**filters)

    def _read_one(self, graphql_selection, **filters):
        try:
            return self._read(graphql_selection, **filters).get()
        except django.core.exceptions.ObjectDoesNotExist as error:
            raise exceptions.NotFoundError(filters) from error

    def _instance_to_dict(self, instance, authenticated_user, graphql_selection, graphql_path,
            enforce_permissions=True):
        # enforce permissions when requested
        if enforce_permissions:
            self.model_config.enforce_permissions(
                operation = Operation.READ,
                instance = instance,
                authenticated_user = authenticated_user,
                graphql_path = graphql_path,
            )
        # build result
        result = {}
        for field_name, graphql_subselection in graphql_selection.items():
            field_value = getattr(instance, field_name)
            # field_value field
            if graphql_subselection is None:
                result[field_name] = field_value
            # related field
            elif type(field_value).__name__ == 'RelatedManager':
                result[field_name] = [
                    self._instance_to_dict(
                        authenticated_user = authenticated_user,
                        instance = child_instance,
                        graphql_selection = graphql_subselection,
                        graphql_path = graphql_path + [field_name, child_index],
                        enforce_permissions = False,
                    )
                    for child_index, child_instance
                    in enumerate(field_value.all())
                ]
            # foreign field
            elif field_value is not None:
                result[field_name] = self._instance_to_dict(
                    authenticated_user = authenticated_user,
                    instance = field_value,
                    graphql_selection = graphql_subselection,
                    graphql_path = graphql_path + [field_name],
                    enforce_permissions = True,
                )
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

    # validation error

    @staticmethod
    def _reraise_validation_error(graphql_path, exception):

        def serialize(issue, path, field_name=None):
            if hasattr(issue, 'error_dict'):
                for field, errors in issue.error_dict.items():
                    for error in errors:
                        yield from serialize(error, path, field)
            else:
                for error in issue.error_list:
                    message = error.message
                    if error.params:
                        message %= error.params
                    yield {
                        'path': path + [field_name] if field_name else path,
                        'message': str(message),
                        'params': getattr(error, 'params', {}),
                        'code': getattr(error, 'code', None),
                    }

        issues = list(serialize(exception, graphql_path))
        raise exceptions.ValidationError(issues) from exception


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
        django.db.models.fields.EmailField: types.String,
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
        elif postgres_support and isinstance(field, django.contrib.postgres.fields.array.ArrayField):
            graphql_type = types.List(cls._to_graphql_type_from_field(field.base_field))
        # unrecognized
        else:
            raise ValueError(f'Could not convert {field} to graphql type')
        # result
        return graphql_type
