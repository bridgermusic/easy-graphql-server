import os
from django.test import TransactionTestCase
from easy_graphql.testing import make_tests_loader

from .schemas.django.graphql import schema


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'schemas/django/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_TESTS_PATH', DEFAULT_TESTS_PATH)


load_tests = make_tests_loader(
    schema = schema,
    path = TESTS_PATH,
    base_test_class = TransactionTestCase,
)
