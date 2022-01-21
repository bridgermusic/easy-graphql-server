# TODO

- if there were no errors returned, the "errors" field should not be present on the response (see https://graphql.org/learn/serving-over-http/)
- document options for `expose_method()` and `expose_model()`
- allow custom fields for models (C, R, U, D)
- `case_manager` in Schema
- use description from Django fields
- handle GraphQL subscriptions
- intercept `GraphQLError` (raised for required fields for instance)
- rewrite `webserver._schema_view.SchemaView._is_graphiql_requested()` method

# DONE

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
