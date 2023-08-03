import pytest
from graphene import types as grt
from starlette.applications import Starlette
from starlette.testclient import TestClient

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


def get_graphql_app(graphiql: bool = True) -> GraphQLApp:
    return GraphQLApp(schema=grt.Schema(query=Query), graphiql=graphiql)


@pytest.fixture()
def app():
    app_ = Starlette()
    app_.mount("/graphql/", get_graphql_app())
    app_.mount("/graphql_without_graphiql/", get_graphql_app(graphiql=False))
    return app_


@pytest.fixture
def client(app):
    return TestClient(app)
