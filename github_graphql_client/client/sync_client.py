from typing import Any

from github_graphql_client.transport.base import BaseTransport


class SyncGraphQLClient:
    """Sync GraphQL client based on `BaseTransport` transport."""

    transport: BaseTransport

    def __init__(self, transport: BaseTransport) -> None:
        self.transport = transport

    def __enter__(self):
        self.connect_sync()
        return self

    def __exit__(self, *args):
        self.close_sync()

    def connect_sync(self) -> None:
        """Connect to `self.transport`."""
        self.transport.connect()

    def close_sync(self) -> None:
        """Close `self.transport` connection."""
        self.transport.close()

    def execute_sync(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        return self.transport.execute(query, variables, **kwargs)
