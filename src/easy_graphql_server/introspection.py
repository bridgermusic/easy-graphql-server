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
    signature = inspect.getfullargspec(method)
    args_count = len(signature.args) if signature.args else 0
    default_args_count = len(signature.defaults) if signature.defaults else 0
    result = {
        arg: args_count - i > default_args_count
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

def validate_class_attributes_against_method_arguments(cls, method,
        excluded_arguments=None, message=''):
    """
        Check if the public attributes of a class can be used as arguments for a method
    """
    attributes = get_public_class_attributes(cls)
    arguments = get_method_arguments(method, excluded_arguments)
    required_arguments = set(argument for argument, required in arguments.items() if required)
    for required_argument in required_arguments:
        if required_argument not in attributes:
            raise ValueError(f'Attribute `{required_argument}` should be present on '
                f'class `{cls}`{message}')
    for attribute in attributes:
        if attribute not in arguments:
            raise ValueError(f'Invalid attribute `{attribute}` for class `{cls}`{message}; '
                'consider making it private with a leading underscore')


def is_instance_or_subclass(thing, klass):
    """
        Check if a thing is an instance or subclass of a given class (or set of classes)
    """
    return isinstance(thing, klass) or (inspect.isclass(thing) and issubclass(thing, klass))
