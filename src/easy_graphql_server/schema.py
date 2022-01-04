"""
    `Schema` class is defined here. This is the root class that will be used as
    a central point to the easy_graphql_server API.
"""


import json
from collections import defaultdict

from graphql import GraphQLSchema, GraphQLField, GraphQLObjectType
# Had to disable pylint below, because "No name '...' in module '...'" and "Unable to import '...'"
from graphql.type.validate import validate_schema # pylint: disable=E0611,E0401
from graphql.utilities import get_introspection_query # pylint: disable=E0611,E0401
from graphql.graphql import graphql_sync

from . import exceptions
from .convert import to_graphql_type, to_graphql_argument
from .model_config import ModelConfig
from .casing import Casing


class Schema:

    """
        Base class for easy_graphql_server API.

        Mutation methods can be exposed with `Schema.expose_mutation()`.

        Query methods can be exposed with `Schema.expose_query()`.

        ORM model can be exposed with `Schema.expose_model()`.

        Schema can be validated using `Schema.check()`.
    """

    # public methods

    def __init__(self, casing=Casing.SNAKE):
        self.methods = defaultdict(dict)
        self.dirty = True
        self.graphql_schema = None
        self.models_configs = []
        self.case_manager = casing.value

    def get_documentation(self, with_descriptions=False):
        """
            Return GraphQL schema description in JSON format.
        """
        result = self.execute(get_introspection_query(descriptions=with_descriptions))
        return json.dumps(result.data, indent=2)

    def expose_query(self, **options):
        """
            Expose a query method in the schema.

            See `_expose_method` for more info about options.
        """
        self._expose_method(type_='query', **options)

    def expose_mutation(self, **options):
        """
            Expose a mutation method in the schema.

            See `_expose_method` for more info about options.
        """
        self._expose_method(type_='mutation', **options)

    def expose_model(self, orm_model, **options):
        """
            Expose an ORM model in the schema.

            See `ModelConfig` class constructor for more info about options.
        """
        self.dirty = True
        model_config = ModelConfig(orm_model=orm_model, schema=self, **options)
        self.models_configs.append(model_config)

    def execute(self, source, variables=None, serializable_output=False):
        """
            Execute a GraphQL query within the schema.
        """
        result = graphql_sync(
            schema = self._get_graphql_schema(),
            source = source,
            variable_values = variables or {},
        )
        if serializable_output:
            return result.formatted
        return result

    def check(self, graphql_schema=None):
        """
            Check the schema's validity; an exception is raised if something is wrong.
        """
        if graphql_schema is None:
            graphql_schema = self._get_graphql_schema()
        for error in validate_schema(graphql_schema):
            raise error
        self.dirty = False

    def get_model_config_from_orm_model(self, orm_model):
        """
            Retrieve an instance of `ModelConfig` if the passed `orm_model` has been
            exposed, `None` otherwise.
        """
        for model_config in self.models_configs:
            if model_config.orm_model_manager.orm_model == orm_model:
                return model_config
        return None

    # private methods

    def _expose_method(self, type_, name, input_format, output_format, method, # pylint: disable=R0913 # Too many arguments
            pass_graphql_selection=False, pass_graphql_path=False):
        self.dirty = True
        # pylint: disable=E1123 # Unexpected keyword argument 'resolve' in constructor call
        self.methods[type_][name] = GraphQLField(
            type_ = to_graphql_type(
                type_ = output_format,
                prefix = name,
                for_input = False,
            ),
            args = to_graphql_argument(
                type_ = input_format,
                prefix = name,
            ),
            resolve = self._make_callback(
                type_ = type_,
                method = method,
                pass_graphql_selection = (
                    'graphql_selection'
                    if pass_graphql_selection is True else
                    pass_graphql_selection
                ),
                pass_graphql_path = (
                    'graphql_path'
                    if pass_graphql_path is True else
                    pass_graphql_path
                )
            ),
        )

    def _get_graphql_schema(self):
        if self.dirty:
            for model_config in self.models_configs:
                model_config.expose_methods()
            self.graphql_schema = GraphQLSchema(
                query = GraphQLObjectType('Query',
                    lambda: self.methods['query']) if self.methods['query'] else None,
                mutation = GraphQLObjectType('Mutation',
                    lambda: self.methods['mutation']) if self.methods['query'] else None,
            )
            self.check(self.graphql_schema)
            self.dirty = False
        return self.graphql_schema

    def _make_callback(self, type_, method, pass_graphql_selection, pass_graphql_path):
        def callback(source, info, **kwargs): # pylint: disable=W0613 # Unused argument 'source'
            try:
                if pass_graphql_selection:
                    kwargs[pass_graphql_selection] = self._get_graphql_selection(
                        info.field_nodes[0].selection_set)
                if pass_graphql_path:
                    kwargs[pass_graphql_path] = [type_, info.path.key]
                return method(**kwargs)
            except exceptions.BaseError:
                raise
            except Exception as error:
                traceback = getattr(error, '__traceback__')
                print('\n\n' + 80 * '*' + '\n*')
                print(f'* {type(error).__qualname__}')
                print('*')
                for arg in error.args:
                    print(f'* {arg}')
                print('*')
                while traceback:
                    # pylint: disable=E1101 # Class 'tb_frame' has no 'f_code' member
                    print(f'*  {traceback.tb_frame.f_code.co_filename}:{traceback.tb_lineno}')
                    traceback = traceback.tb_next
                print('*\n' + 80 * '*' + '\n')
                raise Exception(
                    f'{type(error).__name__}: '
                    + '; '.join(map(str, error.args or []))
                ) from error
        return callback

    @classmethod
    def _get_graphql_selection(cls, selection_set):
        """
            Return the GraphQL selection as a mapping.

            For example, with this query...

            ```gql
            query {
                houses {
                    location
                    tenants {
                        first_name
                        last_name
                    }
                }
            }
            ```

            ...the resulting mapping would be:

            ```python
            {
                'location': None,
                'tenants': {
                    'first_name': None,
                    'last_name': None,
                }
            }
            ```
        """
        return {
            selection.name.value: (
                cls._get_graphql_selection(selection.selection_set)
                if selection.selection_set else None)
            for selection in selection_set.selections
        }
