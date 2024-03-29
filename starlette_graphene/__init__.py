import json
import typing as t
from dataclasses import dataclass

import graphene
from graphql import ExecutionContext, GraphQLError, GraphQLFormattedError, Middleware, graphql
from starlette import status
from starlette import types as st
from starlette.background import BackgroundTasks
from starlette.requests import HTTPConnection, Request
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response


def format_error(error: GraphQLError) -> GraphQLFormattedError:
    if not isinstance(error, GraphQLError):
        raise TypeError("Expected a GraphQLError.")
    return error.formatted


@dataclass
class GraphQLApp:
    schema: graphene.Schema
    graphiql: bool = True
    context_value: t.Optional[t.Any] = None
    root_value: t.Optional[t.Any] = None
    middleware: t.Optional[Middleware] = None
    error_formatter: t.Callable[[GraphQLError], GraphQLFormattedError] = format_error
    execution_context_class: t.Optional[t.Type[ExecutionContext]] = None

    async def __call__(self, scope: st.Scope, receive: st.Receive, send: st.Send) -> None:
        request = Request(scope, receive=receive)
        response = await self._handle_graphql(request)
        await response(scope, receive, send)

    async def _get_context_value(self, request: HTTPConnection) -> t.Any:
        return self.context_value or {
            "request": request,
            "background": BackgroundTasks(),
        }

    @staticmethod
    async def _handle_graphiql(request: Request) -> Response:
        text = GRAPHIQL.replace("{{REQUEST_PATH}}", json.dumps(request.url.path))
        return HTMLResponse(text)

    @staticmethod
    async def _get_query_body(request: Request) -> t.Any:
        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            return await request.json()

        if "application/graphql" in content_type:
            body = await request.body()
            text = body.decode()
            return {"query": text}

        if "query" in request.query_params:
            return request.query_params

        return None

    async def _handle_graphql(self, request: Request) -> Response:
        if request.method not in ("GET", "HEAD", "POST"):
            return PlainTextResponse(
                "Method Not Allowed",
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
            )

        if request.method in ("GET", "HEAD"):
            if not self.graphiql:
                return PlainTextResponse("Not Found", status_code=status.HTTP_404_NOT_FOUND)
            return await self._handle_graphiql(request)

        data = await self._get_query_body(request)
        if data is None:
            return PlainTextResponse(
                "Unsupported Media Type",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        try:
            query = data["query"]
        except KeyError:
            return PlainTextResponse(
                "No GraphQL query found in the request",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        context_value = await self._get_context_value(request)
        result = await graphql(
            self.schema.graphql_schema,
            source=query,
            context_value=context_value,
            root_value=self.root_value,
            middleware=self.middleware,
            variable_values=data.get("variables"),
            operation_name=data.get("operationName"),
            execution_context_class=self.execution_context_class,
        )

        response: t.Dict[str, t.Any] = {"data": result.data}
        if result.errors:
            response["errors"] = [self.error_formatter(error) for error in result.errors]

        status_code = status.HTTP_400_BAD_REQUEST if result.errors else status.HTTP_200_OK
        return JSONResponse(
            response,
            status_code=status_code,
            background=context_value.get("background"),
        )


GRAPHIQL = """
<!--
 *  Copyright (c) Facebook, Inc.
 *  All rights reserved.
 *
 *  This source code is licensed under the license found in the
 *  LICENSE file in the root directory of this source tree.
-->
<!DOCTYPE html>
<html>
  <head>
    <style>
      body {
        height: 100%;
        margin: 0;
        width: 100%;
        overflow: hidden;
      }
      #graphiql {
        height: 100vh;
      }
    </style>
    <!--
      This GraphiQL example depends on Promise and fetch, which are available in
      modern browsers, but can be "polyfilled" for older browsers.
      GraphiQL itself depends on React DOM.
      If you do not want to rely on a CDN, you can host these files locally or
      include them directly in your favored resource bunder.
    -->
    <link href="//cdn.jsdelivr.net/npm/graphiql@0.12.0/graphiql.css" rel="stylesheet"/>
    <script src="//cdn.jsdelivr.net/npm/whatwg-fetch@2.0.3/fetch.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/react@16.2.0/umd/react.production.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/react-dom@16.2.0/umd/react-dom.production.min.js"></script>
    <script src="//cdn.jsdelivr.net/npm/graphiql@0.12.0/graphiql.min.js"></script>
  </head>
  <body>
    <div id="graphiql">Loading...</div>
    <script>
      /**
       * This GraphiQL example illustrates how to use some of GraphiQL's props
       * in order to enable reading and updating the URL parameters, making
       * link sharing of queries a little bit easier.
       *
       * This is only one example of this kind of feature, GraphiQL exposes
       * various React params to enable interesting integrations.
       */
      // Parse the search string to get url parameters.
      var search = window.location.search;
      var parameters = {};
      search.substr(1).split('&').forEach(function (entry) {
        var eq = entry.indexOf('=');
        if (eq >= 0) {
          parameters[decodeURIComponent(entry.slice(0, eq))] =
            decodeURIComponent(entry.slice(eq + 1));
        }
      });
      // if variables was provided, try to format it.
      if (parameters.variables) {
        try {
          parameters.variables =
            JSON.stringify(JSON.parse(parameters.variables), null, 2);
        } catch (e) {
          // Do nothing, we want to display the invalid JSON as a string, rather
          // than present an error.
        }
      }
      // When the query and variables string is edited, update the URL bar so
      // that it can be easily shared
      function onEditQuery(newQuery) {
        parameters.query = newQuery;
        updateURL();
      }
      function onEditVariables(newVariables) {
        parameters.variables = newVariables;
        updateURL();
      }
      function onEditOperationName(newOperationName) {
        parameters.operationName = newOperationName;
        updateURL();
      }
      function updateURL() {
        var newSearch = '?' + Object.keys(parameters).filter(function (key) {
          return Boolean(parameters[key]);
        }).map(function (key) {
          return encodeURIComponent(key) + '=' +
            encodeURIComponent(parameters[key]);
        }).join('&');
        history.replaceState(null, null, newSearch);
      }
      // Defines a GraphQL fetcher using the fetch API. You're not required to
      // use fetch, and could instead implement graphQLFetcher however you like,
      // as long as it returns a Promise or Observable.
      function graphQLFetcher(graphQLParams) {
        // This example expects a GraphQL server at the path /graphql.
        // Change this to point wherever you host your GraphQL server.
        return fetch({{REQUEST_PATH}}, {
          method: 'post',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(graphQLParams),
          credentials: 'include',
        }).then(function (response) {
          return response.text();
        }).then(function (responseBody) {
          try {
            return JSON.parse(responseBody);
          } catch (error) {
            return responseBody;
          }
        });
      }
      // Render <GraphiQL /> into the body.
      // See the README in the top level of this module to learn more about
      // how you can customize GraphiQL by providing different values or
      // additional child elements.
      ReactDOM.render(
        React.createElement(GraphiQL, {
          fetcher: graphQLFetcher,
          query: parameters.query,
          variables: parameters.variables,
          operationName: parameters.operationName,
          onEditQuery: onEditQuery,
          onEditVariables: onEditVariables,
          onEditOperationName: onEditOperationName
        }),
        document.getElementById('graphiql')
      );
    </script>
  </body>
</html>
"""  # noqa: E501
