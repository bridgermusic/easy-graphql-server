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
            Base test case class, associated with a `.gql` file.
        """
        @staticmethod
        def _replace_extension(path, new_extension):
            return re.sub(r'\.\w+$', f'.{new_extension}', path)
        def _iterate_data(self, graphql_path):
            # load GraphQL input
            with open(graphql_path, 'rt', encoding='utf-8') as graphql_file:
                graphql_list = re.split(r'\n\s*;\s*\n', graphql_file.read())
            # load JSON output
            json_path = self._replace_extension(graphql_path, 'json')
            with open(json_path, 'rt', encoding='utf-8') as json_file:
                json_data = json_file.read()
                json_data = re.sub(r'(^|\n)//[^\n]+', r'\1', json_data)
                json_list = []
                for i, expected_output in enumerate(re.split(r'\n\s*;\s*\n', json_data)):
                    try:
                        json_list.append(
                            json.loads(expected_output)
                        )
                    except json.decoder.JSONDecodeError as error:
                        raise ValueError(f'Cannot decode JSON in `{json_path}`[{i}]: '
                            '{error}\n{expected_output}') from error
            # load generated SQL
            sql_path = self._replace_extension(graphql_path, 'sql')
            if os.path.isfile(sql_path):
                with open(sql_path, 'rt', encoding='utf-8') as sql_file:
                    sql_list = sql_file.read().split(';;')
            else:
                sql_list = []
            sql_list += (len(graphql_list) - len(sql_list)) * ['']
            # return iterator
            for i, (graphql, json_, sql) in enumerate(zip(graphql_list, json_list, sql_list)):
                # handle USER directive
                username_match = re.search(r'(?:^|\n)\s*#\s*USER\s*:\s*([^\s]+)', graphql)
                username = username_match.group(1) if username_match else None
                if username is None:
                    user = None
                elif not hasattr(self, 'get_or_create_user'):
                    raise AttributeError(
                        'To use the `USER` directive, you must implement a `get_or_create_user(username) '
                        'method` on a base class for test cases, and pass this class as a '
                        '`base_test_class` parameter.')
                else:
                    user = self.get_or_create_user(username)
                # yield expected data
                yield i, (user, graphql, json_, sql.strip())
        @staticmethod
        def show_diff(path, index, expectation, reality, input_=None):
            """
                Show difference between expected and actual result.
            """
            print(90 * '~')
            print(f'{path} : {index}')
            if input_:
                print(40 * '~' + ' INPUT IS ' + 40 * '~')
                print(input_)
            print(40 * '-' + ' EXPECTED ' + 40 * '-')
            print(expectation)
            print(40 * '+' + ' RECEIVED ' + 40 * '+')
            print(reality)
            print(90 * '~')
        def run_test(self, *args, **kwargs): # pylint: disable=unused-argument
            """
                Run data-driven test
            """
            # show the difference, no matter how long
            self.maxDiff = None # pylint: disable=invalid-name
            # so we can debug SQL queries
            if django_environment:
                from django.conf import settings # pylint: disable=import-outside-toplevel
                settings.DEBUG = True
            # execute setup script if present
            setup_script_path = self._replace_extension(graphql_path, 'setup.py')
            if os.path.isfile(setup_script_path):
                spec = importlib.util.spec_from_file_location(
                    f'setup_{class_name}', setup_script_path)
                setup_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(setup_module)
            # actually run the test step(s)
            for index, (user, graphql, json_, sql) in self._iterate_data(graphql_path):
                # clear sql log
                if sql:
                    schema.check()
                    for orm_model_manager_class in set(schema.orm_model_manager_classes):
                        orm_model_manager_class.start_sql_log()
                # compute output
                json_result = schema.execute(
                    query = graphql,
                    authenticated_user = user,
                    serializable_output = True,
                )
                try:
                    # compare it with what was expected
                    self.assertEqual(json_, json_result)
                except:
                    # if different, show pretty output and re-raise assert exception
                    self.show_diff(
                        path = self._replace_extension(graphql_path, 'json'),
                        index = index,
                        expectation = json.dumps(json_, indent=2),
                        reality = json.dumps(json_result, indent=2),
                        input_ = re.sub(r'(?:(?<=\n)|^)[ \t]*#(?![ \t]*USER)[^\n]*(?:\n|$)', '', graphql),
                    )
                    raise
                # check SQL also (when provided)
                if sql:
                    sql_result_list = []
                    for orm_model_manager_class in set(schema.orm_model_manager_classes):
                        sql_result_list += orm_model_manager_class.get_sql_log()
                    sql_result = '\n;\n'.join(sql_result_list)
                    try:
                        # compare it with what was expected
                        self.assertEqual(sql, sql_result)
                    except:
                        self.show_diff(
                            path = self._replace_extension(graphql_path, "sql"),
                            index = index,
                            expectation = sql,
                            reality = sql_result,
                        )
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

def make_tests_loader(schemata, path, base_test_class=DefaultBaseTestCase):
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
    if not isinstance(schemata, (tuple, list, set)):
        schemata = [schemata]
    def load_tests(loader, tests, ignore): # pylint: disable=unused-argument
        path_ = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', path)
        for schema in schemata:
            for test in generate_testcases(schema, path_, base_test_class):
                tests.addTest(test)
        return tests
    return load_tests
