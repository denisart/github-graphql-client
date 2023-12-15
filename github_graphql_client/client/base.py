from typing import Any, Protocol


class BaseGraphQLClientProtocol(Protocol):
    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        ...


class BaseGraphQLClient:
    """An abstract class for GraphQL client."""

    endpoint: str
    token: str

    def __init__(
        self, endpoint: str, token: str, *args: Any, **kwargs: Any
    ) -> None:
        self.endpoint = endpoint
        self.token = token

    def _get_header(self) -> dict[str, Any]:
        return {"Authorization": f"Bearer {self.token}"}

    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        raise NotImplementedError
