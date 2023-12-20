from typing import Any

from github_graphql_client.transport.base import BaseAsyncTransport


class AsyncGraphQLClient:
    """Async GraphQL client based on `BaseAsyncTransport` transport."""

    transport: BaseAsyncTransport

    def __init__(self, transport: BaseAsyncTransport) -> None:
        self.transport = transport

    async def __aenter__(self):
        await self.connect_async()
        return self

    async def __aexit__(self, *args):
        await self.close_async()

    async def connect_async(self) -> None:
        """Connect to `self.transport`."""
        await self.transport.connect()

    async def close_async(self) -> None:
        """Close `self.transport` connection."""
        await self.transport.close()

    async def execute_async(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        return await self.transport.execute(query, variables, **kwargs)
