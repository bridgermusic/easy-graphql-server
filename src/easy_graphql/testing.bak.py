"""
    Data-driven tests for schema defined with `easy_graphql.Schema`.
"""


import os
import re
import json
import importlib.util

from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.conf import settings


def get_or_create_user(username, is_superuser=False, is_staff=False):
    user_model = get_user_model()
    users = list(user_model.objects.filter(username=username))
    if len(users) > 0:
        user = users[0]
    else:
        user_data = dict(
            username = username,
            is_staff = is_superuser or is_staff,
            is_rightholder = not (is_superuser or is_staff),
        )
        if is_superuser:
            user = user_model.objects.create_superuser(**user_data)
        else:
            user = user_model.objects.create_user(**user_data)
        user.save()
    return user


def make_user(username=None):
    if username is None:
        user = None
    elif 'admin' in username:
        user = get_or_create_user(username, is_superuser=True)
    elif 'staff' in username:
        user = get_or_create_user(username, is_staff=True)
    else:
        user = get_or_create_user(username)
    if user is None and username is not None:
        raise Exception('TEST ERROR: USER COULD NOT BE CREATED')
    return user


def generate_testcase(schema, input_path, output_path):
    """
        TODO: check if proper SQL has been generated, see:

        ```python

            from django.db import connection, reset_queries
            import re

            reset_queries()

            EXECUTE_GRAPHQL_QUERIES()

            print()
            print(96*'<')
            for query in list(connection.queries):
                print()
                print(re.sub(r' (SELECT|FROM|LEFT|WHERE)', '\n\\1', query['sql']))
                print()
            print(96*'>')
            print()

            ASSERT_GENERATED_SQL = EXPECTED_SQL
        ```
    """
    # compute test class name
    name = input_path.split('/')[-1].split('.')[0]
    name = re.sub(r'[^\w]+', '_', name).lower()
    # generate test case from files
    class Test(TransactionTestCase):
        reset_sequences = True

        # something very sad: exceptions caught by GraphQL will be displayed,
        # even when the test finally succeeds
        def runTest(self, *args, **kwargs): # pylint: disable=C0103,W0613
            # so we can debug SQL queries
            settings.DEBUG = True
            # initialize input & output
            with open(input_path, 'rt', encoding='utf-8') as input_file:
                input_graphql_list = re.split(r'\n\s*;\s*\n', input_file.read())
            with open(output_path, 'rt', encoding='utf-8') as output_file:
                try:
                    expected_output_list = [
                        json.loads(expected_output)
                        for i, expected_output
                        in enumerate(re.split(r'\n\s*;\s*\n', output_file.read()))
                    ]
                except json.decoder.JSONDecodeError as error:
                    raise ValueError(f'Cannot decode JSON in `{output_path}`: '
                        '{error}\n{expected_output}') from error
            # execute setup if present
            setup_file_path = re.sub(r'\.json$', '.setup.py', output_path)
            if os.path.isfile(setup_file_path):
                spec = importlib.util.spec_from_file_location('module.name', setup_file_path)
                setup_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(setup_module)
            # actually run the test(s)
            input_output_list = zip(input_graphql_list, expected_output_list)
            for index, (input_graphql, expected_output) in enumerate(input_output_list):
                # get/create a fake user for the request if asked by the #USER directive
                username_match = re.search(r'(?:^|\n)\s*#\s*USER\s*:\s*([^\s]+)', input_graphql)
                username = username_match.group(1) if username_match else None
                user = make_user(username)
                # compute output
                output = schema.execute(input_graphql, authenticated_user=user)
                # show the difference, no matter how long
                self.maxDiff = None # pylint: disable=C0103
                try:
                    self.assertEqual(expected_output, output.formatted)
                except:
                    print(70*'~')
                    print(f'{output_path} : {index}')
                    print(70*'-')
                    print(json.dumps(expected_output, indent=4))
                    print(70*'+')
                    print(json.dumps(output.formatted, indent=4))
                    print(70*'~')
                    raise
    # set test case class name
    Test.__name__ = name
    Test.__qualname__ = '.'.join(Test.__qualname__.split('.')[:-1] + [name])
    # return generated test case class
    return Test
