from .flask.base_flask_test import BaseFlaskTest
from ._base_http_test import BaseHttpTest


class FlaskHttpTest(BaseFlaskTest, BaseHttpTest):

    endpoint_url = '/graphql-methods'
