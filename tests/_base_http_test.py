import unittest
import pathlib
import json


class BaseHttpTest(unittest.TestCase):

    class HttpResponse:
        def __init__(self, data, code, headers):
            try:
                self.data = json.loads(data)
            except json.decoder.JSONDecodeError:
                self.data = data
            self.code = code
            self.headers = headers

    def request(self, method, path, data=None, headers=None, username=None):
        raise NotImplementedError()

    def request_graphql_endpoint(self, data, username=None):
        return self.request(
            method = 'post',
            path = self.endpoint_url,
            data = data,
            username = username,
        )

    def test_endpoint_forbidden_methods(self):
        # ensure only GET and POST method can be performed
        for method in ('delete', 'patch', 'put'):
            response = self.request(method, self.endpoint_url)
            self.assertEqual(response.code, 405)

    def test_endpoint_get(self):
        # try to send empty request
        response = self.request('get', self.endpoint_url)
        self.assertEqual(response.code, 400)
        # try to send wrong data
        response = self.request('get', self.endpoint_url, {'query': []})
        self.assertEqual(response.code, 400)
        # try to send an empty query
        response = self.request('get', self.endpoint_url, {'query': ''})
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data['errors'][0]['message'], 'Syntax Error: Unexpected <EOF>.')

    def test_endpoint_post(self):
        # try to send empty request body
        response = self.request('post', self.endpoint_url)
        self.assertEqual(response.code, 400)
        # try to send properly formatted JSON, with wrong data in it
        response = self.request_graphql_endpoint({})
        self.assertEqual(response.code, 400)
        response = self.request_graphql_endpoint({'query': []})
        self.assertEqual(response.code, 400)
        # try to send an empty query
        response = self.request_graphql_endpoint({'query': ''})
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data['errors'][0]['message'], 'Syntax Error: Unexpected <EOF>.')
        # try to send a proper query
        response = self.request_graphql_endpoint({'query': '''
            query {
                dummy_retrieve (input_identifier: 1) {
                    output_identifier
                    output_name
                }
                dummy_collection_input (max_index: 2, collection: [{value: 3.14}, {value: 2.72}]) {
                    sum
                }
                dummy_collection_output (max_index: 3) {
                    max_index
                    collection {
                        index
                        identifier
                    }
                }
            }
        '''})
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data, {'data': {
            'dummy_retrieve':
                {'output_identifier': 1, 'output_name': 'dummy_1'},
            'dummy_collection_input':
                {'sum': 5.86},
            'dummy_collection_output':
                {'max_index': 3, 'collection': [
                    {'index': 0, 'identifier': 's0'},
                    {'index': 1, 'identifier': 's1'},
                    {'index': 2, 'identifier': 's2'},
                ]},
        }})

    def test_authentication(self):
        # regular user
        response = self.request_graphql_endpoint({'query': '''
            query {
                me {
                    username
                }
            }
        '''}, username='test@example.com')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data, {'data': {'me': {'username': 'test@example.com'}}})
        # staff user
        response = self.request_graphql_endpoint({'query': '''
            query {
                me {
                    id
                    username
                    is_superuser
                    is_staff
                }
            }
        '''}, username='staff@example.com')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data, {'data': {'me': {
            'id': 2, 'username': 'staff@example.com', 'is_staff': True, 'is_superuser': False}
        }})
        # super user
        response = self.request_graphql_endpoint({'query': '''
            query {
                me {
                    id
                    username
                    is_superuser
                    is_staff
                }
            }
        '''}, username='admin@example.com')
        self.assertEqual(response.code, 200)
        self.assertEqual(response.data, {'data': {'me': {
            'id': 3, 'username': 'admin@example.com', 'is_staff': False, 'is_superuser': True}
        }})

    def test_graphiql(self):
        response = self.request(
            method = 'get',
            path = self.endpoint_url,
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9'},
        )
        self.assertEqual(response.code, 200)
        self.assertTrue(response.headers['Content-Type'].startswith('text/html'))
        graphiql_page_path = pathlib.Path(__file__).parent.parent / 'src/easy_graphql_server/webserver/static/graphiql.html'
        with open(graphiql_page_path, 'rt') as graphiql_page_file:
            self.assertEqual(response.data.decode(), graphiql_page_file.read())
