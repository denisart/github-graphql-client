import asyncio
from typing import Any, Union

from github_graphql_client.transport.base import (
    BaseAsyncTransport,
    BaseTransport,
)

from .async_client import AsyncGraphQLClient
from .sync_client import SyncGraphQLClient


class GraphQLClient(SyncGraphQLClient, AsyncGraphQLClient):
    """GraphQL client."""

    transport: Union[BaseTransport, BaseAsyncTransport]

    def __init__(
        self, transport: Union[BaseTransport, BaseAsyncTransport]
    ) -> None:
        super().__init__(transport)

    async def _execute_async(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        async with self as client:
            data = await client.execute_async(
                query,
                variables,
                **kwargs,
            )
        return data

    async def _execute_batch_async(
        self,
        queries: list[str],
        variables: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        tasks = []

        async with self as client:
            for i in range(len(queries)):
                query = queries[i]
                vars = variables[i]

                tasks.append(client.execute_async(query, vars, **kwargs))

            result_data = await asyncio.gather(*tasks)

        return list(result_data)

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""

        if isinstance(self.transport, BaseAsyncTransport):
            return asyncio.run(self._execute_async(query, variables, **kwargs))
        else:
            with self as client:
                return client.execute_sync(query, variables, **kwargs)

    def execute_batch(
        self,
        queries: list[str],
        variables: list[dict[str, Any]],
        **kwargs: Any,
    ) -> list[dict[str, Any]]:
        """Execute a batch of GraphQL queries."""

        if isinstance(self.transport, BaseAsyncTransport):
            return asyncio.run(
                self._execute_batch_async(queries, variables, **kwargs)
            )
        else:
            results = []
            with self as client:
                for i in range(len(queries)):
                    query = queries[i]
                    vars = variables[i]

                    res = client.execute_sync(query, vars, **kwargs)

                    results.append(res)

            return results
