import json

import django.contrib.auth
from django.conf import settings


class BaseDjangoTest(django.test.TransactionTestCase):
    reset_sequences = True
    databases = ['default']

    def setUp(self):
        self.maxDiff = None
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
            user = django.contrib.auth.get_user_model()(**data)
            user.set_password(settings.DEFAULT_USER_PASSWORD)
            user.save()
        return user

    def _get_http_client(self, username=None):
        http_client = django.test.Client(HTTP_USER_AGENT='Mozilla/5.0')
        if username is not None:
            self.get_or_create_user(username)
            http_client.login(
                username = username,
                password = settings.DEFAULT_USER_PASSWORD
            )
        return http_client

    def request(self, method, path, data=None, headers=None, username=None):
        method = method.lower()
        client = self._get_http_client(username=username)
        client_method = getattr(client, method)
        # initialize arguments
        kwargs = {
            'path': path,
        }
        # data
        if data:
            if method != 'get':
                kwargs['content_type'] = 'application/json'
            kwargs['data'] = data
        # headers
        if headers:
            for key, value in headers.items():
                kwargs['HTTP_' + key.upper().replace('-', '_')] = value
        # result
        response = client_method(**kwargs)
        return self.HttpResponse(
            data = response.content,
            code = response.status_code,
            headers = response.headers,
        )
