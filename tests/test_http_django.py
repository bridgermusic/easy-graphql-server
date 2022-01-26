from .django.base_django_test import BaseDjangoTest
from ._base_http_test import BaseHttpTest


class DjangoHttpTest(BaseDjangoTest, BaseHttpTest):

    endpoint_url = '/graphql-methods'
