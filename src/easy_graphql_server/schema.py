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
from .context import ContextValue


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
        result = self.execute(
            get_introspection_query(descriptions=with_descriptions))
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

    def execute(self, source, variables=None, operation_name=None, # pylint: disable=R0913 # Too many arguments
            authenticated_user=None,
            serializable_output=False):
        """
            Execute a GraphQL query within the schema.
        """
        result = graphql_sync(
            schema = self._get_graphql_schema(),
            source = source,
            variable_values = variables or {},
            operation_name = operation_name,
            context_value = ContextValue(
                authenticated_user = authenticated_user,
            ),
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

    def as_django_view(self):
        """
            Expose schema as a django view.

            Example:

            ```python
            from django.urls import path
            import easy_graphql_server

            schema = easy_graphql_server.Schema()

            urlpatterns = [
                path('graphql', schema.as_django_view()),
            ]
            ```
        """
        return self._django_view

    # private methods

    def _expose_method(self, type_, name, method, input_format=None, output_format=None, # pylint: disable=R0913 # Too many arguments
            pass_graphql_selection=False, pass_graphql_path=False,
            pass_authenticated_user=False, force_authenticated_user=False):
        # pylint: disable=E1123 # Unexpected keyword argument 'resolve' in constructor call
        self.methods[type_][name] = GraphQLField(
            # output format
            type_ = to_graphql_type(
                type_ = output_format,
                prefix = name,
                for_input = False,
            ) if output_format else None,
            # input format
            args = to_graphql_argument(
                type_ = input_format,
                prefix = name,
            ) if input_format else None,
            # resolve method
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
                ),
                pass_authenticated_user = (
                    'authenticated_user'
                    if pass_authenticated_user is True else
                    pass_authenticated_user
                ),
                force_authenticated_user = force_authenticated_user,
            ),
        )
        # schema is not up to date anymore
        self.dirty = True

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

    def _make_callback(self, type_, method, # pylint: disable=R0913 # Too many arguments
            pass_graphql_selection, pass_graphql_path,
            pass_authenticated_user, force_authenticated_user):
        def callback(source, info, **kwargs): # pylint: disable=W0613 # Unused argument 'source'
            try:
                if pass_graphql_selection:
                    kwargs[pass_graphql_selection] = self._get_graphql_selection(
                        info.field_nodes[0].selection_set)
                if pass_graphql_path:
                    kwargs[pass_graphql_path] = [type_, info.path.key]
                authenticated_user = info.context.authenticated_user
                if force_authenticated_user and not authenticated_user:
                    raise exceptions.UnauthenticatedError()
                if pass_authenticated_user:
                    kwargs[pass_authenticated_user] = authenticated_user
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

    # HTTP views

    def _django_view(self, request):
        # pylint: disable=C0415 # Import outside toplevel
        from django.http import JsonResponse
        # check method
        if request.method != 'POST':
            return JsonResponse({'errors': [{'message':
                'Method not allowed, only POST is supported',
            }]}, status=405)
        # input should be a JSON object
        try:
            data = json.loads(request.body)
        except json.decoder.JSONDecodeError as error:
            return JsonResponse({'errors': [{'message':
                f'HTTP request body is not valid JSON: {error}',
            }]}, status=400)
        # input should be a JSON object
        if not isinstance(data, dict):
            return JsonResponse({'errors': [{'message':
                'HTTP request body should be formatted as a JSON object',
            }]}, status=400)
        # extract & validate string query
        query = data.get('query')
        if not isinstance(query, str):
            return JsonResponse({'errors': [{'message':
                'In HTTP request body JSON object, '
                'mandatory parameter "query" should be a string',
            }]}, status=400)
        # extract & validate variables mapping
        variables = data.get('variables', {})
        if not isinstance(variables, dict):
            return JsonResponse({'errors': [{'message':
                'In HTTP request body JSON object, '
                'optional parameter "variables" should be an object',
            }]}, status=400)
        # extract & validate string query
        operation_name = data.get('operationName', None)
        if operation_name is not None and not isinstance(operation_name, str):
            return JsonResponse({'errors': [{'message':
                'In HTTP request body JSON object, '
                'optional parameter "operationName" should be a string',
            }]}, status=400)
        # extract user
        if request.user and request.user.is_authenticated and not request.user.is_anonymous:
            authenticated_user = request.user
        else:
            authenticated_user = None
        # compute & return result
        result = self.execute(
            source = query,
            variables = variables,
            operation_name = operation_name,
            authenticated_user = authenticated_user,
            serializable_output = True,
        )
        return JsonResponse(result)
