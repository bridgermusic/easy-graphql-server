import os
from easy_graphql_server.testing import make_tests_loader

from .schemas.methods.schema import schema


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'schemas/methods/docs')
TESTS_PATH = os.getenv('easy_graphql_server_TESTS_PATH', DEFAULT_TESTS_PATH)


load_tests = make_tests_loader(schema, TESTS_PATH)
