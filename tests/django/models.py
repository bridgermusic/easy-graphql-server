import sqlite3

from django.db import models
from django.db.models import Q
import django.contrib.auth.models
import django.core.exceptions
from django.conf import settings

from faker import Faker

from easy_graphql_server import Operation


GENDER_CHOICES = ('female', 'male', 'other')

class Person(django.contrib.auth.models.AbstractBaseUser):
    class Meta:
        ordering = ('id',)
        db_table = 'auth_user'
    id = models.AutoField(primary_key=True)
    gender = models.CharField(
        choices=[(k,k) for k in GENDER_CHOICES],
        max_length=max(len(k) for k in GENDER_CHOICES),
        blank=True, default='other')
    username = models.CharField(max_length=255, unique=True)
    password = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=64)
    birth_date = models.DateField(blank=True, null=True)
    is_staff = models.BooleanField(blank=True, default=False)
    is_superuser = models.BooleanField(blank=True, default=False)
    home = models.ForeignKey(
        to='House',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='tenants')

    USERNAME_FIELD = 'username'

    objects = django.contrib.auth.models.UserManager()

    def clean(self):
        # pylint: disable=E1101 # Instance of 'Person' has no 'daily_occupations' member
        daily_occupations = list(self.daily_occupations.all())
        if daily_occupations:
            hours_sum = 0
            for daily_occupation in daily_occupations:
                hours_sum += daily_occupation.hours_per_day
            if hours_sum != 24:
                raise django.core.exceptions.ValidationError({'daily_occupations': [
                    django.core.exceptions.ValidationError(
                        message = f'the sum of `hours_per_day` for all items should amount to 24, not {hours_sum}',
                        code = 'hours_sum',
                        params = {'expected_hours_sum': 24, 'computed_hours_sum': hours_sum}
                    )
                ]})

    def has_permission(self, authenticated_user, operation, data):
        # unauthenticated requests can only create or read people
        if authenticated_user is None:
            return operation in (Operation.CREATE, Operation.READ)
        # superusers can do anything
        if authenticated_user.is_superuser:
            return True
        # one can always manipulate one's own account
        return self.id == authenticated_user.id

    def __str__(self):
        return self.username

    def __repr__(self):
        return f'<Person first_name={repr(self.first_name)} last_name={repr(self.last_name)} birth_date={self.birth_date}>'


class House(models.Model):
    class Meta:
        ordering = ('id',)
    id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255)
    construction_date = models.DateField(blank=True, null=True)
    owner = models.ForeignKey(
        to=Person,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='houses')
    def filter_by_user(queryset, authenticated_user):
        if not authenticated_user:
            return queryset.none()
        if authenticated_user.is_superuser:
            return queryset
        return queryset.filter(
            Q(tenants__id = authenticated_user.id) | Q(owner_id = authenticated_user.id)
        )


OCCUPATION_CHOICES = ('EAT', 'SLEEP', 'WORK', 'COMMUTE', '_')

class DailyOccupation(models.Model):
    class Meta:
        ordering = ('id',)
    id = models.AutoField(primary_key=True)
    hours_per_day = models.IntegerField()
    occupation = models.CharField(
        choices=[(k,k) for k in OCCUPATION_CHOICES],
        max_length=max(len(k) for k in OCCUPATION_CHOICES))
    person = models.ForeignKey(
        to=Person,
        on_delete=models.CASCADE,
        related_name='daily_occupations')


class BankAccount(models.Model):
    class Meta:
        ordering = ('id',)
    id = models.AutoField(primary_key=True)
    iban = models.CharField(max_length=34)
    owner = models.ForeignKey(
        to=Person,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name='bank_accounts')

    def has_permission(self, authenticated_user, operation, data):
        if authenticated_user.is_superuser:
            return True
        return self.owner_id == authenticated_user.id

    @classmethod
    def filter_for_user(cls, authenticated_user, base_queryset):
        if not authenticated_user:
            return base_queryset.none()
        if authenticated_user.is_superuser:
            return base_queryset
        return base_queryset.filter(owner_id = authenticated_user.id)


template_database = None
def populate_database(random_seed=1985, houses_count=123, people_count=456, max_houses_count_per_person=5, bank_accounts_count=789):

    # try to restore from template database
    global template_database
    if template_database is not None:
        django_database = django.db.connections.all()[0].connection
        # clear Django database
        sql = """
            PRAGMA writable_schema = 1;
            DELETE FROM sqlite_master WHERE type IN ('table', 'index', 'trigger');
            PRAGMA writable_schema = 0;
            PRAGMA INTEGRITY_CHECK;
        """
        for statement in sql.split(';'):
            django_database.execute(statement)
        # restore database to previous state, and exit function
        template_database.backup(django_database)
        return

    # ensure database is empty
    if Person.objects.count() or House.objects.count() or DailyOccupation.objects.count():
        raise Exception('`populate_database()` should be called on an empty database')

    # initialize generator
    Faker.seed(random_seed)
    fake = Faker()

    # populate houses
    for i in range(houses_count):
        location, construction_date = fake.city(), fake.date_of_birth()
        house = House(
            location = location,
            construction_date = construction_date,
        )
        house.save()
    houses = list(House.objects.all())

    # populate people
    for i in range(people_count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        birth_date = fake.date_of_birth() if fake.random_int(0, 2) <= 1 else None
        email = f'{first_name}.{last_name}@example.com'.lower()
        # ensure email unicity
        index = 0
        while Person.objects.filter(username = email).exists():
            index += 1
            email = email.replace('@', f'{index}@')
        # initialize person
        person = Person(
            username = email,
            first_name = first_name,
            last_name = last_name,
            birth_date = birth_date,
        )
        person.set_password(settings.DEFAULT_USER_PASSWORD)
        person.save()
        # initialize person's houses
        for j in range(int(max_houses_count_per_person * i / people_count)):
            house = houses[fake.random_int(0, houses_count - 1)]
            house.owner_id = person.id
            house.save()

    # initialize current house for people
    for person in Person.objects.all():
        person.home = houses[fake.random_int(0, houses_count - 1)]
        person.save()

    # populate bank accounts
    people = list(Person.objects.all())
    for i in range(bank_accounts_count):
        bank_account = BankAccount(
            iban = fake.iban(),
            owner = people[fake.random_int(0, people_count - 1)],
        )
        bank_account.save()

    # populate occupations
    for person in people:
        sum = 0
        OCCUPATION_CHOICES = ('EAT', 'SLEEP', 'WORK', 'COMMUTE')
        for occupation in OCCUPATION_CHOICES:
            if sum == 24:
                break
            hours_per_day = fake.random_int(0, 24 - sum)
            DailyOccupation(
                hours_per_day = hours_per_day,
                occupation = occupation,
                person = person,
            ).save()
            sum += hours_per_day
        if sum < 24:
            DailyOccupation(
                hours_per_day = 24 - sum,
                occupation = occupation,
                person = person,
            ).save()

    # save to template database
    if template_database is None:
        template_database = sqlite3.connect(':memory:')
        django_database = django.db.connections.all()[0].connection
        django_database.backup(template_database)
