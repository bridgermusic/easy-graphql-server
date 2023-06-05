from easy_graphql_server import ExposedMutation, ExposedQuery, Required, Schema


class DummyDoubleMutation(ExposedMutation):
    name = "dummy_double"
    input_format = {
        "input_text": Required(str),
        "input_number": float,
    }
    output_format = {
        "output_text": str,
        "output_number": float,
    }

    @staticmethod
    def method(authenticated_user=None, input_text="", input_number=0.0):
        return {
            "output_text": 2 * input_text,
            "output_number": 2 * input_number,
        }


class DummyDoubleQuery(ExposedQuery):
    name = "dummy_retrieve"
    input_format = {
        "input_identifier": Required(int),
    }
    output_format = {
        "output_identifier": int,
        "output_name": str,
    }

    @staticmethod
    def method(input_identifier):
        return {
            "output_identifier": input_identifier,
            "output_name": f"dummy_{input_identifier}",
        }


class DummyCollectionInput(ExposedQuery):
    name = "dummy_collection_input"
    input_format = {"max_index": int, "collection": [{"value": float}]}
    output_format = {"sum": float}

    @staticmethod
    def method(max_index, collection=None):
        return {
            "sum": sum(item["value"] for item in collection[: max_index + 1])
            if (collection and max_index >= 0)
            else None
        }


class DummyCollectionOutput(ExposedQuery):
    name = "dummy_collection_output"
    input_format = {
        "max_index": Required(int),
    }
    output_format = {
        "max_index": int,
        "collection": [{"index": int, "identifier": str}],
    }

    @staticmethod
    def method(max_index):
        return {
            "max_index": max_index,
            "collection": [
                {
                    "index": i,
                    "identifier": f"s{i}",
                }
                for i in range(max_index)
            ],
        }


class DummyUser(ExposedQuery):
    name = "me"
    output_format = {
        "username": str,
    }
    pass_authenticated_user = True

    @staticmethod
    def method(authenticated_user):
        return authenticated_user.username


schema = Schema(debug=True)
schema.expose(DummyDoubleMutation)
schema.expose(DummyDoubleQuery)
schema.expose(DummyCollectionInput)
schema.expose(DummyCollectionOutput)
schema.expose(DummyUser)
