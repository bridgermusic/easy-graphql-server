import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model
from django.db.models import Sum


schema = easy_graphql_server.Schema()

class ExposedPerson(schema.ExposedModel):
    orm_model = Person
    plural_name = 'people'
    can_expose = ('id', 'username', 'first_name', 'last_name', 'birth_date',
        'houses', 'home', 'daily_occupations')

class ExposedMe(schema.ExposedQuery):
    name = 'me'
    force_authenticated_user = True
    pass_authenticated_user = True
    output_format = easy_graphql_server.Model('person').output_format + {
        'is_superuser': bool, 'is_staff': bool}
    @staticmethod
    def method(authenticated_user):
        return authenticated_user

class ExposedDailyOccupation(schema.ExposedModel):
    orm_model = DailyOccupation
    only_when_child_of = Person

class ExposedHouseTenantsOccupations(easy_graphql_server.CustomField):
    name = 'tenants_occupations'
    format = {
        'total_hours_per_day': int,
        'occupations': easy_graphql_server.Model('dailyoccupation').fields.occupation,
    }
    @staticmethod
    def read_one(instance, authenticated_user, graphql_selection):
        return [
            {
                'occupation': occupation['occupation'],
                'hours_per_day': occupation['total_hours_per_day'],
            }
            for occupation
            in DailyOccupation.objects.filter(person__home__id = instance.id).values('occupation').annotate(
                total_hours_per_day = Sum('hours_per_day'),
            )
        ]

class ExposedHouse(schema.ExposedModel):
    orm_model = House
    custom_fields = [ExposedHouseTenantsOccupations]

class ExposedBankAccount(schema.ExposedModel):
    orm_model = BankAccount
    force_authenticated_user = True
