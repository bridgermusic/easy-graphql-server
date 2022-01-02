import os
import django.test
from easy_graphql.testing import make_tests_loader

from .schemas.django.graphql import schema


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'schemas/django/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_TESTS_PATH', DEFAULT_TESTS_PATH)


class TestCase(django.test.TransactionTestCase):
    reset_sequences = True
    databases = ['default']

    def setUp(self):
        self.tearDown()


load_tests = make_tests_loader(
    schema = schema,
    path = TESTS_PATH,
    base_test_class = TestCase,
)
