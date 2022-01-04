# TODO

- `case_manager` in Schema
- use description from Django fields
- handle GraphQL subscriptions
- check generated SQL in tests:
        ```python

            from django.db import connection, reset_queries
            import re

            reset_queries()

            EXECUTE_GRAPHQL_QUERIES()

            print()
            print(96*'<')
            for query in list(connection.queries):
                print()
                print(re.sub(r' (SELECT|FROM|LEFT|WHERE)', '\n\\1', query['sql']))
                print()
            print(96*'>')
            print()

            assert GENERATED_SQL == EXPECTED_SQL
        ```
- write SQL tests for nested queries, and also for permissions
- Django view with GraphIQL

# DONE

- manage authentication from HTTP view, callback method, exposed model
- Django view
- better exceptions
- `TestCase.databases = ['default']` shouldn't be necessary in `testing`
- `NonNull` for mandatory input fields
- model create
- model update
- transactions
- `ModelConfig.only_when_child_of` should do something
- added publication tool
