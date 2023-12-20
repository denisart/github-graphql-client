from typing import Any, Optional

import requests as r

from .base import BaseGraphQLClient


class RequestsClient(BaseGraphQLClient):
    """GraphQL client based on `requests` library."""

    DEFAULT_TIMEOUT = 1

    session: Optional[r.Session]

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        super().__init__(endpoint, token, **kwargs)

        self.timeout = kwargs.get("timeout", RequestsClient.DEFAULT_TIMEOUT)
        self.session = None

    def __enter__(self) -> None:
        self.session = r.Session()

    def __exit__(self, *args):
        self.close_session()

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        if self.session is None:
            self.session = r.Session()

        response = self.session.post(
            url=self.endpoint,
            json={"query": query, "variables": variables},
            headers=self._get_header(),
            timeout=self.timeout,
        )
        response = response.json()
        return response["data"]

    def close_session(self) -> None:
        self.session.close()
        self.session = None
