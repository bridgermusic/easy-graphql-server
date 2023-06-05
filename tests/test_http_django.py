from ._base_http_test import BaseHttpTest
from .testapp.base_django_test import BaseDjangoTest


class DjangoHttpTest(BaseDjangoTest, BaseHttpTest):
    endpoint_url = "/graphql-methods"
