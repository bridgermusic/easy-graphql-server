import os
from easy_graphql.testing import generate_testcases

from .schemas.methods.schema import schema

def load_tests(loader, tests, ignore):
    # automatically add tests generated from GraphQL files
    default_path = os.path.join(os.path.dirname(__file__), 'schemas/methods/docs')
    path = os.getenv('EASY_GRAPHQL_TESTS_PATH', default_path)
    print()
    print(default_path)
    print()
    for test in generate_testcases(schema, path):
        tests.addTest(test)
    return tests
