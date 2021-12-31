"""
    This module defines the `ModelConfig` class.
"""

from .operations import Operation
from .convert import to_graphql_objecttype, to_graphql_argument
from .types import List
from .orm import ORM


class ModelConfig:

    """
        Configuration of an exposed model.

        Internally used within `Schema` class as a `Schema.models_configs` collection
        to store configuration for exposed models.
    """

    # pylint: disable=R0913 # Too many arguments
    def __init__(self, schema, orm_model, name=None, plural_name=None,
            can_create=True, can_read=True, can_update=True, can_write=True, can_delete=True,
            cannot_create=False, cannot_update=False, cannot_read=False, cannot_write=False,
            cannot_delete=False,
            only_when_child_of=None):
        # store raw options
        self.schema = schema
        self.only_when_child_of = only_when_child_of
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
                (can_write, can_create), True),
            Operation.READ: self._concatenate_fields_options(
                (can_read,), True),
            Operation.UPDATE: self._concatenate_fields_options(
                (can_write, can_update), True),
        }
        self.concatenated_exclude = {
            Operation.CREATE: self._concatenate_fields_options(
                (cannot_write, cannot_create), False),
            Operation.READ: self._concatenate_fields_options(
                (cannot_read,), False),
            Operation.UPDATE: self._concatenate_fields_options(
                (cannot_write, cannot_update), False),
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
        # available filters for querying
        filters = self.orm_model_manager.get_filters()
        # this is the common output format for all methods
        output_type = self._get_type(
            operation = Operation.READ,
            prefix = self.name,
        )
        # expose read methods
        if self.available_operations[Operation.READ]:
            # fetch one instance
            self.schema.expose_query(
                name = self.name,
                input_format = self.orm_model_manager.fields_info.unique,
                output_format = output_type,
                method = self.orm_model_manager.read_one,
                pass_graphql_selection = True,
            )
            # fetch many instances
            self.schema.expose_query(
                name = self.plural_name,
                input_format = filters,
                output_format = List(output_type),
                method = self.orm_model_manager.read_many,
                pass_graphql_selection = True,
            )
        # expose delete method
        if self.available_operations[Operation.DELETE]:
            # delete one instance
            self.schema.expose_mutation(
                name = f'delete_{self.name}',
                input_format = self.orm_model_manager.fields_info.unique,
                output_format = output_type,
                method = self.orm_model_manager.delete_one,
                pass_graphql_selection = True,
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

    def get_type_mapping(self, operation, exclude=None):
        """
            Return a `dict` from `str` to GraphQL types, corresponding to the model.

            Using recursion, it allows nesting, in a way that we never go through a given foreign
            key twice.
        """
        fields_info = self.orm_model_manager.fields_info
        exclude = exclude or set()
        mapping = {}
        # value fields
        for field_name, graphql_type in fields_info.value.items():
            mapping[field_name] = graphql_type
        # foreign & related fields...
        for field_name, field in (fields_info.foreign | fields_info.related).items():
            # ensure the field is exposed for this operation
            if operation != Operation.DELETE and not self.can_perform(operation, field_name):
                continue
            # retrieve other model
            other_model = self.schema.get_model_config_from_orm_model(field.orm_model)
            if other_model is None:
                continue
            # these fields are at stake, and will be later excluded
            _exclude = {(self, field_name), (other_model, field.field_name)}
            if exclude & _exclude:
                continue
            # ...with recursion
            mapping[field_name] = other_model.get_type_mapping(
                operation = operation,
                exclude = exclude | _exclude,
            )
            # related are presented as collections
            if field_name in fields_info.related:
                mapping[field_name] = [mapping[field_name]]
        # result
        return mapping

    def _get_type(self, operation, prefix):
        return to_graphql_objecttype(
            type_ = self.get_type_mapping(operation),
            prefix = prefix,
        )

    def _get_argument(self, operation, prefix):
        return to_graphql_argument(
            type_ = self.get_type_mapping(operation),
            prefix = prefix,
        )

    # authorizations

    def can_perform(self, operation, field_name):
        """
            Check if a given `Operation` can be performed on a given field, given its `str` name.

            Of course, this does not make sense for `Operation.DELETE`, which raises an exception.
        """
        if operation == Operation.DELETE:
            raise ValueError(
                'Model.can_perform can only be called with `operation != Operation.DELETE`')
        if self.concatenated_fields[operation]:
            if field_name not in self.concatenated_fields[operation]:
                return False
        if self.concatenated_exclude[operation]:
            if field_name in self.concatenated_exclude[operation]:
                return False
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
