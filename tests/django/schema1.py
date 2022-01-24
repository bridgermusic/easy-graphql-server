import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model
from django.db.models import Sum


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
    custom_fields = [
        {
            'name': 'tenants_occupations',
            'format': [{
                'hours_per_day': int,
                'occupation': easy_graphql_server.Model('daily_occupation').fields.occupation,
            }],
            'read_one': lambda instance, authenticated_user, graphql_selection: [
                {
                    'occupation': occupation['occupation'],
                    'hours_per_day': occupation['total_hours_per_day'],
                }
                for occupation
                in DailyOccupation.objects.filter(person__home__id = instance.id).values('occupation').annotate(
                    total_hours_per_day = Sum('hours_per_day'),
                ).order_by('occupation')
            ]
        }
    ],
)

schema.expose_model(
    orm_model = DailyOccupation,
    only_when_child_of = Person,
)

schema.expose_model(
    orm_model = BankAccount,
    force_authenticated_user = True,
)
