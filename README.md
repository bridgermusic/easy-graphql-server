# Easy GraphQL Server

## Installation

easy_graphql_server can be installed from PyPI using the built-in pip command:

```bash
pip install git+https://github.com/mathieurodic/easy-graphql-server
```

## Goals

easy_graphql_server's intention is to provide an easy way to expose a database in GraphQL,
using ORM models (so far only Django is supported, but SQLAlchemy will soon come).

## Credits and history

The easy_graphql_server library was originally a subproject within the Bridger development
team, to provide an easy way to expose database models with GraphQL using
[Graphene](https://github.com/graphql-python/graphene).

The project was then rewritten with [graphq-core](https://github.com/graphql-python/graphql-core/)
and Graphene was dropped.

## License

easy_graphql_server is under MIT license.
