from typing import Any

import requests as r

from .base import BaseGraphQLClient


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        response = r.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
        )
        response = response.json()
        return response["data"]
