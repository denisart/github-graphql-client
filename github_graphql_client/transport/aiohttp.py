from typing import Any, Optional

import aiohttp

from github_graphql_client.transport.base import BaseAsyncTransport


class AIOHTTPTransport(BaseAsyncTransport):
    """The transport based on aiohttp library."""

    DEFAULT_TIMEOUT = 1
    session: Optional[aiohttp.ClientSession]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
        self.timeout = kwargs.get("timeout", AIOHTTPTransport.DEFAULT_TIMEOUT)

        self.session = None

    async def connect(self) -> None:
        """Coroutine which will create an aiohttp ClientSession() as self.session."""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self.auth_header,
            )
        else:
            raise Exception(f"AIOHTTPTransport is already connected")

    async def close(self) -> None:
        """Coroutine which will close the aiohttp session."""
        if self.session is not None:
            await self.session.close()
            self.session = None

    async def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query with aiohttp."""
        if self.session is None:
            raise Exception(f"AIOHTTPTransport session not connected")

        async with self.session.post(
            self.endpoint,
            json={"query": query, "variables": variables},
        ) as response:
            data = await response.json()

        return data.get("data")
