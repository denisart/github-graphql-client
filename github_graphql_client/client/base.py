from typing import Any


class BaseGraphQLClient:
    """An abstract class for GraphQL client."""

    endpoint: str
    token: str

    def __init__(self, endpoint: str, token: str, **kwargs: Any) -> None:
        self.endpoint = endpoint
        self.token = token

    def _get_header(self) -> dict[str, Any]:
        return {"Authorization": f"Bearer {self.token}"}

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        raise NotImplementedError
