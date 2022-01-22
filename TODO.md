# TODO

- document options for `expose_model()`
- enums generated for models should have unique names, even when nested
- allow custom fields for models (C, R, U, D)
- `case_manager` in Schema
- use description from Django fields
- handle GraphQL subscriptions
- intercept `GraphQLError` (raised for required fields for instance)
- rewrite `webserver._schema_view.SchemaView._must_serve_graphiql()` method

# DONE

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
