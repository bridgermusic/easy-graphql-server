"""
    This module defines the `ModelConfig` class.
"""

from .operations import Operation
from .convert import to_graphql_objecttype, to_graphql_argument
from .types import Mandatory
from .orm import ORM
from . import exceptions


class ModelConfig:

    """
        Configuration of an exposed model.

        Internally used within `Schema` class as a `Schema.models_configs` collection
        to store configuration for exposed models.
    """

    # pylint: disable=R0913 # Too many arguments
    def __init__(self, schema, orm_model, name=None, plural_name=None,
            can_expose=True, cannot_expose=False,
            can_create=True, can_read=True, can_update=True, can_write=True, can_delete=True,
            cannot_create=False, cannot_update=False, cannot_read=False, cannot_write=False,
            cannot_delete=False,
            only_when_child_of=None, force_authenticated_user=False,
            ensure_permissions=None):
        # store raw options
        self.schema = schema
        self.force_authenticated_user = force_authenticated_user
        self.only_when_child_of = only_when_child_of
        self.ensure_permissions = ensure_permissions
        # name
        self.name = name or schema.case_manager.convert(orm_model.__name__)
        self.plural_name = plural_name or f'{self.name}s'
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
            model_config = self)

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
            type_ = self.get_type_mapping(Operation.READ),
            prefix = self.name,
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
                force_authenticated_user = self.force_authenticated_user,
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
                force_authenticated_user = self.force_authenticated_user,
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
                force_authenticated_user = self.force_authenticated_user,
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
                force_authenticated_user = self.force_authenticated_user,
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
                force_authenticated_user = self.force_authenticated_user,
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

    def get_type_mapping(self, operation, exclude=None, depth=0, linked_field=None):
        """
            Return a `dict` from `str` to GraphQL types, corresponding to the model.

            Using recursion, it allows nesting, in a way that we never go through a given foreign
            key twice.
        """
        fields_info = self.orm_model_manager.fields_info
        exclude = exclude or set()
        mapping = {}
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
            if not self.can_perform(operation, field_name):
                continue
            # map
            mapping[field_name] = graphql_type
        # foreign & related fields...
        for field_name, field in fields_info.linked.items():
            # ensure the field is exposed for this operation
            if not self.can_perform(operation, field_name):
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
                linked_field = field,
            )
            # related are presented as collections
            if field_name in fields_info.related:
                mapping[field_name] = [mapping[field_name]]
        # apply non null when necessary
        if operation == Operation.CREATE:
            for field_name, graphql_type in list(mapping.items()):
                if field_name in fields_info.mandatory:
                    if linked_field is not None and field_name == linked_field.value_field_name:
                        continue
                    mapping[field_name] = Mandatory(graphql_type)
        # result
        return mapping

    def _get_argument(self, operation, prefix):
        return to_graphql_argument(
            type_ = self.get_type_mapping(operation),
            prefix = prefix,
            schema = self.schema,
        )

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

    def check_permissions(self, operation, instance, authenticated_user=None, data=None):
        """
            Returns a `bool` indicating whether or not the requested operation can
            be performed on the instance.

            `data` is provided when the operation is either `Operation.CREATE` or
            `Operation.UPDATE`. It is a dictionary containing the new provided data
            for the instance.
        """
        if hasattr(instance, 'ensure_permissions'):
            if not instance.ensure_permissions(authenticated_user, operation, data):
                return False
        if self.ensure_permissions:
            if not self.ensure_permissions(instance, authenticated_user, operation, data):
                return False
        return True

    def enforce_permissions(self, operation, instance, authenticated_user,
            data=None, graphql_path=None):
        """
            Raise an `exceptions.ForbiddenError` when `check_permissions()` returns
            `False` with the same parameters.

            The `graphql_path` parameter indicates where the permission was denied.
        """
        permitted = self.check_permissions(
            operation = operation,
            instance = instance,
            authenticated_user = authenticated_user,
            data = data)
        if not permitted:
            raise exceptions.ForbiddenError(
                operation = operation,
                authenticated_user = authenticated_user,
                path = graphql_path,
            )
