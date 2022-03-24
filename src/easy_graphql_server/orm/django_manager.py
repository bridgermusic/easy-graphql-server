"""
    Definition of `DjangoModelManager` class.
"""

import django.db
import django.db.models
import django.db.transaction
from django.conf import settings
try:
    import django.contrib.postgres.fields
    WITH_POSTGRES_SUPPORT = True
except ImportError:
    WITH_POSTGRES_SUPPORT = False
import django.core.exceptions

from .. import graphql_types
from .. import conversion
from .. import exceptions
from ..operations import Operation
from .django_errors import reraise_django_validation_error
from ._manager import ModelManager
from ._fields import FieldsInfo, ForeignField, RelatedField


class DjangoModelManager(ModelManager):
    """
        ModelManager class for Django ORM.
    """

    # metadata extraction

    def get_fields_info(self):
        """
            Retrieve fields info for a given Django model.
        """
        # initialize result
        fields_info = FieldsInfo()
        # primary key
        fields_info.primary = self.orm_model._meta.pk.name # pylint: disable=protected-access
        # value & foreign fields_info
        for field in self.orm_model._meta.fields: # pylint: disable=protected-access
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
        for related in self.orm_model._meta.related_objects: # pylint: disable=protected-access
            fields_info.related[related.name] = RelatedField(
                orm_model = related.related_model,
                field_name = related.field.name,
                value_field_name = related.field.attname)
        # return result
        return fields_info

    # CRUD operations on ORM model instances

    def create_one(self, authenticated_user, graphql_path, graphql_selection=None, ensure_permission=True, **data):
        # related things
        related_data = {}
        for field_name in list(data.keys()):
            if field_name in self.fields_info.foreign:
                foreign_field = self.fields_info.foreign[field_name]
                foreign_model_config = self.model_config.schema.get_model_config(
                    orm_model = foreign_field.orm_model)
                foreign_instance = foreign_model_config.orm_model_manager.create_one(
                    authenticated_user = authenticated_user,
                    graphql_path = graphql_path + [field_name],
                    ensure_permission = False,
                    **data.pop(field_name))
                data[field_name] = foreign_instance
            elif field_name in self.fields_info.related:
                related_data[field_name] = data.pop(field_name)
        # extract data for custom fields
        custom_fields_data = self._extract_custom_fields_data(
            operation = Operation.CREATE,
            data = data)
        # instance itself
        instance = self.orm_model(**data)
        # custom fields definition
        self._create_custom_fields(
            instance = instance,
            authenticated_user = authenticated_user,
            data = custom_fields_data)
        # pre-save trigger
        self.model_config.on_before_operation(instance, authenticated_user, Operation.CREATE, data)
        # enforce permissions
        if ensure_permission:
            self.model_config.ensure_permission(
                operation = Operation.CREATE,
                instance = instance,
                authenticated_user = authenticated_user,
                graphql_path = graphql_path,
                data = data,
            )
        # validation
        try:
            instance.full_clean()
        except django.core.exceptions.ValidationError as exception:
            reraise_django_validation_error(graphql_path, exception)
        # save
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            for related_index, related_data in enumerate(children_data):
                related_field = self.fields_info.related[field_name]
                related_data[related_field.value_field_name] = instance.pk
                related_model_config = self.model_config.schema.get_model_config(
                    orm_model = related_field.orm_model)
                related_instance = related_model_config.orm_model_manager.create_one(
                    authenticated_user = authenticated_user,
                    graphql_path = graphql_path + [field_name, related_index],
                    ensure_permission = False,
                    **related_data)
                getattr(instance, field_name).add(related_instance)
        # validation
        try:
            if callable(getattr(instance, 'clean_related', None)):
                instance.clean_related()
        except django.core.exceptions.ValidationError as exception:
            reraise_django_validation_error(graphql_path, exception)
        # post-save trigger
        self.model_config.on_after_operation(instance, authenticated_user, Operation.CREATE, data)
        # result
        if graphql_selection is None:
            return instance
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            ensure_permission = False,
        )

    def read_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        instance = self._read_one(
            graphql_selection = graphql_selection,
            authenticated_user = authenticated_user,
            **filters
        )
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            ensure_permission = True,
        )

    def read_many(self, authenticated_user, graphql_path, graphql_selection, **filters):
        return [
            self._instance_to_dict(
                authenticated_user = authenticated_user,
                instance = instance,
                graphql_selection = graphql_selection,
                graphql_path = graphql_path,
                ensure_permission = False,
            )
            for instance in self._read(
                graphql_selection = graphql_selection,
                authenticated_user = authenticated_user,
                **filters
            ).all()
            if self.model_config.has_permission(
                operation = Operation.READ,
                instance = instance,
                authenticated_user = authenticated_user,
            )
        ]

    def update_one(self, authenticated_user, graphql_path, graphql_selection=None,
            _=None, **filters):
        # variable that contains new data
        data = _ or {}
        # retrieve the instance to update
        instance = self._read_one(
            graphql_selection = graphql_selection or {},
            authenticated_user = authenticated_user,
            **filters
        )
        # enforce permissions
        self.model_config.ensure_permission(
            operation = Operation.UPDATE,
            instance = instance,
            authenticated_user = authenticated_user,
            graphql_path = graphql_path,
            data = data,
        )
        # pre-update trigger
        self.model_config.on_before_operation(instance, authenticated_user, Operation.UPDATE, data)
        # related things
        related_data = {}
        for field_name in list(data.keys()):
            # foreign fields
            if field_name in self.fields_info.foreign:
                child_data = data.pop(field_name)
                # if child_data is null, the reference will be deleted
                if child_data is not None:
                    child_model_config = self.model_config.schema.get_model_config(
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
        # extract data for custom fields
        custom_fields_data = self._extract_custom_fields_data(
            operation = Operation.UPDATE,
            data = data)
        # custom fields definition
        self._update_custom_fields(
            instance = instance,
            authenticated_user = authenticated_user,
            data = custom_fields_data)
        # direct attributes
        for key, value in data.items():
            setattr(instance, key, value)
        # validation (raise an easy_graphql_server exception instead of a Django one)
        try:
            instance.clean()
        except django.core.exceptions.ValidationError as exception:
            reraise_django_validation_error(graphql_path, exception)
        # save instance
        instance.save()
        # related data
        for field_name, children_data in related_data.items():
            related_field = self.fields_info.related[field_name]
            child_model_config = self.model_config.schema.get_model_config(
                orm_model = related_field.orm_model)
            children_identifiers = []
            # create & update
            for child_index, child_data in enumerate(children_data):
                child_identifier = child_data.get(
                    child_model_config.orm_model_manager.fields_info.primary, None)
                # update only if identifier provided
                if child_identifier is not None:
                    child_instance = child_model_config.orm_model_manager.update_one(
                        authenticated_user = authenticated_user,
                        graphql_path = graphql_path + [field_name, child_index],
                        _ = child_data,
                        **{child_model_config.orm_model_manager.fields_info.primary:
                            child_identifier})
                    # store identifier
                    children_identifiers.append(child_identifier)
            # delete omitted children
            for child_instance in getattr(instance, field_name).all():
                if child_instance.pk not in children_identifiers:
                    child_instance.delete()
            # create
            for child_index, child_data in enumerate(children_data):
                child_identifier = child_data.get(
                    child_model_config.orm_model_manager.fields_info.primary, None)
                # create only if no identifier provided
                if child_identifier is None:
                    child_instance = child_model_config.orm_model_manager.create_one(
                        authenticated_user = authenticated_user,
                        graphql_path = graphql_path + [field_name, child_index],
                        **dict({related_field.value_field_name: instance.pk}, **child_data))
                    getattr(instance, field_name).add(child_instance)
        # validation (raise an easy_graphql_server exception instead of a Django one)
        try:
            instance.full_clean()
            if callable(getattr(instance, 'clean_related', None)):
                instance.clean_related()
        except django.core.exceptions.ValidationError as exception:
            reraise_django_validation_error(graphql_path, exception)
        # post-update trigger
        self.model_config.on_after_operation(instance, authenticated_user, Operation.UPDATE, data)
        # result
        if graphql_selection is None:
            return instance
        return self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            ensure_permission = True,
        )

    def delete_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        instance = self._read_one(
            graphql_selection = graphql_selection,
            authenticated_user = authenticated_user,
            **filters
        )
        self.model_config.ensure_permission(
            operation = Operation.DELETE,
            instance = instance,
            authenticated_user = authenticated_user,
            graphql_path = graphql_path,
        )
        # keep primary key for later result
        if self.fields_info.primary in graphql_selection:
            pre_result = {self.fields_info.primary: getattr(instance, self.fields_info.primary)}
        else:
            pre_result = {}
        # actually perform operations
        self.model_config.on_before_operation(instance, authenticated_user, Operation.DELETE)
        instance.delete()
        self.model_config.on_after_operation(instance, authenticated_user, Operation.DELETE)
        # compute & return result
        result = self._instance_to_dict(
            authenticated_user = authenticated_user,
            instance = instance,
            graphql_selection = graphql_selection,
            graphql_path = graphql_path,
            ensure_permission = False,
        )
        result.update(pre_result)
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

    def _read(self, graphql_selection, authenticated_user, **filters):
        # build queryset as intended by easy_graphql_server
        queryset = self.build_queryset(
            graphql_selection = graphql_selection,
            authenticated_user = authenticated_user
        ).filter(**filters)
        # filter queryset, depending on model config
        queryset = self.model_config.filter_for_user(
            queryset = queryset,
            authenticated_user = authenticated_user)
        # return resulting queryset
        return queryset

    def _read_one(self, graphql_selection, authenticated_user, **filters):
        try:
            return self._read(
                graphql_selection = graphql_selection,
                authenticated_user = authenticated_user,
                **filters
            ).get()
        except django.core.exceptions.ObjectDoesNotExist as error:
            raise exceptions.NotFoundError(filters) from error

    def _instance_to_dict(self, instance, authenticated_user, graphql_selection, graphql_path,
            ensure_permission=True):
        # pre-read trigger
        self.model_config.on_before_operation(instance, authenticated_user, Operation.READ)
        # enforce permissions when requested
        if ensure_permission:
            self.model_config.ensure_permission(
                operation = Operation.READ,
                instance = instance,
                authenticated_user = authenticated_user,
                graphql_path = graphql_path,
            )
        # build result: custom fields
        result = self._read_custom_fields(
            instance = instance,
            authenticated_user = authenticated_user,
            graphql_selection = graphql_selection)
        # build result: from instance attributes
        for field_name, graphql_subselection in graphql_selection.items():
            if field_name in result:
                continue
            field_value = getattr(instance, field_name)
            # field_value field
            if graphql_subselection is None:
                result[field_name] = field_value
            # related field
            elif type(field_value).__name__ == 'RelatedManager':
                children_instances = field_value.all()
                if len(children_instances) == 0:
                    result[field_name] = []
                else:
                    model_manager = self.model_config.schema.get_model_config(
                        orm_model=children_instances[0].__class__).orm_model_manager
                    result[field_name] = [
                        model_manager._instance_to_dict(
                            authenticated_user = authenticated_user,
                            instance = child_instance,
                            graphql_selection = graphql_subselection,
                            graphql_path = graphql_path + [field_name, child_index],
                            ensure_permission = False,
                        )
                        for child_index, child_instance
                        in enumerate(children_instances)
                    ]
            # foreign field
            elif field_value is not None:
                model_manager = self.model_config.schema.get_model_config(
                    orm_model=field_value.__class__).orm_model_manager
                # pylint: disable=protected-access
                result[field_name] = model_manager._instance_to_dict(
                    authenticated_user = authenticated_user,
                    instance = field_value,
                    graphql_selection = graphql_subselection,
                    graphql_path = graphql_path + [field_name],
                    ensure_permission = ensure_permission,
                )
        # post-read trigger
        self.model_config.on_after_operation(instance, authenticated_user, Operation.READ)
        return result

    def build_queryset(self, graphql_selection, authenticated_user):
        """
            Build queryset for given GraphQL selection
        """
        only, prefetch_related, select_related = (
            self.build_queryset_parts(
                graphql_selection = graphql_selection,
                authenticated_user = authenticated_user,
            )
        )
        base_queryset = self.model_config.filter_for_user(self.orm_model.objects, authenticated_user)
        if self.restrict_queried_fields:
            return (base_queryset
                .only(*only)
                .prefetch_related(*prefetch_related)
                .select_related(*select_related)
            )
        return (base_queryset
            .prefetch_related(*prefetch_related)
            .select_related(*select_related)
        )

    def build_queryset_parts(self, graphql_selection, authenticated_user,
            field_prefix=''):
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
        only = []
        prefetch_related = []
        select_related = []
        # browse fields in GraphQL selection
        for field_name, graphql_subselection in graphql_selection.items():
            # no subselection, this is a direct field
            if graphql_subselection is None and field_name not in self.fields_info.custom:
                only.append(field_prefix + field_name)
            # there is a subselection, and it is a foreign key
            elif field_name in self.fields_info.foreign:
                foreign_field = self.fields_info.foreign[field_name]
                only.append(field_prefix + foreign_field.value_field_name)
                select_related.append(field_prefix + field_name)
                foreign_orm_model_manager = schema.get_model_config(
                    orm_model = foreign_field.orm_model).orm_model_manager
                foreign_only, foreign_prefetch_related, foreign_select_related = (
                    foreign_orm_model_manager.build_queryset_parts(
                        graphql_selection = graphql_subselection,
                        authenticated_user = authenticated_user,
                        field_prefix = f'{field_prefix}{field_name}__'
                    )
                )
                only += foreign_only
                prefetch_related += foreign_prefetch_related
                select_related += foreign_select_related
            # there is a subselection, and it is a related field
            elif field_name in self.fields_info.related:
                related_field = self.fields_info.related[field_name]
                related_model_config = schema.get_model_config(
                    orm_model = related_field.orm_model)
                prefetch_related.append(
                    django.db.models.Prefetch(
                        field_name,
                        queryset = related_model_config.orm_model_manager.build_queryset(
                            graphql_selection = dict({related_field.value_field_name: None},
                                **graphql_subselection),
                            authenticated_user = authenticated_user,
                        )
                    )
                )
        # return resulting queryset
        return only, prefetch_related, select_related


    # Django field conversion to GraphQL type

    GRAPHQL_TYPES_MAPPING = {
        # boolean
        django.db.models.fields.BooleanField: graphql_types.Boolean,
        # integers
        django.db.models.fields.AutoField: graphql_types.Int,
        django.db.models.fields.IntegerField: graphql_types.Int,
        django.db.models.fields.BigIntegerField: graphql_types.Int,
        django.db.models.fields.SmallIntegerField: graphql_types.Int,
        # non-integer numbers
        django.db.models.fields.FloatField: graphql_types.Float,
        django.db.models.fields.DecimalField: graphql_types.Decimal,
        # texts
        django.db.models.fields.CharField: graphql_types.String,
        django.db.models.fields.TextField: graphql_types.String,
        django.db.models.fields.URLField: graphql_types.String,
        django.db.models.fields.EmailField: graphql_types.String,
        # date/time
        django.db.models.fields.DateField: graphql_types.Date,
        django.db.models.fields.DateTimeField: graphql_types.DateTime,
        django.db.models.fields.TimeField: graphql_types.Time,
        # other things
        django.db.models.fields.json.JSONField: graphql_types.JSONString,
    }

    def _to_graphql_type_from_field(self, field):
        """
            Convert Django ORM model fields to GraphQL type.
        """
        # enum
        if getattr(field, 'choices', None):
            graphql_type = conversion.to_graphql_enum_from_choices(
                prefix = f'{self.model_config.name}__{field.name}',
                choices = field.choices,
                schema = self.model_config.schema,
            )
        # scalar
        elif isinstance(field, tuple(self.GRAPHQL_TYPES_MAPPING)):
            graphql_type = self.GRAPHQL_TYPES_MAPPING[type(field)]
        # Postgres
        elif WITH_POSTGRES_SUPPORT:
            # array
            if isinstance(field, django.contrib.postgres.fields.array.ArrayField):
                graphql_type = graphql_types.List(
                    self._to_graphql_type_from_field(field.base_field))
        # unrecognized
        else:
            raise ValueError(f'Could not conversion {field} to graphql type')
        # result
        return graphql_type

    # SQL logging

    @staticmethod
    def start_sql_log():
        settings.DEBUG = True
        django.db.reset_queries()

    @staticmethod
    def get_sql_log():
        return [
            query['sql']
            for query in list(django.db.connection.queries)
        ]
