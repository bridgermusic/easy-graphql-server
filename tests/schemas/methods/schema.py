import easy_graphql


schema = easy_graphql.Schema()

schema.expose_mutation(
    name = 'dummy_double',
    input_format = {
        'input_text': easy_graphql.NonNull(easy_graphql.String),
        'input_number': easy_graphql.Float,
    },
    output_format = {
        'output_text': easy_graphql.String,
        'output_number': easy_graphql.Float,
    },
    method = lambda authenticated_user=None, input_text='', input_number=0.0: {
        'output_text': 2 * input_text,
        'output_number': 2 * input_number,
    }
)

schema.expose_query(
    name = 'dummy_retrieve',
    input_format = {
        'input_identifier': easy_graphql.NonNull(easy_graphql.Int),
    },
    output_format = {
        'output_identifier': easy_graphql.Int,
        'output_name': easy_graphql.String,
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
        'max_index': easy_graphql.NonNull(easy_graphql.Int),
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
