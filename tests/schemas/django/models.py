from django.db import models
import django.core.exceptions
from faker import Faker


class Person(models.Model):
    id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=32)
    last_name = models.CharField(max_length=64)
    birth_date = models.DateField(blank=True, null=True)
    home = models.ForeignKey(
        to='House',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='tenants')

    def clean(self):
        # pylint: disable=E1101 # Instance of 'Person' has no 'daily_occupations' member
        daily_occupations = list(self.daily_occupations.all())
        if daily_occupations:
            hours_sum = 0
            for daily_occupation in daily_occupations:
                hours_sum += daily_occupation.hours_per_day
            if hours_sum != 24:
                raise django.core.exceptions.ValidationError({'daily_occupations': [
                    f'the sum of `hours_per_day` for all items should amount to `24`, not `{hours_sum}`']})

    def __repr__(self):
        return f'<Person first_name={repr(self.first_name)} last_name={repr(self.last_name)} birth_date={self.birth_date}>'

    __str__ = __repr__


class House(models.Model):
    id = models.AutoField(primary_key=True)
    location = models.CharField(max_length=255)
    construction_date = models.DateField()
    owner = models.ForeignKey(
        to=Person,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='houses')


OCCUPATION_CHOICES = ('EAT', 'SLEEP', 'WORK', 'COMMUTE', '_')

class DailyOccupation(models.Model):
    id = models.AutoField(primary_key=True)
    hours_per_day = models.IntegerField()
    occupation = models.CharField(
        choices=[(k,k) for k in OCCUPATION_CHOICES],
        max_length=max(len(k) for k in OCCUPATION_CHOICES))
    person = models.ForeignKey(
        to=Person,
        on_delete=models.CASCADE,
        related_name='daily_occupations')


def populate_database(random_seed=1985, houses_count=123, people_count=456, max_houses_count_per_person=5):

    # initialize generator
    Faker.seed(random_seed)
    fake = Faker()

    # populate houses
    for i in range(houses_count):
        house = House(
            location = fake.city(),
            construction_date = fake.date_of_birth(),
        )
        house.save()
    houses = list(House.objects.all())

    # populate people
    for i in range(people_count):
        # initialize person
        person = Person(
            first_name = fake.first_name(),
            last_name = fake.last_name(),
            birth_date = fake.date_of_birth() if fake.random_int(0, 2) <= 1 else None,
        )
        person.save()
        # initialize person's houses
        for j in range(int(max_houses_count_per_person * i / people_count)):
            house = houses[fake.random_int(0, houses_count - 1)]
            house.owner_id = person.id
            house.save()

    # initialize current house for people
    for person in Person.objects.all():
        if fake.random_int(0, 2):
            person.home = houses[fake.random_int(0, houses_count - 1)]
            person.save()
