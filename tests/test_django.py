import os
import json

import django.test

from easy_graphql_server.testing import make_tests_loader

from .schemas.django.graphql import schema
from .schemas.django.models import populate_database


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'schemas/django/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', DEFAULT_TESTS_PATH)
ENDPOINT_URL = '/graphql'


class TestCase(django.test.TransactionTestCase):
    reset_sequences = True
    databases = ['default']

    def setUp(self):
        self.tearDown()


class DjangoGraphqlHttpTest(TestCase):

    def setUp(self):
        self.tearDown()
        populate_database()

    @staticmethod
    def get_http_client():
        http_client = django.test.Client(HTTP_USER_AGENT='Mozilla/5.0')
        return http_client

    @classmethod
    def request_graphql_endpoint(cls, data):
        return cls.get_http_client().post(
            path = ENDPOINT_URL,
            data = json.dumps(data),
            content_type = 'application/json',
        )

    def test_endpoint(self):
        http_client = self.get_http_client()
        # ensure only POST method can be performed
        for method in ('get', 'delete', 'patch', 'put'):
            response = getattr(http_client, method)(ENDPOINT_URL)
            self.assertEqual(response.status_code, 405)
        # try to send empty request body
        response = http_client.post(ENDPOINT_URL, )
        self.assertEqual(response.status_code, 400)
        # try to send properly formatted JSON, with wrong data in it
        response = self.request_graphql_endpoint({})
        self.assertEqual(response.status_code, 400)
        response = self.request_graphql_endpoint({'query': []})
        self.assertEqual(response.status_code, 400)
        # try to send an empty query
        response = self.request_graphql_endpoint({'query': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['errors'][0]['message'], 'Syntax Error: Unexpected <EOF>.')
        # try to send a proper query
        response = self.request_graphql_endpoint({'query': '''
            query {
                person (id: 1) {
                    first_name
                    last_name
                }
                people (first_name__icontains: "ren") {
                    id
                    first_name
                    last_name
                }
            }
        '''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'errors': None, 'data': {
            'people': [
                {'first_name': 'Karen', 'id': 177, 'last_name': 'Evans'},
                {'first_name': 'Lauren', 'id': 199, 'last_name': 'Pennington'},
                {'first_name': 'Lauren', 'id': 212, 'last_name': 'Ayala'},
                {'first_name': 'Renee', 'id': 222, 'last_name': 'Gutierrez'},
                {'first_name': 'Brenda', 'id': 356, 'last_name': 'Garcia'},
                {'first_name': 'Karen', 'id': 389, 'last_name': 'Wilson'}],
            'person':
                {'first_name': 'David', 'last_name': 'Nichols'}
        }})

load_tests = make_tests_loader(
    schema = schema,
    path = TESTS_PATH,
    base_test_class = TestCase,
)
