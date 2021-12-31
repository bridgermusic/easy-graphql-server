"""
    Definition of `Manager` base class.
"""

from .. import types
from ..operations import Operation
from ._lookups import LOOKUPS


class Manager:
    """
        Base class for `DjangoManager`, `SqlAlchemyManager`, `PeeweeManager`

        Cannot be used as is, this is an abstract class that must be inherited.
    """

    def __init__(self, orm_model, model_config):
        self.orm_model = orm_model
        self.model_config = model_config
        self.fields_info = self.get_fields_info()

    # metadata extraction

    def get_fields_info(self):
        """
            Retrieve fields info for the given ORM model.
        """
        raise NotImplementedError()

    def get_filters(self, mapping=None, prefix=''):
        """
            Retrieve available filters for the given ORM model.

            Needs corresponding `easy_graphql.ModelConfig` to be properly initialize, aka.,
            just before GraphQL schema is built.
        """
        filters = {}
        # base mapping
        if mapping is None:
            mapping = self.model_config.get_type_mapping(Operation.READ)
        # browse all fields
        for field_name, graphql_type in mapping.items():
            prefixed_field_name = f'{prefix}{field_name}'
            # foreign & related field
            if isinstance(graphql_type, (dict, list)):
                mapping = graphql_type[0] if isinstance(graphql_type, list) else graphql_type
                filters.update(self.get_filters(mapping, f'{prefixed_field_name}__'))
            # value field
            elif graphql_type in LOOKUPS:
                # basic filter (equality)
                filters[prefixed_field_name] = graphql_type
                # browse & add available lookups
                for lookup_name, lookup_graphql_type in LOOKUPS.get(graphql_type, {}).items():
                    filters[f'{prefixed_field_name}__{lookup_name}'] = lookup_graphql_type
                    # apply same filters as for integers on date/time parts
                    if (graphql_type in (types.Date, types.DateTime, types.Time)
                            and lookup_graphql_type == types.Int):
                        int_lookups = LOOKUPS[types.Int]
                        for int_lookup_name, int_lookup_graphql_type in int_lookups.items():
                            name = f'{prefixed_field_name}__{lookup_name}__{int_lookup_name}'
                            filters[name] = int_lookup_graphql_type
        # result
        return filters

    # CRUD operations on ORM model instances

    def create_one(self, graphql_selection, **data):
        """
            Create one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def read_one(self, graphql_selection, **filters):
        """
            Read one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def read_many(self, graphql_selection, **filters):
        """
            Read many instance of the given ORM model.

            Result is a `list` of `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def update_one(self, graphql_selection, _=None, **filters):
        """
            Update one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()

    def delete_one(self, graphql_selection, **filters):
        """
            Delete one instance of the given ORM model.

            Result is a `dict`, corresponding to the format given by `graphql_selection`.
        """
        raise NotImplementedError()
