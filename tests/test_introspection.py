import pytest

from easy_graphql_server import introspection


class IntrospectionTestClass:
    @staticmethod
    def method1(a, b, c=1, **kwargs):
        pass

    @classmethod
    def method2(a, b, c=1, **kwargs):
        pass

    def method3(self, a, b, c=1, **kwargs):
        pass


class Klass:
    a = 4
    b = 12

    def __init__(self, a, b, c=1):
        pass

    def c(self, *args, **kwargs):
        pass


class A(Klass):
    pass


class B(Klass):
    pass


class C(B):
    pass


@pytest.mark.parametrize(
    "input_class,exclude,expected_output",
    [
        pytest.param(Klass, None, {A, B, C}, id="with-subclassess"),
        pytest.param(Klass, {B}, {A}, id="exclude-subclasses"),
    ],
)
def test_get_subclasses(input_class, exclude, expected_output):
    assert (
        set(introspection.get_subclasses(input_class, exclude=exclude))
        == expected_output
    )


@pytest.mark.parametrize(
    "class_obj, method_name, exclude, expected_output",
    [
        pytest.param(
            IntrospectionTestClass,
            "method1",
            None,
            {"a": True, "b": True, "c": False},
            id="introspection-args-method1",
        ),
        pytest.param(
            IntrospectionTestClass,
            "method1",
            ("a",),
            {"b": True, "c": False},
            id="introspection-args-method1-exclude",
        ),
        pytest.param(
            Klass,
            None,
            ("self", "a"),
            {"b": True, "c": False},
            id="introspection-on-class",
        ),
    ],
)
def test_get_method_arguments(class_obj, method_name, exclude, expected_output):
    method = getattr(class_obj, method_name) if method_name is not None else class_obj
    assert (
        introspection.get_method_arguments(method=method, exclude=exclude)
        == expected_output
    )


@pytest.mark.parametrize(
    "class_obj, expected_dictionary",
    [
        pytest.param(
            Klass,
            {"a": 4, "b": 12},
        ),
    ],
)
def test_get_public_class_attributes(class_obj, expected_dictionary):
    attributes = introspection.get_public_class_attributes(class_obj)
    for key, value in expected_dictionary.items():
        assert attributes[key] == value
