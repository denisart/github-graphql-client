import time
from typing import Any

from github_graphql_client.client.base import BaseGraphQLClientProtocol


def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration is {toc - tic:0.4f} seconds")
        return result

    return wrapper


class GraphQLClientRunner:
    client: BaseGraphQLClientProtocol

    def __init__(
        self, client: BaseGraphQLClientProtocol, *args: Any, **kwargs: Any
    ) -> None:
        self.client = client

    @check_execute
    def execute(
        self, query: str, variables: dict[str, Any], *args: Any, **kwargs: Any
    ) -> dict[str, Any]:
        return self.client.execute(query, variables, *args, **kwargs)
