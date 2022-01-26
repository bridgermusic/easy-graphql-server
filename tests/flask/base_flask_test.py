import unittest
import json

import flask_login

from .app import app
from .login import add_user, get_user


class BaseFlaskTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.tearDown()

    def get_or_create_user(self, username):
        data = {'username': username}
        if 'staff' in username:
            data['is_staff'] = True
        if 'admin' in username:
            data['is_superuser'] = True
        user = get_user(username)
        if user is None:
            user = add_user(**data)
        return user

    def request(self, method, path, data=None, headers=None, username=None):
        method = method.lower()
        with app.test_client() as client:
            # user
            if username is not None:
                authenticated_user = self.get_or_create_user(username)
                @app.login_manager.request_loader
                def load_user_from_request(request):
                    return authenticated_user
            # HTTP method
            client_method = getattr(client, method)
            # initialize arguments
            kwargs = {}
            # data
            if data:
                if method == 'get':
                    kwargs['query_string'] = data
                else:
                    kwargs['json'] = data
            # headers
            if headers:
                kwargs['headers'] = headers
            # result
            response = client_method(path, **kwargs)
            return self.HttpResponse(
                data = response.data,
                code = response.status_code,
                headers = response.headers,
            )
