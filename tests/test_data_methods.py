import os
from easy_graphql_server.testing import make_tests_loader

from .methods import schema1, schema2, schema3


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'methods/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', DEFAULT_TESTS_PATH)


load_tests = make_tests_loader(
    schemata = (schema1.schema, schema2.schema, schema3.schema),
    path = TESTS_PATH)
