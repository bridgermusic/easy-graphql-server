import os
import pathlib
import json

import django.test
import django.contrib.auth
from django.conf import settings

from easy_graphql_server.testing import make_tests_loader

from .django import schema1, schema2, schema3
from .django.models import populate_database


DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), 'schemas/django/docs')
TESTS_PATH = os.getenv('EASY_GRAPHQL_SERVER_TESTS_PATH', DEFAULT_TESTS_PATH)
ENDPOINT_URL = '/graphql'


class BaseTestCase(django.test.TransactionTestCase):
    reset_sequences = True
    databases = ['default']

    def setUp(self):
        self.tearDown()

    def get_or_create_user(self, username):
        data = {'username': username}
        if 'staff' in username:
            data['is_staff'] = True
        if 'admin' in username:
            data['is_superuser'] = True
        user_model = django.contrib.auth.get_user_model()
        try:
            user = user_model.objects.get(username = username)
        except user_model.DoesNotExist:
            user, created = django.contrib.auth.get_user_model().objects.get_or_create(**data)
            user.set_password(settings.DEFAULT_USER_PASSWORD)
            user.save()
        return user


load_tests = make_tests_loader(
    schemata = (schema1, schema2, schema3),
    path = TESTS_PATH,
    base_test_class = BaseTestCase,
)


class DjangoGraphqlHttpTest(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        populate_database()

    def _get_http_client(self, username = None):
        http_client = django.test.Client(HTTP_USER_AGENT='Mozilla/5.0')
        if username is not None:
            self.get_or_create_user(username)
            http_client.login(
                username = username,
                password = settings.DEFAULT_USER_PASSWORD
            )
        return http_client

    def _request_graphql_endpoint(self, data, username=None):
        return self._get_http_client(username = username).post(
            path = ENDPOINT_URL,
            data = json.dumps(data),
            content_type = 'application/json',
        )

    def test_endpoint(self):
        http_client = self._get_http_client()
        # ensure only POST method can be performed
        for method in ('delete', 'patch', 'put'):
            response = getattr(http_client, method)(ENDPOINT_URL)
            self.assertEqual(response.status_code, 405)
        # try to send empty request body
        response = http_client.post(ENDPOINT_URL, )
        self.assertEqual(response.status_code, 400)
        # try to send properly formatted JSON, with wrong data in it
        response = self._request_graphql_endpoint({})
        self.assertEqual(response.status_code, 400)
        response = self._request_graphql_endpoint({'query': []})
        self.assertEqual(response.status_code, 400)
        # try to send an empty query
        response = self._request_graphql_endpoint({'query': ''})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['errors'][0]['message'], 'Syntax Error: Unexpected <EOF>.')
        # try to send a proper query
        response = self._request_graphql_endpoint({'query': '''
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
        self.assertTrue(response.headers['Content-Type'].startswith('application/json'))
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

    def test_authentication(self):
        # regular user
        response = self._request_graphql_endpoint({'query': '''
            query {
                me {
                    id
                    username
                    is_superuser
                    is_staff
                }
            }
        '''}, username='test@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': {'me': {
            'id': 457, 'username': 'test@example.com', 'is_staff': False, 'is_superuser': False}
        }, 'errors': None})
        # staff user
        response = self._request_graphql_endpoint({'query': '''
            query {
                me {
                    id
                    username
                    is_superuser
                    is_staff
                }
            }
        '''}, username='staff@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': {'me': {
            'id': 458, 'username': 'staff@example.com', 'is_staff': True, 'is_superuser': False}
        }, 'errors': None})
        # super user
        response = self._request_graphql_endpoint({'query': '''
            query {
                me {
                    id
                    username
                    is_superuser
                    is_staff
                }
            }
        '''}, username='admin@example.com')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'data': {'me': {
            'id': 459, 'username': 'admin@example.com', 'is_staff': False, 'is_superuser': True}
        }, 'errors': None})

    def test_graphiql(self):
        response = self._get_http_client().get(
            path = ENDPOINT_URL,
            content_type = 'application/json',
            HTTP_ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        graphiql_page_path = pathlib.Path(__file__).parent.parent / 'src/easy_graphql_server/webserver/static/graphiql.html'
        self.assertEqual(response.content.decode(), open(graphiql_page_path, 'rt').read())
