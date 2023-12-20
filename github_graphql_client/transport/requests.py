from typing import Any, Optional

import requests as r

from github_graphql_client.transport.base import BaseTransport


class RequestsTransport(BaseTransport):
    """The transport based on requests library."""

    DEFAULT_TIMEOUT: int = 1
    session: Optional[r.Session]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token
        self.auth_header = {"Authorization": f"Bearer {self.token}"}
        self.timeout = kwargs.get("timeout", RequestsTransport.DEFAULT_TIMEOUT)

        self.session = None

    def connect(self) -> None:
        """Start a `requests.Session` connection."""
        if self.session is None:
            self.session = r.Session()
        else:
            raise Exception("Session already started")

    def close(self) -> None:
        """Closing `requests.Session` connection."""
        if self.session is not None:
            self.session.close()
            self.session = None

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""
        if self.session is None:
            raise Exception(f"RequestsTransport session not connected")

        post_args = {
            "headers": self.auth_header,
            "json": {"query": query, "variables": variables},
            "timeout": self.timeout,
        }
        post_args["headers"]["Content-Type"] = "application/json"

        response = self.session.request("POST", self.endpoint, **post_args)

        result = response.json()
        return result.get("data")
