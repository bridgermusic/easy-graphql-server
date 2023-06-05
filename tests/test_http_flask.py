from ._base_http_test import BaseHttpTest
from .flask.base_flask_test import BaseFlaskTest


class FlaskHttpTest(BaseFlaskTest, BaseHttpTest):
    endpoint_url = "/graphql-methods"
