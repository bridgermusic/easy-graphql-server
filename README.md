# Easy GraphQL Server

**easy_graphql_server** provides an easy way to expose a database in GraphQL, using ORM models and web frameworks (so far only Django is supported, but SQLAlchemy & Flask will soon come).

<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Easy GraphQL Server](#easy-graphql-server)
	- [Installation](#installation)
	- [Usage](#usage)
		- [Expose methods](#expose-methods)
			- [Calling `Schema.expose_query()` and `Schema.expose_mutation()`](#calling-schemaexposequery-and-schemaexposemutation)
			- [Subclassing `Schema.ExposedQuery` and `Schema.ExposedMutation`](#subclassing-schemaexposedquery-and-schemaexposedmutation)
			- [Available options](#available-options)
		- [Expose ORM models](#expose-orm-models)
			- [Calling `Schema.expose_model()`](#calling-schemaexposemodel)
			- [Subclassing `Schema.ExposedModel`](#subclassing-schemaexposedmodel)
			- [Available options](#available-options)
		- [Perform GraphQL queries](#perform-graphql-queries)
	- [Credits and history](#credits-and-history)
	- [License](#license)

<!-- /TOC -->

## Installation

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

#### Available options

The same options can be passed either as class attributes for subclasses of `Schema.ExposedQuery` and `Schema.ExposedMutation`, or as keyword arguments to `Schema.expose_query()` and `Schema.expose_mutation()` methods.

Options for *queries* and *mutations* are the same.

`name`

`method`

`input_format` input format for GraphQL method, passed as a (possible recursive) mapping; if unspecified or `None`, the defined GraphQL method will take no input.

output_format=None
pass_graphql_selection=False
pass_graphql_path=False
pass_authenticated_user=False
force_authenticated_user=False

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

#### Available options

The same options can be passed either as class attributes for subclasses of `ExposedModel`, or as keyword arguments to `Schema.expose_model()` method.

### Perform GraphQL queries

## Credits and history

The **easy_graphql_server** library was originally a subproject within the [Bridger](https://www.rightsbridger.com/) development
team, to provide an easy way to expose database models with GraphQL using
[Graphene](https://github.com/graphql-python/graphene).

The project was then rewritten with [graphq-core](https://github.com/graphql-python/graphql-core/)
and Graphene was dropped.

## License

**easy_graphql_server** is under MIT license.
