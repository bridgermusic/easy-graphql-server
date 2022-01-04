import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model


schema = easy_graphql_server.Schema()

schema.expose_query(
    name = 'me',
    force_authenticated_user = True,
    pass_authenticated_user = True,
    output_format = {
        'id': int,
        'username': str,
        'is_superuser': bool,
        'is_staff': bool,
    },
    method = lambda authenticated_user: {
        'id': authenticated_user.id,
        'username': authenticated_user.username,
        'is_superuser': authenticated_user.is_superuser,
        'is_staff': authenticated_user.is_staff,
    },
)

schema.expose_model(
    orm_model = Person,
    plural_name = 'people',
    can_expose = ('id', 'username', 'first_name', 'last_name', 'birth_date',
        'houses', 'home', 'daily_occupations'),
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
