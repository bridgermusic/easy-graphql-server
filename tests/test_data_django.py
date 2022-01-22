import os

from .django import schema1, schema2, schema3
from .django.base_test_case import BaseTestCase

from easy_graphql_server.testing import make_tests_loader


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'django/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', DEFAULT_TESTS_PATH)


load_tests = make_tests_loader(
    schemata = (schema1.schema, schema2.schema, schema3.schema),
    path = TESTS_PATH,
    base_test_class = BaseTestCase,
)
