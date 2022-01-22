import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model


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

class ExposedHouse(schema.ExposedModel):
    orm_model = House

class ExposedDailyOccupation(schema.ExposedModel):
    orm_model = DailyOccupation
    only_when_child_of = Person

class ExposedBankAccount(schema.ExposedModel):
    orm_model = BankAccount
    force_authenticated_user = True
