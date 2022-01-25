import pathlib
import json

import django.test
from django.conf import settings

from .django.base_test_case import BaseTestCase
from .django.models import populate_database
from .django.schema1 import schema


ENDPOINT_URL = '/graphql'


class DjangoGraphqlHttpTest(BaseTestCase):

    def setUp(self):
        BaseTestCase.setUp(self)
        populate_database()
        self.schema_documentation = schema.get_documentation()

    def _get_http_client(self, username=None):
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
        self.assertEqual(response.json(), {'data': {
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
        }})
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
        }})
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
        }})

    def test_graphiql(self):
        response = self._get_http_client().get(
            path = ENDPOINT_URL,
            HTTP_ACCEPT = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        graphiql_page_path = pathlib.Path(__file__).parent.parent / 'src/easy_graphql_server/webserver/static/graphiql.html'
        self.assertEqual(response.content.decode(), open(graphiql_page_path, 'rt').read())

    def _search_schema(self, root=None, **criteria):
        if root is None:
            root = self.schema_documentation
        if isinstance(root, list):
            for item in root:
                yield from self._search_schema(item, **criteria)
        elif isinstance(root, dict):
            if all(key in root and root[key] == value for key, value in criteria.items()):
                yield root
            for key, value in root.items():
                if isinstance(value, (list, dict)):
                    yield from self._search_schema(value, **criteria)

    def _get_from_schema(self, root=None, **criteria):
        for result in self._search_schema(root=root, **criteria):
            return result

    def _get_output_type(self, name):
        for result in self._search_schema(name=name):
            if isinstance(result.get('fields'), list):
                return result

    def _check_gender_type(self, gender_type):
        self.assertEqual(gender_type['kind'], 'ENUM')
        self.assertEqual(gender_type['name'], 'person__gender__enum_type')

    def test_enum_names(self):
        # check gender argument for create_person
        create_person = self._get_from_schema(name='create_person')
        create_person_gender_arg = self._get_from_schema(root=create_person['args'], name='gender')
        self._check_gender_type(create_person_gender_arg['type'])
        # check gender argument for update_person
        update_person = self._get_from_schema(name='update_person')
        update_person_underscore_arg = self._get_from_schema(root=update_person['args'], name='_')
        update_person_underscore_input_type = self._get_from_schema(
            kind = 'INPUT_OBJECT',
            interfaces = None,
            name = update_person_underscore_arg['type']['name'])
        update_person_gender_arg = self._get_from_schema(root=update_person_underscore_input_type, name='gender')
        self._check_gender_type(update_person_gender_arg['type'])
        # check gender argument for create_house
        create_house = self._get_from_schema(name='create_house')
        create_house_tenants_input_type = self._get_from_schema(root=create_house, name='tenants')['type']['ofType']
        create_house_owner_input_type = self._get_from_schema(root=create_house, name='owner')['type']
        for input_type_reference in (create_house_tenants_input_type, create_house_owner_input_type):
            input_type = self._get_from_schema(
                kind = 'INPUT_OBJECT',
                interfaces = None,
                name = input_type_reference['name'])
            gender = self._get_from_schema(root=input_type, name='gender')
            self._check_gender_type(gender['type'])
        # check gender output
        output_types_names = set()
        for method_name in ('person', 'people', 'create_person', 'update_person', 'delete_person'):
            method = self._get_from_schema(name=method_name)
            method_type = method['type']
            if method_type['kind'] == 'LIST':
                method_type = method_type['ofType']
            self.assertEqual(method_type['kind'], 'OBJECT')
            output_types_names.add(method_type['name'])
        self.assertEqual(len(output_types_names), 1)
        for method_name in ('house', 'houses', 'create_house', 'update_house', 'delete_house'):
            method = self._get_from_schema(name=method_name)
            method_type = method['type']
            if method_type['kind'] == 'LIST':
                method_type = method_type['ofType']
            self.assertEqual(method_type['kind'], 'OBJECT')
            method_output_type = self._get_output_type(name=method_type['name'])
            for attribute in ('owner', 'tenants'):
                method_person_output_type = self._get_from_schema(method_output_type, name=attribute)
                method_type = method_person_output_type['type']
                if method_type['kind'] == 'LIST':
                    method_type = method_type['ofType']
                self.assertEqual(method_type['kind'], 'OBJECT')
                output_types_names.add(method_type['name'])
        self.assertEqual(len(output_types_names), 3)
        for output_type_name in output_types_names:
            output_type = self._get_output_type(output_type_name)
            gender = self._get_from_schema(output_type, name='gender')
            self._check_gender_type(gender['type'])
