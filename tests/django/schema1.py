import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model


schema = easy_graphql_server.Schema()

schema.expose_model(
    orm_model = Person,
    plural_name = 'people',
    can_expose = ('id', 'username', 'first_name', 'last_name', 'birth_date',
        'houses', 'home', 'daily_occupations'),
)

schema.expose_query(
    name = 'me',
    force_authenticated_user = True,
    pass_authenticated_user = True,
    output_format = easy_graphql_server.Model('person').output_format + {
        'is_superuser': bool, 'is_staff': bool,
    },
    method = lambda authenticated_user: authenticated_user,
)

schema.expose_model(
    orm_model = House,
)

schema.expose_model(
    orm_model = DailyOccupation,
    only_when_child_of = Person,
)

schema.expose_model(
    orm_model = BankAccount,
    force_authenticated_user = True,
)
