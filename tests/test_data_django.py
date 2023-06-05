import json
import os

import pytest
from model_bakery import baker

try:
    from easy_graphql_server.testing import (
        EgsError,
        EgsOutputFactory,
        make_tests_loader,
    )
except ImportError:
    print("Importing  loader failed")

try:
    from .testapp import schema1, schema2, schema3
except ImportError:
    print("Importing  schema failed")

from .testapp.base_django_test import BaseDjangoTest

# DEFAULT_TESTS_PATH = os.path.join(os.path.dirname(__file__), "testapp/docs")
# TESTS_PATH = os.getenv("EASY_GRAPHQL_SERVER_TESTS_PATH", DEFAULT_TESTS_PATH)


# load_tests = make_tests_loader(
#    schemata=(schema1.schema, schema2.schema, schema3.schema),
#   path=TESTS_PATH,
#    base_test_class=BaseDjangoTest,
# )


_GQL_QUERY = """
        mutation {
        create_person (
            first_name: "Michel"
            last_name: "Thisfakenameiswaaaytoolongandshoulddefinitelyberejectedbecauseofit"
            username: "michel.dupont@example.com"
        ) {
            id
            first_name
            last_name
        }
        }
"""

_MUTATION_VALIDATION_ERROR = {
    "type": "VALIDATION",
    "payload": [
        {
            "path": ["mutation", "create_person", "last_name"],
            "message": "Ensure this value has at most 64 characters (it has 66).",
            "params": {
                "limit_value": 64,
                "show_value": 66,
                "value": "Thisfakenameiswaaaytoolongandshoulddefinitelyberejectedbecauseofit",
            },
            "code": "max_length",
        },
    ],
}


_egs_validation_error = EgsError(
    **{
        "message": json.dumps(_MUTATION_VALIDATION_ERROR),
        "locations": [{"line": 3, "column": 9}],
        "path": ["create_person"],
    }
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "schema, query, expected_output",
    [
        pytest.param(
            schema1.schema,
            _GQL_QUERY,
            EgsOutputFactory.bake_egs_output(
                data={"create_person": None},
                errors=[_egs_validation_error],
            ),
            id="test-validation-error",
        )
    ],
)
def test_fail_django_user_authentication(
    django_auth_user, schema, query, expected_output
):
    _computed_output = schema.execute(
        query=query, authenticated_user=django_auth_user, serializable_output=True
    )
    assert _computed_output == expected_output
