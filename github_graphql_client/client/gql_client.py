from typing import Any

from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

from .base import BaseGraphQLClient


class GqlClient(BaseGraphQLClient):
    """GraphQL client based on `gql` lib."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        transport = AIOHTTPTransport(
            url=self.endpoint, headers=self._get_header()
        )
        self.client = Client(
            transport=transport, fetch_schema_from_transport=False
        )

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        gql_query = gql(query)
        return self.client.execute(
            gql_query, variable_values=variables, *args, **kwargs
        )
