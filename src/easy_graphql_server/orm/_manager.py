"""
    Definition of `ModelManager` base class.
"""

from .. import graphql_types
from ..operations import Operation
from ._lookups import LOOKUPS

import graphql.type.definition


class ModelManager:
    """
        Base class for `DjangoModelManager`, `SqlAlchemyModelManager`, `PeeweeModelManager`

        Cannot be used as is, this is an abstract class that must be inherited.
    """

    def __init__(self, orm_model, model_config, restrict_queried_fields):
        self.orm_model = orm_model
        self.model_config = model_config
        self.restrict_queried_fields = restrict_queried_fields
        self.fields_info = self.get_fields_info()
        self.fields_info.compute_linked()
        for custom_field in self.model_config.custom_fields:
            self.fields_info.custom.add(custom_field.name)

    # metadata extraction

    def get_fields_info(self):
        """
            Retrieve fields info for the given ORM model.
        """
        raise NotImplementedError()

    def get_filters(self, mapping=None, prefix=''):
        """
            Retrieve available filters for the given ORM model.

            Needs corresponding `easy_graphql_server.ModelConfig` to be properly initialize, aka.,
            just before GraphQL schema is built.
        """
        filters = {}
        # base mapping
        if mapping is None:
            mapping = self.model_config.get_type_mapping(
                operation = Operation.READ,
                with_custom_fields = False)
        # browse all fields
        for field_name, graphql_type in mapping.items():
            prefixed_field_name = f'{prefix}{field_name}'
            # foreign & related field
            if isinstance(graphql_type, (dict, list)):
                submapping = graphql_type[0] if isinstance(graphql_type, list) else graphql_type
                filters.update(self.get_filters(submapping, f'{prefixed_field_name}__'))
            # value field
            elif graphql_type in LOOKUPS:
                # basic filter (equality)
                filters[prefixed_field_name] = graphql_type
                # browse & add available lookups
                for lookup_name, lookup_graphql_type in LOOKUPS.get(graphql_type, {}).items():
                    filters[f'{prefixed_field_name}__{lookup_name}'] = lookup_graphql_type
                    # apply same filters as for integers on date/time parts
                    date_time_types = (
                        graphql_types.Date, graphql_types.DateTime, graphql_types.Time)
                    if graphql_type in date_time_types and lookup_graphql_type == graphql_types.Int:
                        int_lookups = LOOKUPS[graphql_types.Int]
                        for int_lookup_name, int_lookup_graphql_type in int_lookups.items():
                            name = f'{prefixed_field_name}__{lookup_name}__{int_lookup_name}'
                            filters[name] = int_lookup_graphql_type
            elif isinstance(graphql_type, graphql.type.definition.GraphQLEnumType):
                filters[prefixed_field_name] = graphql_type
                filters[f'{prefixed_field_name}__in'] = graphql_types.List(graphql_type)
                filters[f'{prefixed_field_name}__isnull'] = graphql_types.Boolean
        # result
        return filters

    # CRUD operations on ORM model instances

    def create_one(self, authenticated_user, graphql_path, graphql_selection, **data):
        """
            Create one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def read_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        """
            Read one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def read_many(self, authenticated_user, graphql_path, graphql_selection, **filters):
        """
            Read many instance of the given ORM model.

            Result is a `list` of `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def update_one(self, authenticated_user, graphql_path, graphql_selection, _=None, **filters):
        """
            Update one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def delete_one(self, authenticated_user, graphql_path, graphql_selection, **filters):
        """
            Delete one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    #

    def _extract_custom_fields_data(self, operation, data):
        result = {}
        for custom_field in self.model_config.custom_fields:
            if custom_field.name in data and custom_field.can_perfom(operation):
                result[custom_field.name] = data.pop(custom_field.name)
        return result

    def _create_custom_fields(self, instance, authenticated_user, data):
        for custom_field in self.model_config.custom_fields:
            if custom_field.name in data:
                custom_field.perform_one_creation(
                    instance = instance,
                    authenticated_user = authenticated_user,
                    value = data[custom_field.name])

    def _update_custom_fields(self, instance, authenticated_user, data):
        for custom_field in self.model_config.custom_fields:
            if custom_field.name in data:
                custom_field.perform_one_update(
                    instance = instance,
                    authenticated_user = authenticated_user,
                    value = data[custom_field.name])

    def _read_custom_fields(self, instance, authenticated_user, graphql_selection):
        result = {}
        for custom_field in self.model_config.custom_fields:
            if custom_field.name in graphql_selection and custom_field.can_perfom(Operation.READ):
                result[custom_field.name] = custom_field.perform_one_read(
                    instance = instance,
                    authenticated_user = authenticated_user,
                    graphql_selection = graphql_selection)
        return result

    # methods should be executed within an atomic database transaction

    @staticmethod
    def decorate(method):
        """
            Decorator to execute a given method within a transaction, using
            the corresponding ORM.
        """
        raise NotImplementedError()

    # SQL logging

    @staticmethod
    def start_sql_log():
        """
            Clear ORM-level SQL log
        """
        raise NotImplementedError()

    @staticmethod
    def get_sql_log():
        """
            Get a log of SQL queries executed by the ORM in the form of a `list[str]`
        """
        raise NotImplementedError()
