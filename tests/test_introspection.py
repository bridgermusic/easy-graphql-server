import inspect
import unittest

from easy_graphql_server import introspection


class IntrospectionTest(unittest.TestCase):

    @staticmethod
    def method1(a, b, c=1, **kwargs): pass

    @classmethod
    def method2(a, b, c=1, **kwargs): pass

    def method3(a, b, c=1, **kwargs): pass

    class Klass:
        a = 4
        b = 12
        def __init__(self, a, b, c=1): pass
        def c(self, *args, **kwargs): pass

    class A(Klass): pass
    class B(Klass): pass
    class C(B): pass

    def test_get_subclasses(self):
        subclasses = set(introspection.get_subclasses(self.Klass))
        self.assertEqual(subclasses, {self.A, self.B, self.C})
        subclasses = set(introspection.get_subclasses(self.Klass, {self.B}))
        self.assertEqual(subclasses, {self.A,})

    def test_get_method_arguments(self):
        methods = (self.method1, self.method2, self.method3)
        for method in methods:
            arguments = introspection.get_method_arguments(method=method)
            self.assertEqual(arguments, {'a': True, 'b': True, 'c': False})
            arguments = introspection.get_method_arguments(method=method, exclude=('a',))
        arguments = introspection.get_method_arguments(method=self.Klass, exclude=('self', 'a'))
        self.assertEqual(arguments, {'b': True, 'c': False})

    def test_get_public_class_attributes(self):
        attributes = introspection.get_public_class_attributes(self.Klass)
        self.assertEqual(set(attributes.keys()), set('abc'))
        self.assertEqual(attributes['a'], 4)
        self.assertEqual(attributes['b'], 12)
