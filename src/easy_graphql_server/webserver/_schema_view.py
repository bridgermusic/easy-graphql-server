"""
    Definition of base `SchemaView` class.
"""

import re
import json
import pathlib


class SchemaView:
    # pylint: disable=too-few-public-methods

    """
        Django schema view. Base class for `DjangoSchemaView`.
    """

    def __init__(self, schema, with_graphiql=True):
        self.schema = schema
        self.with_graphiql = with_graphiql
        if with_graphiql:
            graphiql_page_path = pathlib.Path(__file__).parent / 'static/graphiql.html'
            with open(graphiql_page_path, 'rt', encoding='utf-8') as graphiql_page_file:
                self.graphiql_page = graphiql_page_file.read()

    def _must_serve_graphiql(self, headers):
        if not self.with_graphiql:
            return False
        # taken from https://github.com/graphql-python/graphene-django/blob/
        # e1a7d1983314174c91ede1ebbfe35a9009cf6268/graphene_django/views.py#L33
        def qualify(content_type):
            parts = content_type.split(';', 1)
            if len(parts) == 2:
                match = re.match(r'(^|;)q=(0(\.\d{,3})?|1(\.0{,3})?)(;|$)', parts[1])
                if match:
                    return parts[0].strip(), float(match.group(2))
            return parts[0].strip(), 1
        raw_content_types = headers.get('Accept', '*/*').split(',')
        qualified_content_types = map(qualify, raw_content_types)
        accepted_content_types = [
            content_type[0]
            for content_type in sorted(
                qualified_content_types, key=lambda content_type: content_type[1], reverse=True)
        ]
        # taken from https://github.com/graphql-python/graphene-django/blob/
        # e1a7d1983314174c91ede1ebbfe35a9009cf6268/graphene_django/views.py#L351
        html_priority = (
            len(accepted_content_types) - accepted_content_types.index('text/html')
            if 'text/html' in accepted_content_types
            else 0
        )
        json_priority = (
            len(accepted_content_types) - accepted_content_types.index('application/json')
            if 'application/json' in accepted_content_types
            else 0
        )
        return html_priority > json_priority

    # pylint: disable=too-many-return-statements
    def compute_response(self, method, headers, body, query, authenticated_user):
        """
            Compute response to be served by HTTP server.
        """
        # data extraction
        if method == 'POST':
            # extract data from JSON payload
            try:
                data = json.loads(body)
            except json.decoder.JSONDecodeError as error:
                return {'errors': [{'message':
                    f'HTTP request body is not valid JSON: {error}',
                }]}, 400
            if not isinstance(data, dict):
                return {'errors': [{'message':
                    'HTTP request body should be formatted as a JSON object',
                }]}, 400
        elif method == 'GET':
            if self._must_serve_graphiql(headers):
                return self.graphiql_page
            try:
                data = {
                    'query': query.get('query'),
                    'variables': json.loads(query.get('variables', 'null')),
                    'operationName': query.get('operationName'),
                }
            except json.JSONDecodeError:
                return {'errors': [{'message':
                    f'Parameter `variables` is not valid JSON: {error}',
                }]}, 400
        else:
            return {'errors': [{'message':
                f'Method {method} not allowed, only GET and POST are supported',
            }]}, 405
        # extract & validate string query
        query = data.get('query')
        if not isinstance(query, str):
            return {'errors': [{'message':
                'Required parameter "query" should be a string',
            }]}, 400
        # extract & validate variables mapping
        variables = data.get('variables') or {}
        if not isinstance(variables, dict):
            return {'errors': [{'message':
                'Optional parameter "variables" should be an mapping',
            }]}, 400
        # extract & validate string query
        operation_name = data.get('operationName', None)
        if operation_name is not None and not isinstance(operation_name, str):
            return {'errors': [{'message':
                'Optional parameter "operationName" should be a string',
            }]}, 400
        # compute & return result
        result = self.schema.execute(
            query = query,
            variables = variables,
            operation_name = operation_name,
            authenticated_user = authenticated_user,
            serializable_output = True,
        )
        return result, 200
