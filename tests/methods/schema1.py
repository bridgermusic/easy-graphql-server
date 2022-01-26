import easy_graphql_server


schema = easy_graphql_server.Schema()

schema.expose_mutation(
    name = 'dummy_double',
    input_format = {
        'input_text': easy_graphql_server.Mandatory(str),
        'input_number': float,
    },
    output_format = {
        'output_text': str,
        'output_number': float,
    },
    method = lambda authenticated_user=None, input_text='', input_number=0.0: {
        'output_text': 2 * input_text,
        'output_number': 2 * input_number,
    }
)

schema.expose_query(
    name = 'dummy_retrieve',
    input_format = {
        'input_identifier': easy_graphql_server.Mandatory(int),
    },
    output_format = {
        'output_identifier': int,
        'output_name': str,
    },
    method = lambda input_identifier: {
        'output_identifier': input_identifier,
        'output_name': f'dummy_{input_identifier}',
    }
)

schema.expose_query(
    name = 'dummy_collection_input',
    input_format = {'max_index': int, 'collection': [{'value': float}]},
    output_format = {'sum': float},
    method = lambda max_index, collection=None: {
        'sum': sum(
            item['value']
            for item in collection[:max_index + 1]
        ) if (collection and max_index >= 0) else None
    }
)

schema.expose_query(
    name = 'dummy_collection_output',
    input_format = {
        'max_index': easy_graphql_server.Mandatory(int),
    },
    output_format = {
        'max_index': int,
        'collection': [{'index': int, 'identifier': str}],
    },
    method = lambda max_index: {
        'max_index': max_index,
        'collection': [
            {
                'index': i,
                'identifier': f's{i}',
            }
            for i in range(max_index)
        ]
    }
)

schema.expose_query(
    name = 'me',
    output_format = {
        'id': int,
        'username': str,
        'is_superuser': bool,
        'is_staff': bool,
    },
    pass_authenticated_user = True,
    method = lambda authenticated_user: authenticated_user
)
