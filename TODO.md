# TODO

- document options for `expose_method()` and `expose_model()`
- allow custom fields for models (C, R, U, D)
- split `types.py` into `graphql_types.py` and `types.py`
- `case_manager` in Schema
- use description from Django fields
- handle GraphQL subscriptions
- Django view with GraphIQL
- intercept `GraphQLError` (raised for required fields for instance)

# DONE

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
