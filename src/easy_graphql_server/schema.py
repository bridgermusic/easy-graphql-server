"""
    `Schema` class is defined here. This is the root class that will be used as
    a central point to the easy_graphql_server API.
"""

import inspect
from collections import defaultdict

from graphql import GraphQLSchema, GraphQLField, GraphQLObjectType
# Had to disable pylint below, because "No name '...' in module '...'" and "Unable to import '...'"
from graphql.type.validate import validate_schema # pylint: disable=E0611,E0401
from graphql.utilities import get_introspection_query # pylint: disable=E0611,E0401
from graphql.graphql import graphql_sync

from . import exceptions, exposition, introspection
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

        Any subclass of `ExposedModel`, `ExposedQuery` or `ExposedMutation` can
        be exposed via `Schema.expose()`.

        Schema can be validated using `Schema.check()`.
    """

    # public methods

    def __init__(self, casing=Casing.SNAKE):
        self.methods = defaultdict(dict)
        self.subclasses = []
        self.dirty = True
        self.graphql_schema = None
        self.models_configs = []
        self.case_manager = casing.value
        # abstract parent classes
        class Exposed(exposition.Exposed):
            # pylint: disable=R0903 # Too few public methods
            # pylint: disable=C0115 # Missing class docstring
            pass
        self.Exposed = Exposed # pylint: disable=C0103 # doesn't conform to snake_case naming style
        class ExposedModel(exposition.ExposedModel, self.Exposed):
            # pylint: disable=R0903 # Too few public methods
            # pylint: disable=C0115 # Missing class docstring
            pass
        self.ExposedModel = ExposedModel # pylint: disable=C0103 # doesn't conform to snake_case naming style
        class ExposedQuery(exposition.ExposedQuery, self.Exposed):
            # pylint: disable=R0903 # Too few public methods
            # pylint: disable=C0115 # Missing class docstring
            pass
        self.ExposedQuery = ExposedQuery # pylint: disable=C0103 # doesn't conform to snake_case naming style
        class ExposedMutation(exposition.ExposedMutation, self.Exposed):
            # pylint: disable=R0903 # Too few public methods
            # pylint: disable=C0115 # Missing class docstring
            pass
        self.ExposedMutation = ExposedMutation # pylint: disable=C0103 # doesn't conform to snake_case naming style
        self.orm_model_manager_classes = []

    def get_documentation(self, with_descriptions=False):
        """
            Return GraphQL schema description in JSON format.
        """
        result = self.execute(
            get_introspection_query(descriptions=with_descriptions))
        return result.data

    def expose(self, cls):
        """
            Expose a subclass from `exposition.ExposedQuery`, `exposition.ExposedMutation`
            or `exposition.ExposedModel`
        """
        if not inspect.isclass(cls):
            raise ValueError('Parameter to `expose()` method should be a class, '
                f'`{cls}` was given instead.')
        accepted_parent_classes = (
            exposition.ExposedQuery, exposition.ExposedMutation, exposition.ExposedModel)
        if not issubclass(cls, accepted_parent_classes):
            raise ValueError('Parameter to `expose()` method should be a subclass of either '
                '`exposition.ExposedQuery`, `exposition.ExposedMutation` or '
                f'`exposition.ExposedModel`, but `{cls}` was found instead')
        self.subclasses.append(cls)

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
        orm_model_manager_class = model_config.orm_model_manager.__class__
        if orm_model_manager_class not in self.orm_model_manager_classes:
            self.orm_model_manager_classes.append(orm_model_manager_class)

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
            Expose schema as a Django view.

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
        from .webserver.django_schema_view import DjangoSchemaView
        return DjangoSchemaView(schema=self).view

    # private attributes & methods

    # pylint: disable=R0913 # Too many arguments
    def _expose_method(self, type_, name, method, input_format=None, output_format=None,
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

    def _collect_from_classes(self):
        for subclass in introspection.get_subclasses(self.Exposed):
            if subclass not in (self.ExposedModel, self.ExposedQuery, self.ExposedMutation):
                self.expose(subclass)
        for subclass in self.subclasses:
            subclass_attributes = introspection.get_public_class_attributes(subclass)
            # different parent classes, different results
            if issubclass(subclass, exposition.ExposedModel):
                parent_class = exposition.ExposedModel
                exposition_method = self.expose_model
                arguments = introspection.get_method_arguments(ModelConfig, ('self', 'schema'))
            elif issubclass(subclass, exposition.ExposedQuery):
                parent_class = exposition.ExposedQuery
                exposition_method = self.expose_query
                arguments = introspection.get_method_arguments(
                    self._expose_method, ('self', 'type_'))
            elif issubclass(subclass, exposition.ExposedMutation):
                parent_class = exposition.ExposedMutation
                exposition_method = self.expose_mutation
                arguments = introspection.get_method_arguments(
                    self._expose_method, ('self', 'type_'))
            else:
                raise ValueError(f'Unrecognized class: {subclass}')
            # attributes validation
            required_arguments = set(
                argument for argument, required in arguments.items() if required)
            for required_argument in required_arguments:
                if required_argument not in subclass_attributes:
                    raise ValueError(f'Attribute `{required_argument}` should be present on '
                        f'class `{subclass}` when subclassing `{parent_class}`')
            for subclass_attribute in subclass_attributes:
                if subclass_attribute not in arguments:
                    raise ValueError(f'Invalid attribute `{subclass_attribute}` for '
                        f'class `{subclass}` when subclassing `{parent_class}`; '
                        'consider prefixing it with an underscore')
            # actual exposition
            exposition_method(**subclass_attributes)


    # build schema when modified, returned cached version otherwise

    def _make_graphql_schema(self):
        self._collect_from_classes()
        # collect methods from exposed models
        for model_config in self.models_configs:
            model_config.expose_methods()
        # build and return schema
        return GraphQLSchema(
            query = GraphQLObjectType('Query',
                lambda: self.methods['query']) if self.methods['query'] else None,
            mutation = GraphQLObjectType('Mutation',
                lambda: self.methods['mutation']) if self.methods['query'] else None,
        )

    def _get_graphql_schema(self):
        if self.dirty:
            graphql_schema = self._make_graphql_schema()
            self.check(graphql_schema)
            self.graphql_schema = graphql_schema
            self.dirty = False
        return self.graphql_schema

    # build wrapper around passed methods to build a callback

    def _make_callback(self, type_, method, # pylint: disable=R0913 # Too many arguments
            pass_graphql_selection, pass_graphql_path,
            pass_authenticated_user, force_authenticated_user):
        def callback(source, info, **kwargs): # pylint: disable=W0613 # Unused argument 'source'
            try:
                # ensure authenticated user when mandatory
                if force_authenticated_user or pass_authenticated_user:
                    authenticated_user = info.context.authenticated_user
                if force_authenticated_user and not authenticated_user:
                    raise exceptions.UnauthenticatedError()
                # pass parameters
                if pass_authenticated_user:
                    kwargs[pass_authenticated_user] = authenticated_user
                if pass_graphql_selection:
                    kwargs[pass_graphql_selection] = self._get_graphql_selection(
                        info.field_nodes[0].selection_set)
                if pass_graphql_path:
                    kwargs[pass_graphql_path] = [type_, info.path.key]
                # executed method
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

    # using GraphQL core AST tree to return the GraphQL selection

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
