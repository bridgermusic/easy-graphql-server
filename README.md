# Easy GraphQL Server

**easy_graphql_server** provides an easy way to expose a database in GraphQL, using ORM models and web frameworks (so far only Django is supported, but SQLAlchemy & Flask will soon come).

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Easy GraphQL Server](#easy-graphql-server)
	- [Usage](#usage)
		- [Expose methods](#expose-methods)
			- [Calling `Schema.expose_query()` and `Schema.expose_mutation()`](#calling-schemaexposequery-and-schemaexposemutation)
			- [Subclassing `Schema.ExposedQuery` and `Schema.ExposedMutation`](#subclassing-schemaexposedquery-and-schemaexposedmutation)
			- [Subclassing `easy_graphql_server.ExposedQuery` and `easy_graphql_server.ExposedMutation`](#subclassing-easygraphqlserverexposedquery-and-easygraphqlserverexposedmutation)
			- [Available options for exposing methods](#available-options-for-exposing-methods)
		- [Expose ORM models](#expose-orm-models)
			- [Calling `Schema.expose_model()`](#calling-schemaexposemodel)
			- [Subclassing `Schema.ExposedModel`](#subclassing-schemaexposedmodel)
			- [Subclassing `easy_graphql_server.ExposedModel`](#subclassing-easygraphqlserverexposedmodel)
			- [Available options for exposing models](#available-options-for-exposing-models)
		- [Perform GraphQL queries](#perform-graphql-queries)
	- [Credits and history](#credits-and-history)
	- [License](#license)

<!-- /TOC -->

**easy_graphql_server** can be installed from PyPI using the built-in pip command:

```bash
pip install easy-graphql-server
```

## Usage

### Expose methods

There are three ways to expose a method in the GraphQL schema.

#### Calling `Schema.expose_query()` and `Schema.expose_mutation()`

```python
import easy_graphql_server as egs

schema = egs.Schema()

schema.expose_query(
    name = 'foo',
    input_format = {
        'input_string': egs.Mandatory(str),
        'input_integer': int,
    },
    output_format = {
        'output_string': str,
        'output_integer': int,
    },
    method = lambda input_string, input_integer=None: {
        'output_string': 2 * input_string,
        'output_integer': None if input_integer is None else 2 * input_integer,
    },
)

_internal_value = 0
def bar_mutation_method(value=None, increment_value=None):
    if value is not None:
        _internal_value = value
    if increment_value is not None:
        _internal_value += increment_value
    return {
        'value': _internal_value,
    }

schema.expose_mutation(
    name = 'bar',
    input_format = {
        'input_string': egs.Mandatory(str),
        'input_integer': int,
    },
    output_format = {
        'output_string': str,
        'output_integer': int,
    },
    method = bar_mutation_method,
)
```

#### Subclassing `Schema.ExposedQuery` and `Schema.ExposedMutation`

```python
import easy_graphql_server as egs

schema = egs.Schema()

class FooQuery(schema.ExposedQuery):
    name = 'foo'
    input_format = {
        'input_string': egs.Mandatory(str),
        'input_integer': int,
    }
    output_format = {
        'output_string': str,
        'output_integer': int,
    }
    @staticmethod
    def method(input_string, input_integer=None):
        return {
            'output_string': 2 * input_string,
            'output_integer': None if input_integer is None else 2 * input_integer,
        }

class BarMutation(schema.ExposedMutation):
    name = 'bar'
    _internal_value = 0
    input_format = {
        'value': int,
        'increment_value': int,
    }
    output_format = {
        'value': int,
    }
    @classmethod
    def method(cls, value=None, increment_value=None):
        if value is not None:
            cls._internal_value = value
        if increment_value is not None:
            cls._internal_value += increment_value
        return {
            'value': cls._internal_value,
        }
```

#### Subclassing `easy_graphql_server.ExposedQuery` and `easy_graphql_server.ExposedMutation`

This is very similar to the previous way.

```python
import easy_graphql_server as egs

class FooQuery(schema.ExposedQuery):
    name = 'foo'
    input_format = {
        'input_string': egs.Mandatory(str),
        'input_integer': int,
    }
    output_format = {
        'output_string': str,
        'output_integer': int,
    }
    @staticmethod
    def method(input_string, input_integer=None):
        return {
            'output_string': 2 * input_string,
            'output_integer': None if input_integer is None else 2 * input_integer,
        }

class BarMutation(schema.ExposedMutation):
    name = 'bar'
    _internal_value = 0
    input_format = {
        'value': int,
        'increment_value': int,
    }
    output_format = {
        'value': int,
    }
    @classmethod
    def method(cls, value=None, increment_value=None):
        if value is not None:
            cls._internal_value = value
        if increment_value is not None:
            cls._internal_value += increment_value
        return {
            'value': cls._internal_value,
        }

schema = egs.Schema()
schema.expose(FooQuery)
schema.expose(BarMutation)
```

#### Available options for exposing methods

The same options can be passed either as class attributes for subclasses of `Schema.ExposedQuery` and `Schema.ExposedMutation`, or as keyword arguments to `Schema.expose_query()` and `Schema.expose_mutation()` methods.

Options for *queries* and *mutations* are the same.

 * `name` is the name under which the method shall be exposed

 * `method` is the callback function of your choice

 * `input_format` is the input format for the GraphQL method, passed as a (possibly recursive) mapping; if unspecified or `None`, the defined GraphQL method will take no input; the mapping keys are

 * `output_format` is the output format of the GraphQL method, passed as a (possibly recursive) mapping or as a `list` containing one mapping

 * `pass_graphql_selection` can either be a `bool` or a `str`; if set to `True`, the `graphql_selection` parameter will be passed to the callback method, indicating which fields are requested for output; if set to a `str`, the given string will be the name of the keyword parameter passed to the callback method instead of `graphql_selection`

 * `pass_graphql_path` can either be a `bool` or a `str`; if set to `True`, the `graphql_path` parameter will be passed to the callback method, indicating as a `list[str]` the GraphQL path in which the method is being executed; if set to a `str`, the given string will be the name of the keyword parameter passed to the callback method instead of `graphql_path`

 * `pass_authenticated_user` can either be a `bool` or a `str`; if set to `True`, the `authenticated_user` parameter will be passed to the callback method, indicating the user authenticated in the source HTTP request (or `None` if the request was unauthenticated); if set to a `str`, the given string will be the name of the keyword parameter passed to the callback method instead of `authenticated_user`

 * `force_authenticated_user` is a `bool` indicating whether or not authentication is required for the exposed method

### Expose ORM models

#### Calling `Schema.expose_model()`

```python
import easy_graphql_server
from my_django_application.models import Person

schema = easy_graphql_server.Schema()

schema.expose_model(
	orm_model=Person,
	plural_name='people',
	can_expose=('id', 'first_name', 'last_name'),
	cannot_write=('id',),
)
```

#### Subclassing `Schema.ExposedModel`

```python
import easy_graphql_server
from my_django_application.models import Person

schema = easy_graphql_server.Schema()

class ExposedPerson(schema.ExposedModel):
		orm_model = Person
		plural_name = 'people'
		can_expose = ('id', 'first_name', 'last_name')
		cannot_write = ('id',)
```

#### Subclassing `easy_graphql_server.ExposedModel`

This is very similar to the previous way.

```python
import easy_graphql_server
from my_django_application.models import Person

schema = easy_graphql_server.Schema()

class ExposedPerson(easy_graphql_server.ExposedModel):
		orm_model = Person
		plural_name = 'people'
		can_expose = ('id', 'first_name', 'last_name')
		cannot_write = ('id',)

schema = easy_graphql_server.Schema()
schema.expose(ExposedPerson)
```

#### Available options for exposing models

The same options can be passed either as class attributes for subclasses of `ExposedModel`, or as keyword arguments to `Schema.expose_model()` method.

 * `orm_model` is the model class that we want to expose.

### Perform GraphQL queries

If you want to perform GraphQL queries on the schema without going through a schema, you can use `Schema.execute()`. This method can take the following parameters:

 * `query`: the GraphQL query, in the form of a `str`
 * `variables`: variables to go along with the query (optional), as a `dict[str,Any]`
 * `operation_name`: name of the operation to be executed within the query (optional)
 * `authenticated_user`: parameter that will be passed to the callback functions of GraphQL methods that require it (optional)
 * `serializable_output`: the output will be rendered as JSON-serializable `dict`, instead of a `graphql.GraphQLResult` instance

## Credits and history

The **easy_graphql_server** library was originally a subproject within the [Bridger](https://www.rightsbridger.com/) development
team, to provide an easy way to expose database models with GraphQL using
[Graphene](https://github.com/graphql-python/graphene).

The project was then rewritten with [graphq-core](https://github.com/graphql-python/graphql-core/)
and Graphene was dropped.

## License

**easy_graphql_server** is under MIT license.
