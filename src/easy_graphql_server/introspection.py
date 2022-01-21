"""
    Useful tools for introspection, used internally.
"""

import inspect


def get_subclasses(cls, exclude=None):
    """
        Get subclasses of class, excluding itself.
    """
    assert inspect.isclass(cls)
    if exclude is None:
        exclude = set()
    exclude.add(cls)
    for subclass in cls.__subclasses__():
        if subclass not in exclude:
            yield subclass
            exclude.add(subclass)
            yield from get_subclasses(subclass, exclude)


def get_method_arguments(method, exclude=None):
    """
        Return the method's argument, associated with a boolean describing whether
        or not the given argument is required.
    """
    signature = inspect.getargspec(method)
    result = {
        arg: len(signature.args) - i > len(signature.defaults)
        for i, arg in enumerate(signature.args)
    }
    if exclude:
        for arg in exclude:
            result.pop(arg)
    return result

def get_public_class_attributes(cls):
    """
        Retrieve the attribute names of a class that do not have a leading underscore.
    """
    return {
        attribute: getattr(cls, attribute)
        for attribute in dir(cls)
        if attribute[0] != '_'
    }
