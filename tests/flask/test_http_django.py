from .django.base_django_test import BaseDjangoTest as DjangoBaseDjangoTest
from ._base_http_test import BaseHttpTest


class DjangoHttpTest(DjangoBaseDjangoTest, BaseHttpTest):

    endpoint_url = '/graphql-methods'
