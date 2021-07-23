def test_invalid_method(client):
    response = client.put("/graphql/", data="{ hello }", headers={"content-type": "dummy"})
    assert response.status_code == 405
    assert response.text == "Method Not Allowed"


def test_invalid_media_type(client):
    response = client.post("/graphql/", data="{ hello }", headers={"content-type": "dummy"})
    assert response.status_code == 415
    assert response.text == "Unsupported Media Type"


def test_graphiql_if_enable(client):
    response = client.get("/graphql/")
    assert response.status_code == 200, response.text


def test_graphiql_if_disable(client):
    response = client.get("/graphql_without_graphiql/")
    assert response.status_code == 404
    assert response.text == "Not Found"


def test_without_query_in_data(client):
    response = client.post(
        "/graphql/",
        json={"query2": "{accounts(filters:{}),{account}}"},
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 400
    assert response.text == "No GraphQL query found in the request"


def test_with_errors(client):
    response = client.post(
        "/graphql/",
        data="{accounts(),{account}}",
        headers={"content-type": "application/graphql"},
    )
    assert response.status_code == 400, response.text


def test_success_graphql(client):
    response = client.post(
        "/graphql/",
        data="{accounts(filters:{}),{account}}",
        headers={"content-type": "application/graphql"},
    )
    assert response.status_code == 200, response.text


def test_success_json(client):
    response = client.post(
        "/graphql/",
        json={"query": "{accounts(filters:{}),{account}}"},
        headers={"content-type": "application/json"},
    )
    assert response.status_code == 200, response.text


def test_success_query_params(client):
    response = client.post(
        "/graphql/",
        params={"query": "{accounts(filters:{}),{account}}"},
    )
    assert response.status_code == 200, response.text
