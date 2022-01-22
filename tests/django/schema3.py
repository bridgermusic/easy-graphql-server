import easy_graphql_server

from .models import Person, House, DailyOccupation, BankAccount
from django.contrib.auth import get_user_model

class ExposedPerson(easy_graphql_server.ExposedModel):
    orm_model = Person
    plural_name = 'people'
    can_expose = ('id', 'username', 'first_name', 'last_name', 'birth_date',
        'houses', 'home', 'daily_occupations')

class ExposedMe(easy_graphql_server.ExposedQuery):
    name = 'me'
    force_authenticated_user = True
    pass_authenticated_user = True
    output_format = easy_graphql_server.Model('person').output_format + {
        'is_superuser': bool, 'is_staff': bool} - ('houses', 'home', 'daily_occupations')
    @staticmethod
    def method(authenticated_user):
        return authenticated_user

class ExposedHouse(easy_graphql_server.ExposedModel):
    orm_model = House

class ExposedDailyOccupation(easy_graphql_server.ExposedModel):
    orm_model = DailyOccupation
    only_when_child_of = Person

class ExposedBankAccount(easy_graphql_server.ExposedModel):
    orm_model = BankAccount
    force_authenticated_user = True


schema = easy_graphql_server.Schema()
schema.expose(ExposedPerson)
schema.expose(ExposedMe)
schema.expose(ExposedHouse)
schema.expose(ExposedDailyOccupation)
schema.expose(ExposedBankAccount)
