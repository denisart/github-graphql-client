from typing import Any


class BaseTransport:
    """An abstract transport."""

    def execute(
        self, query: str, variables: dict[str, Any], **kwargs: Any
    ) -> dict[str, Any]:
        """Execute GraphQL query."""
        raise NotImplementedError

    def connect(self) -> None:
        """Establish a session with the transport."""
        raise NotImplementedError

    def close(self) -> None:
        """Close a session."""
        raise NotImplementedError
