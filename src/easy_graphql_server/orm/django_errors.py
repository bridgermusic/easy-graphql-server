import inspect

from .. import exceptions


def reraise_django_validation_error(graphql_path, exception):

    def serialize(issue, path, field_name=None):
        if hasattr(issue, 'error_dict'):
            for field, errors in issue.error_dict.items():
                for error in errors:
                    yield from serialize(error, path, field)
        else:
            for error in issue.error_list:
                # extract & format params
                params = getattr(error, 'params', None) or {}
                for key in list(params.keys()):
                    if isinstance(params[key], (str, int, float, list, dict)):
                        continue
                    if isinstance(params[key], (tuple, set)):
                        params[key] = list(params[key])
                    elif inspect.isclass(params[key]):
                        params[key] = params[key].__name__
                    else:
                        params[key] = str(params[key])
                # extract & format message
                message = error.message
                if message and error.params:
                    message %= params
                # yield one serialized error
                yield {
                    'path': path + [field_name] if field_name else path,
                    'message': str(message),
                    'params': getattr(error, 'params', {}),
                    'code': getattr(error, 'code', None),
                }
    issues = list(serialize(exception, graphql_path))
    raise exceptions.ValidationError(issues) from exception
