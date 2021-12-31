import easy_graphql

from .models import Person, House, DailyOccupation


schema = easy_graphql.Schema()

schema.expose_query(
    name = 'dummy_collection_input',
    input_format = {'max_index': int, 'collection': [{'value': float}]},
    output_format = {'sum': float},
    method = lambda max_index, collection=None: {'sum': sum(collection[i]['value'] for i in range(max_index)) if collection else None}
)

schema.expose_model(
    orm_model = Person,
    plural_name = 'people',
)

schema.expose_model(
    orm_model = House,
)

schema.expose_model(
    orm_model = DailyOccupation,
    only_when_child_of = Person,
)
