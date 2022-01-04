"""
    Data-driven tests for schema defined with `easy_graphql_server.Schema`.
"""

import os
import re
import json
import importlib.util
import unittest


DefaultBaseTestCase = unittest.TestCase


def generate_testcase(schema, graphql_path,
        base_test_class=DefaultBaseTestCase, django_environment=False):
    """
        Generate one test case class, corresponding to a `.gql` file.
    """
    # compute test class name
    class_name = graphql_path.split(os.sep)[-1].split('.')[0]
    class_name = re.sub(r'[^\w]+', '_', class_name).lower()
    class_name = f'easy_graphql_server_test_{class_name}'
    # generate test case from files
    class TestCase(base_test_class):
        """
            Test case class, corresponding to a `.gql` file.
        """
        @staticmethod
        def _replace_extension(path, new_extension):
            return re.sub(r'\.\w+$', f'.{new_extension}', path)
        @classmethod
        def _iterate_data(cls, graphql_path):
            # load GraphQL input
            with open(graphql_path, 'rt', encoding='utf-8') as graphql_file:
                graphql_list = re.split(r'\n\s*;\s*\n', graphql_file.read())
            # load JSON output
            json_path = cls._replace_extension(graphql_path, 'json')
            with open(json_path, 'rt', encoding='utf-8') as json_file:
                try:
                    json_list = [
                        json.loads(expected_output)
                        for i, expected_output
                        in enumerate(re.split(r'\n\s*;\s*\n', json_file.read()))
                    ]
                except json.decoder.JSONDecodeError as error:
                    raise ValueError(f'Cannot decode JSON in `{json_path}`: '
                        '{error}\n{expected_output}') from error
            # load generated SQL
            sql_path = cls._replace_extension(graphql_path, 'sql')
            if os.path.isfile(sql_path):
                with open(sql_path, 'rt', encoding='utf-8') as sql_file:
                    sql_list = sql_file.read().split(';;')
            else:
                sql_list = len(graphql_list) * [None]
            # return iterator
            return enumerate(zip(graphql_list, json_list, sql_list))
        def run_test(self, *args, **kwargs): # pylint: disable=W0613 # Unused arguments 'args', 'kwargs'
            """
                Run data-driven test
            """
            # show the difference, no matter how long
            self.maxDiff = None # pylint: disable=C0103 # Attribute name "maxDiff" doesn't conform to snake_case
            # so we can debug SQL queries
            if django_environment:
                from django.conf import settings # pylint: disable=C0415 # Import outside toplevel
                settings.DEBUG = True
            # execute setup script if present
            setup_script_path = self._replace_extension(graphql_path, 'setup.py')
            if os.path.isfile(setup_script_path):
                spec = importlib.util.spec_from_file_location(
                    f'setup_{class_name}', setup_script_path)
                setup_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(setup_module)
            # actually run the test step(s)
            for index, (graphql, json_, sql) in self._iterate_data(graphql_path):
                # compute output
                json_result = schema.execute(graphql, serializable_output=True)
                try:
                    # compare it with what was expected
                    self.assertEqual(json_, json_result)
                except:
                    # if different, show pretty output and re-raise assert exception
                    json_path = self._replace_extension(graphql_path, 'json')
                    print(90 * '~')
                    print(f'{json_path} : {index}')
                    print(40 * '-' + ' EXPECTED ' + 40 * '-')
                    print(json.dumps(json_, indent=2))
                    print(40 * '+' + ' RECEIVED ' + 40 * '+')
                    print(json.dumps(json_result, indent=2))
                    print(90 * '~')
                    raise
    # set test case class name
    TestCase.__name__ = class_name
    TestCase.__qualname__ = '.'.join(TestCase.__qualname__.split('.')[:-1] + [class_name])
    # return generated test case class
    return TestCase('run_test')

def _get_gql_path_list(path):
    if os.path.isfile(path) and path.endswith('.gql'):
        yield path
    elif os.path.isdir(path):
        for entry in os.scandir(path):
            yield from _get_gql_path_list(entry.path)

def generate_testcases(schema, path, base_test_class=DefaultBaseTestCase):
    """
        Iterator to generate all test cases for a schema, given a path.

        `path` can either be a directory that will be recursively searched for `.gql` files,
        or a `.gql` file.

        Each of the `.gql` file will correspond to a yielded test case class, generated
        with `generate_testcase()`.
    """
    for gql_path in sorted(_get_gql_path_list(path)):
        yield generate_testcase(schema, gql_path, base_test_class)

def make_tests_loader(schema, path, base_test_class=DefaultBaseTestCase):
    """
        This method returns a `load_tests` method, useful for loading generated tests
        from a module.

        Parameters have the same meaning as for `generate_testcases()`.

        Example:

        ```python
        from easy_graphql_server import Schema
        from easy_graphql_server.testing import make_tests_loader

        schema = Schema()

        load_tests = make_tests_loader(schema, 'path/to/graphql/test/data')
        ```
    """
    def load_tests(loader, tests, ignore): # pylint: disable=W0613 # Unused argument 'loader', 'ignore'
        path_ = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', path)
        for test in generate_testcases(schema, path_, base_test_class):
            tests.addTest(test)
        return tests
    return load_tests
