import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from model_bakery import baker


@pytest.fixture
def app_client():
    return Client()


@pytest.fixture
def django_default_auth_user():
    return {
        "last_name": "admin",
    }


@pytest.mark.django_db
@pytest.fixture
def django_auth_user(django_default_auth_user):
    return baker.make(get_user_model(), **django_default_auth_user)


@pytest.fixture
def person_recipe():
    return {"last_name": "lastTest1", "first_name": "firstTest1"}
