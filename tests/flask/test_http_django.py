from .._base_http_test import BaseHttpTest
from ..testapp.base_django_test import BaseDjangoTest as DjangoBaseDjangoTest


class DjangoHttpTest(DjangoBaseDjangoTest, BaseHttpTest):
    endpoint_url = "/graphql-methods"
