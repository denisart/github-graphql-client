from typing import Any

import requests as r

from .base import BaseGraphQLClient


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    DEFAULT_TIMEOUT = 1

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        super().__init__(endpoint, token, **kwargs)

        self.timeout = kwargs.get("timeout", RequestsClient.DEFAULT_TIMEOUT)

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        response = r.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
            timeout=self.timeout,
        )
        response = response.json()
        return response["data"]
