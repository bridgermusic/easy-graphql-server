# TODO

- give possibility to use model fields in `input_format` and `output_format` mappings
- check generated type names (from model exposition) in tests
- possibility to pre-filter collection of model instances with `authenticated_user`
- allow custom fields for models (C, R, U, D)
- `case_manager` in Schema
- use description from Django fields
- handle GraphQL subscriptions
- intercept `GraphQLError` (raised for required fields for instance)
- rewrite `webserver._schema_view.SchemaView._must_serve_graphiql()` method

# DONE

- give possibility to use model interfaces in `input_format` and `output_format` mappings
- enums generated for models should have unique names, even when nested
- document options for `expose_model()`
- document options for `expose_method()`
- if no error, "errors" field should not be present in HTTP response (see https://graphql.org/learn/serving-over-http/)
- split `types.py` into `graphql_types.py` and `types.py`
- views with GraphIQL
- check generated SQL in tests
- write SQL tests for nested queries
- write SQL tests for permissions
- handle authentication from HTTP view, callback method, exposed model, tests
- Django view
- better exceptions
- `TestCase.databases = ['default']` shouldn't be necessary in `testing`
- `NonNull` for mandatory input fields
- model create
- model update
- transactions
- `ModelConfig.only_when_child_of` should do something
- added publication tool
