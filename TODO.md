- `case_manager` in Schema
- `NonNull` for mandatory input fields
- `authenticated_user`
- transactions
- exceptions
- use description from Django fields
- views (see graphiql also)
- `TestCase.databases = ['default']` shouldn't be necessary in `testing`
- check generated SQL:
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
