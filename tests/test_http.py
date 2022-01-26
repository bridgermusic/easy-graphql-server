from .django.base_test_case import BaseTestCase as DjangoBaseTestCase
from ._base_http_test import BaseHttpTest


class DjangoHttpTest(DjangoBaseTestCase, BaseHttpTest):

    endpoint_url = '/graphql-methods'
