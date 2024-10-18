# starlette-graphene

[![CI](https://github.com/bigbag/starlette-graphene/workflows/CI/badge.svg)](https://github.com/bigbag/starlette-graphene/actions?query=workflow%3ACI)
[![codecov](https://codecov.io/gh/bigbag/starlette-graphene/branch/main/graph/badge.svg?token=FQTY888XG1)](https://codecov.io/gh/bigbag/starlette-graphene)
[![pypi](https://img.shields.io/pypi/v/starlette-graphene.svg)](https://pypi.python.org/pypi/starlette-graphene)
[![downloads](https://img.shields.io/pypi/dm/starlette-graphene.svg)](https://pypistats.org/packages/starlette-graphene)
[![versions](https://img.shields.io/pypi/pyversions/starlette-graphene.svg)](https://github.com/bigbag/starlette-graphene)
[![license](https://img.shields.io/github/license/bigbag/starlette-graphene.svg)](https://github.com/bigbag/starlette-graphene/blob/master/LICENSE)


**starlette-graphene** is a helper for add support for graphene in starlette.

* [Project Changelog](https://github.com/bigbag/starlette-graphene/blob/main/CHANGELOG.md)

## Installation

starlette-graphene is available on PyPI.
Use pip to install:

    $ pip install starlette-graphene

## Basic Usage

```py
import uvicorn
from graphene import types as grt
from starlette.applications import Starlette

from starlette_graphene import GraphQLApp


class Account(grt.ObjectType):
    account = grt.Int(required=True)


class AccountFilter(grt.InputObjectType):
    accounts = grt.List(grt.Int)


class Query(grt.ObjectType):
    course_list = None
    accounts = grt.Field(
        grt.List(Account),
        filters=AccountFilter(),
    )

    async def resolve_accounts(
        self,
        info,
        filters: AccountFilter,
    ):

        return [Account(account=1212), Account(account=43434)]


def get_graphql_app() -> GraphQLApp:
    return GraphQLApp(schema=grt.Schema(query=Query))


def init_app():
    app_ = Starlette()
    app_.mount("/graphql/", get_graphql_app())
    return app_


app = init_app()

if __name__ == "__main__":
    uvicorn.run(app=app)
```

## License

starlette-graphene is developed and distributed under the Apache 2.0 license.

## Reporting a Security Vulnerability

See our [security policy](https://github.com/bigbag/starlette-graphene/security/policy).
