"""
    This module defines the `ModelConfig` class.
"""

from collections import defaultdict

from .operations import Operation
from .conversion import to_graphql_objecttype, to_graphql_argument
from .types import Required
from .orm import ORM
from .model_config_custom_field import ModelConfigCustomField
from . import exceptions, introspection, graphql_types
from .exposition import CustomField


class ModelConfig:

    """
        Configuration of an exposed model.

        Internally used within `Schema` class as a `Schema.models_configs` collection
        to store configuration for exposed models.
    """

    def __init__(self, schema, orm_model,
            name=None, plural_name=None, types_name=None,
            can_expose=True, cannot_expose=False,
            can_create=True, can_read=True, can_update=True, can_write=True, can_delete=True,
            cannot_create=False, cannot_update=False, cannot_read=False, cannot_write=False,
            cannot_delete=False,
            only_when_child_of=None, require_authenticated_user=False, restrict_queried_fields=False,
            has_permission=None, filter_for_user=None,
            on_before_operation=None, on_after_operation=None,
            custom_fields=None, max_depth=None, limit=-1):
        # pylint: disable=unused-argument # for callbacks

        # store raw options
        self.schema = schema
        if require_authenticated_user is False:
            self.require_authenticated_user = ()
        elif require_authenticated_user is True:
            self.require_authenticated_user = (Operation.CREATE, Operation.READ, Operation.UPDATE, Operation.DELETE)
        else:
            self.require_authenticated_user = require_authenticated_user
        self.only_when_child_of = only_when_child_of
        self.max_depth = max_depth
        self.limit = limit
        # callbacks
        callbacks_names = ('has_permission', 'filter_for_user', 'on_before_operation', 'on_after_operation')
        self.callbacks = defaultdict(list)
        for callback_name in callbacks_names:
            local_callback = locals().get(callback_name)
            if local_callback:
                self.callbacks[callback_name].append(local_callback)
            model_callback_name = f'egs_{callback_name}'
            model_callback = orm_model.__dict__.get(model_callback_name)
            if model_callback:
                if isinstance(model_callback, (staticmethod, classmethod)):
                    callback = getattr(orm_model, model_callback_name)
                    self.callbacks[callback_name].append(callback)
                else:
                    def make_callback(model_callback_name):
                        return (lambda instance, *args, **kwargs:
                            getattr(instance, model_callback_name)(*args, **kwargs))
                    self.callbacks[callback_name].append(
                        make_callback(model_callback_name))
        # custom fields
        self.custom_fields = []
        if custom_fields:
            for custom_field in custom_fields:
                if isinstance(custom_field, dict):
                    self._add_custom_field(**custom_field)
                elif issubclass(custom_field, CustomField):
                    introspection.validate_class_attributes_against_method_arguments(
                        cls = custom_field,
                        method = ModelConfigCustomField,
                        excluded_arguments = ('self', ))
                    attributes = introspection.get_public_class_attributes(custom_field)
                    self._add_custom_field(**attributes)
        # what methods are exposed
        self.available_operations = {
            Operation.READ: (can_read is not False and cannot_read is not True),
            Operation.CREATE: (can_write is not False and
                can_create is not False and cannot_create is not True),
            Operation.UPDATE: (can_write is not False and
                can_update is not False and cannot_update is not True),
            Operation.DELETE: (can_write is not False and
                can_delete is not False and cannot_delete is not True),
        }
        # what fields are exposed in which method
        self.concatenated_fields = {
            Operation.CREATE: self._concatenate_fields_options(
                (can_expose, can_write, can_create), True),
            Operation.READ: self._concatenate_fields_options(
                (can_expose, can_read,), True),
            Operation.UPDATE: self._concatenate_fields_options(
                (can_expose, can_write, can_update), True),
        }
        self.concatenated_exclude = {
            Operation.CREATE: self._concatenate_fields_options(
                (cannot_expose, cannot_write, cannot_create), False),
            Operation.READ: self._concatenate_fields_options(
                (cannot_expose, cannot_read,), False),
            Operation.UPDATE: self._concatenate_fields_options(
                (cannot_expose, cannot_write, cannot_update), False),
        }
        # instanciate ORM model manager
        self.orm_model_manager = ORM.get_manager(
            orm_model = orm_model,
            model_config = self,
            restrict_queried_fields = restrict_queried_fields,
        )
        # name
        self.name = name or schema.case_manager.convert(self.orm_model_manager.get_table_name())
        self.types_name = types_name or self.name
        self.plural_name = plural_name or f'{self.name}s'

    def expose_methods(self):
        """
            Called from `Schema` just before generating actual GraphQL schema.
            Exposes methods to read, write, create, and update model instances.

            Only allowed methods will be exposed.
        """
        # do not expose if explicitely forbidden
        if self.only_when_child_of:
            return
        # available filters for querying
        filters = self.orm_model_manager.get_filters()
        # this is the common output format for all methods
        output_type = to_graphql_objecttype(
            type_ = self.get_type_mapping(Operation.READ, require_non_nullable=True),
            prefix = self.types_name,
            schema = self.schema,
        )
        # expose create method
        if self.available_operations[Operation.CREATE]:
            # create one instance
            self.schema.expose_mutation(
                name = f'create_{self.name}',
                input_format = to_graphql_argument(
                    type_ = self.get_type_mapping(Operation.CREATE),
                    prefix = f'create_{self.name}',
                    schema = self.schema,
                ),
                output_format = output_type,
                method = self.orm_model_manager.decorate(
                    self.orm_model_manager.create_one),
                pass_graphql_path = True,
                pass_graphql_selection = True,
                pass_authenticated_user = True,
                require_authenticated_user = Operation.CREATE in self.require_authenticated_user,
            )
        # expose read methods
        if self.available_operations[Operation.READ]:
            # fetch one instance
            self.schema.expose_query(
                name = self.name,
                input_format = self.orm_model_manager.fields_info.unique,
                output_format = output_type,
                method = self.orm_model_manager.decorate(
                    self.orm_model_manager.read_one),
                pass_graphql_path = True,
                pass_graphql_selection = True,
                pass_authenticated_user = True,
                require_authenticated_user = Operation.READ in self.require_authenticated_user,
            )
            # fetch many instances
            self.schema.expose_query(
                name = self.plural_name,
                input_format = filters,
                output_format = [output_type],
                method = self.orm_model_manager.decorate(
                    self.orm_model_manager.read_many),
                pass_graphql_path = True,
                pass_graphql_selection = True,
                pass_authenticated_user = True,
                require_authenticated_user = Operation.READ in self.require_authenticated_user,
            )
        # expose UPDATE method
        if self.available_operations[Operation.UPDATE]:
            # update one instance
            self.schema.expose_mutation(
                name = f'update_{self.name}',
                input_format = to_graphql_argument(
                    type_ = dict(
                        {'_': self.get_type_mapping(Operation.UPDATE)},
                        ** self.orm_model_manager.fields_info.unique),
                    prefix = f'update_{self.name}',
                    schema = self.schema,
                ),
                output_format = output_type,
                method = self.orm_model_manager.decorate(
                    self.orm_model_manager.update_one),
                pass_graphql_path = True,
                pass_graphql_selection = True,
                pass_authenticated_user = True,
                require_authenticated_user = Operation.UPDATE in self.require_authenticated_user,
            )
        # expose delete method
        if self.available_operations[Operation.DELETE]:
            # delete one instance
            self.schema.expose_mutation(
                name = f'delete_{self.name}',
                input_format = self.orm_model_manager.fields_info.unique,
                output_format = output_type,
                method = self.orm_model_manager.decorate(
                    self.orm_model_manager.delete_one),
                pass_graphql_path = True,
                pass_graphql_selection = True,
                pass_authenticated_user = True,
                require_authenticated_user = Operation.DELETE in self.require_authenticated_user,
            )

    # concatenate

    @staticmethod
    def _concatenate_fields_options(options, continue_if):
        concatenated = set()
        for option in options:
            # if option is a boolean
            if option is continue_if:
                continue
            if option is (not continue_if):
                return None
            # if option is an iterator
            if concatenated is None:
                concatenated = set(option)
            else:
                concatenated |= set(option)
        return tuple(concatenated) if concatenated else None

    # types computation

    def get_type_mapping(self, operation=None, exclude=None, depth=0, linked_field=None,
            with_custom_fields=True, max_depth=None, require_non_nullable=False):
        """
            Return a `dict` from `str` to GraphQL types, corresponding to the model.

            Using recursion, it allows nesting, in a way that we never go through a given foreign
            key twice.
        """
        fields_info = self.orm_model_manager.fields_info
        exclude = exclude or set()
        mapping = {}
        # check depth
        if self.max_depth is not None and (max_depth is None or self.max_depth < max_depth):
            max_depth = self.max_depth
        # no mapping for deletion
        if operation == Operation.DELETE:
            return {}
        # value fields
        for field_name, graphql_type in fields_info.value.items():
            # primary fields mustn't be exposed for creation & update, unless nested
            if operation in (Operation.CREATE, Operation.UPDATE):
                if depth == 0 and field_name == fields_info.primary:
                    continue
            # ensure the field is exposed for this operation
            if operation is not None and not self.can_perform(operation, field_name):
                continue
            # map
            mapping[field_name] = graphql_type
        # foreign & related fields...
        if max_depth is None or max_depth > 0:
            for field_name, field in fields_info.linked.items():
                # ensure the field is exposed for this operation
                if operation is not None and not self.can_perform(operation, field_name):
                    continue
                # retrieve other model config
                other_model_config = self.schema.get_model_config(orm_model=field.orm_model)
                if other_model_config is None:
                    continue
                # only_when_child_of is important
                if other_model_config.only_when_child_of and not issubclass(
                        self.orm_model_manager.orm_model, other_model_config.only_when_child_of):
                    continue
                # these fields are at stake, and will be later excluded
                _exclude = {(self, field_name), (other_model_config, field.field_name)}
                if exclude & _exclude:
                    continue
                # ...with recursion
                mapping[field_name] = other_model_config.get_type_mapping(
                    operation = operation,
                    exclude = exclude | _exclude,
                    depth = depth + 1,
                    max_depth = (max_depth - 1) if max_depth is not None else None,
                    linked_field = field,
                    with_custom_fields = with_custom_fields,
                    require_non_nullable = require_non_nullable)
                # related are presented as collections
                if field_name in fields_info.related:
                    if require_non_nullable:
                        mapping[field_name] = Required([Required(mapping[field_name])])
                    else:
                        mapping[field_name] = [mapping[field_name]]
        # apply non null when necessary
        if operation == Operation.CREATE:
            for field_name, graphql_type in list(mapping.items()):
                if field_name in fields_info.mandatory:
                    if linked_field is not None and field_name == linked_field.value_field_name:
                        continue
                    mapping[field_name] = self._make_required(graphql_type)
        if require_non_nullable:
            for field_name, graphql_type in list(mapping.items()):
                if field_name not in fields_info.nullable:
                    mapping[field_name] = self._make_required(graphql_type)
        # custom fields
        if with_custom_fields:
            for custom_field in self.custom_fields:
                if operation is None or custom_field.can_perfom(operation):
                    mapping[custom_field.name] = custom_field.format
        # result
        return mapping

    # required

    @classmethod
    def _make_required(cls, graphql_type):
        if isinstance(graphql_type, (graphql_types.NonNull, Required)):
            return graphql_type
        if isinstance(graphql_type, graphql_types.List):
            return graphql_types.NonNull(graphql_types.List(graphql_types.NonNull(graphql_type.of_type)))
        if isinstance(graphql_type, list):
            return Required([Required(graphql_type[0])])
        return Required(graphql_type)

    # callbacks

    def _call(self, callback_name, *args, **kwargs):
        for method in self.callbacks[callback_name]:
            yield method(*args, **kwargs)

    # authorizations

    def can_perform(self, operation, field_name):
        """
            Check if a given `Operation` can be performed on a given field, given its `str` name.

            Of course, this does not make sense for `Operation.DELETE`, which raises an exception.
        """
        # deletion doesn't apply to one field
        if operation == Operation.DELETE:
            raise ValueError(
                'Model.can_perform can only be called with `operation != Operation.DELETE`')
        # cannot if not in explicitely exposed fields
        if self.concatenated_fields[operation]:
            if field_name not in self.concatenated_fields[operation]:
                return False
        # cannot if in explicitely forbidden fields
        if self.concatenated_exclude[operation]:
            if field_name in self.concatenated_exclude[operation]:
                return False
        # otherwise, it works
        return True

    def can_expose_from_parent(self, orm_model):
        """
            Check if the present ORM model can be exposed when nested under another model.

            This is useful when a model cannot be exposed as a standalone, but only
            nested under some other model.
        """
        if not self.only_when_child_of:
            return True
        return issubclass(orm_model, self.only_when_child_of)

    def filter_for_user(self, queryset, authenticated_user):
        """
            Returns a Django `Queryset`, which is a filtered version of the input `queryset`
            only showing what is available to the `authenticated_user`.
        """
        for filter_for_user_method in self.callbacks['filter_for_user']:
            queryset = filter_for_user_method(queryset, authenticated_user)
        return queryset

    def has_permission(self, instance, authenticated_user, operation, data=None):
        """
            Return a boolean indicating whether or not the requested operation can
            be performed on the instance.

            `data` is provided when the operation is either `Operation.CREATE` or
            `Operation.UPDATE`. It is a dictionary containing the new provided data
            for the instance.
        """
        if data is None:
            data = {}
        return all(self._call('has_permission', instance, authenticated_user, operation, data))

    def ensure_permission(self, instance, authenticated_user, operation,
            data=None, graphql_path=None):
        """
            Raise an `exceptions.ForbiddenError` when `has_permission()` returns
            `False` with the same parameters, aka when the requested operation cannot
            be performed on the instance.

            `data` is provided when the operation is either `Operation.CREATE` or
            `Operation.UPDATE`. It is a dictionary containing the new provided data
            for the instance.

            The `graphql_path` parameter indicates where the permission was denied.
        """
        if data is None:
            data = {}
        if not self.has_permission(instance, authenticated_user, operation, data):
            raise exceptions.ForbiddenError(
                operation = operation,
                authenticated_user = authenticated_user,
                path = graphql_path,
            )

    # triggers

    def on_before_operation(self, instance, authenticated_user, operation, data=None, depth=0):
        """
            Execute pre-trigger(s) for given instance with given parameters.
        """
        if not isinstance(instance, self.orm_model_manager.orm_model):
            raise Exception(f'Unexpected instance {instance}, should be of type {self.orm_model_manager.orm_model}')
        return list(self._call('on_before_operation', instance, authenticated_user, operation, data, depth))

    def on_after_operation(self, instance, authenticated_user, operation, data=None, depth=0):
        """
            Execute post-trigger(s) for given instance with given parameters.
        """
        if not isinstance(instance, self.orm_model_manager.orm_model):
            raise Exception(f'Unexpected instance {instance}, should be of type {self.orm_model_manager.orm_model}')
        return list(self._call('on_after_operation', instance, authenticated_user, operation, data, depth))

    # custom field

    def _add_custom_field(self, *args, **kwargs):
        custom_field = ModelConfigCustomField(*args, **kwargs)
        self.custom_fields.append(custom_field)
