"""
    `Schema` class is defined here. This is the root class that will be used as
    a central point to the easy_graphql_server API.
"""

import inspect
from collections import defaultdict

from graphql import GraphQLSchema, GraphQLField, GraphQLObjectType
from graphql.type.validate import validate_schema # pylint: disable=no-name-in-module,import-error
from graphql.utilities import get_introspection_query # pylint: disable=no-name-in-module,import-error
from graphql.graphql import graphql_sync

from . import exceptions, exposition, introspection
from .conversion import to_graphql_type, to_graphql_argument
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

    def __init__(self, debug=False, casing=Casing.SNAKE, restrict_models_queried_fields=False):
        self.methods = defaultdict(dict)
        self.subclasses = []
        self.dirty = True
        self.graphql_schema = None
        self.models_configs = []
        # options
        self.case_manager = casing.value
        self.debug = debug
        self.restrict_models_queried_fields = restrict_models_queried_fields
        # abstract parent classes
        class Exposed(exposition.Exposed):
            # pylint: disable=too-few-public-methods,missing-class-docstring
            pass
        self.Exposed = Exposed # pylint: disable=invalid-name
        class ExposedModel(exposition.ExposedModel, self.Exposed):
            # pylint: disable=too-few-public-methods,missing-class-docstring
            pass
        self.ExposedModel = ExposedModel # pylint: disable=invalid-name
        class ExposedQuery(exposition.ExposedQuery, self.Exposed):
            # pylint: disable=too-few-public-methods,missing-class-docstring
            pass
        self.ExposedQuery = ExposedQuery # pylint: disable=invalid-name
        class ExposedMutation(exposition.ExposedMutation, self.Exposed):
            # pylint: disable=too-few-public-methods,missing-class-docstring
            pass
        self.ExposedMutation = ExposedMutation # pylint: disable=invalid-name
        self.orm_model_manager_classes = []

    def get_documentation(self, with_descriptions=False):
        """
            Return GraphQL schema description in JSON format.
        """
        result = self.execute(
            get_introspection_query(descriptions=with_descriptions, directive_is_repeatable=True))
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
        if 'restrict_queried_fields' not in options:
            options['restrict_queried_fields'] = self.restrict_models_queried_fields
        model_config = ModelConfig(orm_model=orm_model, schema=self, **options)
        self.models_configs.append(model_config)
        orm_model_manager_class = model_config.orm_model_manager.__class__
        if orm_model_manager_class not in self.orm_model_manager_classes:
            self.orm_model_manager_classes.append(orm_model_manager_class)

    def execute(self, query, variables=None, operation_name=None,
            authenticated_user=None,
            serializable_output=False):
        """
            Execute a GraphQL query within the schema.
        """
        result = graphql_sync(
            schema = self._get_graphql_schema(),
            source = query,
            variable_values = variables or {},
            operation_name = operation_name,
            context_value = ContextValue(
                authenticated_user = authenticated_user,
            ),
        )
        if serializable_output:
            formatted_result = result.formatted
            if 'errors' in formatted_result and not formatted_result['errors']:
                del formatted_result['errors']
            return formatted_result
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

    def get_model_config(self, orm_model=None, name=None):
        """
            Retrieve an instance of `ModelConfig` if the passed `orm_model` has been
            exposed, `None` otherwise.
        """
        if not bool(orm_model) ^ bool(name):
            raise ValueError('You have to specify exactly one of the following parameters: '
                '`orm_model`, `name`')
        for model_config in self.models_configs:
            if model_config.orm_model_manager.orm_model == orm_model or model_config.name == name:
                return model_config
        return None

    def as_django_view(self, with_graphiql=True):
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
        # pylint: disable=import-outside-toplevel
        from .webserver.django_schema_view import DjangoSchemaView
        return DjangoSchemaView(schema=self, with_graphiql=with_graphiql).view

    def as_flask_view(self):
        """
            Expose schema as a Flask view.

            Example:

            ```python
            from flask import Flask
            import easy_graphql_server

            schema = easy_graphql_server.Schema()

            app = Flask()

            app.add_url_rule(
                rule = '/graphql',
                endpoint = 'graphql',
                view_func = schema.as_flask_view())
            ```
        """
        # pylint: disable=import-outside-toplevel
        from .webserver.flask_schema_view import FlaskSchemaView
        return FlaskSchemaView(schema=self).view

    # private attributes & methods

    def _expose_method(self, type_, name, method, input_format=None, output_format=None,
            pass_graphql_selection=False, pass_graphql_path=False,
            pass_authenticated_user=False, require_authenticated_user=False):
        self.methods[type_][name] = GraphQLField(
        # output format
        type_ = to_graphql_type(
            type_ = output_format,
            prefix = name,
            for_input = False,
            schema = self,
        ) if output_format else None,
        # input format
        args = to_graphql_argument(
            type_ = input_format,
            prefix = name,
            schema = self,
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
            require_authenticated_user = require_authenticated_user,
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
                message = ' when subclassing `ExposedModel`'
                exposition_method = self.expose_model
                validation_method = ModelConfig
                excluded_arguments = ('self', 'schema')
            elif issubclass(subclass, exposition.ExposedQuery):
                message = ' when subclassing `ExposedQuery`'
                exposition_method = self.expose_query
                validation_method = self._expose_method
                excluded_arguments = ('self', 'type_')
            elif issubclass(subclass, exposition.ExposedMutation):
                message = ' when subclassing `ExposedMutation`'
                exposition_method = self.expose_mutation
                validation_method = self._expose_method
                excluded_arguments = ('self', 'type_')
            else:
                raise ValueError(f'Unrecognized class: {subclass}')
            # attributes validation
            introspection.validate_class_attributes_against_method_arguments(
                cls = subclass,
                method = validation_method,
                excluded_arguments = excluded_arguments,
                message = message)
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

    def _make_callback(self, type_, method,
            pass_graphql_selection, pass_graphql_path,
            pass_authenticated_user, require_authenticated_user):
        def callback(source, info, **kwargs): # pylint: disable=unused-argument
            try:
                # ensure authenticated user when mandatory
                if require_authenticated_user or pass_authenticated_user:
                    authenticated_user = info.context.authenticated_user
                if require_authenticated_user and not authenticated_user:
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
                raise exceptions.InternalError(error if self.debug else None)
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
            if selection.name.value != '__typename'
        }
