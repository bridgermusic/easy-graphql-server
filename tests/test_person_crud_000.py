import json

import pytest
from django.contrib.auth import get_user_model
from model_bakery import baker

from easy_graphql_server.testing import EgsError, EgsOutputFactory

from .testapp import schema1


# TODO: test authentication failure


# 01 - Fail Create person Query
_CREATE_PERSON_GQL_QUERY = """
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


_person_last_name_validation_error = EgsError(
    **{
        "message": json.dumps(_MUTATION_VALIDATION_ERROR),
        "locations": [{"line": 3, "column": 13}],
        "path": ["create_person"],
    }
)


# 02 - Success Create person Query with correct last_name
_02_FAILED_CREATE_PERSON_GQL_QUERY = """
        mutation {
            create_person (
                first_name: "Michel"
                last_name: "Dupont"
            ) {
                id
                first_name
                last_name
            }
        }
"""


_MISSING_USERNAME_ARG_MESSAGE = json.dumps(
    {
        "type": "MISSING_ARGUMENT",
        "payload": {
            "parent_type_name": "create_person",
            "expected_argument_name": "username",
            "expected_type": "String!",
            "path": ["mutation", "create_person"],
        },
    }
)

_person_username_validation_error = EgsError(
    **{
        "message": _MISSING_USERNAME_ARG_MESSAGE,
        "locations": [{"line": 3, "column": 13}],
        "path": ["mutation", "create_person"],
    }
)


# 03 - Successfully create person object
_SUCCESS_CREATE_PERSON = """
    mutation {
        create_person (
            first_name: "Michel"
            last_name: "Dupont"
            username: "Random"
        ) {
            id
            first_name
            last_name
        }
    }
"""
_success_create_person_data = {
    "create_person": {"id": 2, "first_name": "Michel", "last_name": "Dupont"}
}


_SCENARIOS = [
    # 01 - Failed to create user - last_name length > 64
    {
        "gql_query": _CREATE_PERSON_GQL_QUERY,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"create_person": None},
            errors=[_person_last_name_validation_error],
        ),
        "auth_required": True,
    },
    # 02 - Failed username is required
    {
        "gql_query": _02_FAILED_CREATE_PERSON_GQL_QUERY,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data=None,
            errors=[_person_username_validation_error],
        ),
        "auth_required": True,
    },
    # 03 - Success create person object
    {
        "gql_query": _SUCCESS_CREATE_PERSON,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data=_success_create_person_data,
            errors=None,
        ),
        "auth_required": True,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "schema, scenarios",
    [pytest.param(schema1.schema, _SCENARIOS, id="create-person-mutation")],
)
def test_ok_create_person(django_auth_user, schema, scenarios):
    for scenario in scenarios:
        _computed_output = schema.execute(
            query=scenario["gql_query"],
            authenticated_user=django_auth_user,
            serializable_output=scenario["auth_required"],
        )
        expected_output = scenario["expected_output"]
        assert _computed_output["data"] == expected_output["data"]

        if "errors" in _computed_output.keys():
            assert _computed_output["errors"] == expected_output["errors"]


# 04 - Query existing person data from db
_GET_EXISTING_PERSON_GQL_QUERY = """
    query {
        person (id: 2) {
            id
            first_name
            last_name
        }
    }
"""

_existing_person_data = {
    "person": {"id": 2, "first_name": "firstTest1", "last_name": "lastTest1"}
}


# 05 - Query non existing person data from db
_GET_UNKOWN_PERSON_GQL_QUERY = """
    query {
        person (id: 1000) {
            id
            first_name
            last_name
        }
    }
"""

_non_existing_person_data = EgsError(
    **{
        "message": json.dumps(
            {"type": "NOT_FOUND", "payload": {"filters": {"id": 1000}}}
        ),
        "locations": [{"line": 3, "column": 9}],
        "path": ["person"],
    }
)

_QUERY_PERSON_SCENARIOS = [
    # 04 - Query existing person
    {
        "gql_query": _GET_EXISTING_PERSON_GQL_QUERY,
        "expected_output": EgsOutputFactory.bake_egs_output(data=_existing_person_data),
        "auth_required": True,
    },
    # 05 - Query non-existing person
    {
        "gql_query": _GET_UNKOWN_PERSON_GQL_QUERY,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"person": None},
            errors=[_non_existing_person_data],
        ),
        "auth_required": True,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "schema, is_existing, scenario",
    [
        pytest.param(
            schema1.schema, True, _QUERY_PERSON_SCENARIOS[0], id="query-existing-person"
        ),
        pytest.param(
            schema1.schema,
            False,
            _QUERY_PERSON_SCENARIOS[1],
            id="query-non-existing-person",
        ),
    ],
)
def test_ok_query_person(
    django_auth_user, person_recipe, schema, is_existing, scenario
):
    if is_existing is True:
        person = baker.make(get_user_model(), **person_recipe)
        person.save()

    _computed_output = schema.execute(
        query=scenario["gql_query"],
        authenticated_user=django_auth_user,
        serializable_output=scenario["auth_required"],
    )
    expected_output = scenario["expected_output"]
    assert _computed_output["data"] == expected_output["data"]

    if "errors" in _computed_output.keys():
        assert _computed_output["errors"] == expected_output["errors"]


# 06 - Fail Update existing person data in db, unexpected argument
_UPDATE_PERSON_GQL_MUTATION_UNEXPECTED = """
    mutation {
        update_person (id: 2, _: {id: 42}) {
            first_name
        }
    }
"""

_unexpected_argument_name = EgsError(
    **{
        "message": json.dumps(
            {
                "type": "UNEXPECTED_ARGUMENT",
                "payload": {
                    "unexpected_argument_name": "id",
                    "parent_type_name": "update_person_____input_type",
                    "path": ["mutation", "update_person", "_", "id"],
                },
            }
        ),
        "locations": [{"line": 3, "column": 35}],
        "path": ["mutation", "update_person", "_", "id"],
    }
)

# 07 - Update existing person data in db
_UPATE_EXISTING_PERSON_GQL_MUTATION = """
    mutation {
      update_person (id: 2, _: {first_name: "Jean-Michel"}) {
        first_name
      }
    }
"""


# 07 - Update existing person data in db
_UPATE_NONEXISTING_PERSON_GQL_MUTATION = """
    mutation {
        update_person (id: 1000, _: {first_name: "Jean-Michel"}) {
            first_name
        }
    }
"""

# NOTE: duplicate
_update_person_not_found = EgsError(
    **{
        "message": json.dumps(
            {"type": "NOT_FOUND", "payload": {"filters": {"id": 1000}}}
        ),
        "locations": [{"line": 3, "column": 9}],
        "path": ["update_person"],
    }
)

# 08 - Delete existing person
_DELETE_EXISTING_PERSON_GQL_MUTATION = """
    mutation {
        delete_person (id: 2) {
            id
            last_name
        }
    }
"""

# 09 - Delete non-existing person
_DELETE_UNKOWN_PERSON_GQL_MUTATION = """
    mutation {
        delete_person (id: 100) {
            id
            first_name
            last_name
        }
    }
"""

_delete_non_existing_person_error = EgsError(
    **{
        "message": json.dumps(
            {"type": "NOT_FOUND", "payload": {"filters": {"id": 100}}}
        ),
        "locations": [{"line": 3, "column": 9}],
        "path": ["delete_person"],
    }
)


_MUTATION_SCENARIOS = [
    # 06 - Update existing person data in db
    {
        "gql_query": _UPDATE_PERSON_GQL_MUTATION_UNEXPECTED,
        "expected_output": EgsOutputFactory.bake_egs_output(
            errors=[_unexpected_argument_name]
        ),
        "auth_required": True,
    },
    # 07 - Update existing person data in db
    {
        "gql_query": _UPATE_EXISTING_PERSON_GQL_MUTATION,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"update_person": {"first_name": "Jean-Michel"}},
        ),
        "auth_required": True,
    },
    # 08 - Update non-existing person data in db
    {
        "gql_query": _UPATE_NONEXISTING_PERSON_GQL_MUTATION,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"update_person": None}, errors=[_update_person_not_found]
        ),
        "auth_required": True,
    },
    # 09 - Delete existing person data in db
    {
        "gql_query": _DELETE_EXISTING_PERSON_GQL_MUTATION,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"delete_person": {"id": 2, "last_name": "lastTest1"}},
        ),
        "auth_required": True,
    },
    # 10 - Delete non-existing person data in db
    {
        "gql_query": _DELETE_UNKOWN_PERSON_GQL_MUTATION,
        "expected_output": EgsOutputFactory.bake_egs_output(
            data={"delete_person": None}, errors=[_delete_non_existing_person_error]
        ),
        "auth_required": True,
    },
]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "schema, is_existing, scenario",
    [
        pytest.param(
            schema1.schema,
            True,
            _MUTATION_SCENARIOS[0],
            id="mutation-update-existing-person-wrong-args",
        ),
        pytest.param(
            schema1.schema,
            True,
            _MUTATION_SCENARIOS[1],
            id="mutation-update-existing-person",
        ),
        pytest.param(
            schema1.schema,
            False,
            _MUTATION_SCENARIOS[2],
            id="mutation-update-non-existing-person",
        ),
        pytest.param(
            schema1.schema,
            True,
            _MUTATION_SCENARIOS[3],
            id="mutation-delete-existing-person",
        ),
        pytest.param(
            schema1.schema,
            False,
            _MUTATION_SCENARIOS[4],
            id="mutation-delete-non-existing-person",
        ),
    ],
)
def test_ok_person_mutations(
    django_auth_user, person_recipe, schema, is_existing, scenario
):
    if is_existing is True:
        person = baker.make(get_user_model(), **person_recipe)
        person.save()

    _computed_output = schema.execute(
        query=scenario["gql_query"],
        authenticated_user=django_auth_user,
        serializable_output=scenario["auth_required"],
    )
    expected_output = scenario["expected_output"]
    assert _computed_output["data"] == expected_output["data"]

    if "errors" in _computed_output.keys():
        assert _computed_output["errors"] == expected_output["errors"]
