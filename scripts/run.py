import os
import time
from typing import Any

from dotenv import load_dotenv

from github_graphql_client.client.base import BaseGraphQLClient
from github_graphql_client.client.requests_client import RequestsClient
from github_graphql_client.queries.repository import (
    get_repository_issues_query,
)

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")


def check_execute(fn):
    def wrapper(*args, **kwargs):
        tic = time.perf_counter()
        result = fn(*args, **kwargs)
        toc = time.perf_counter()
        print(f"Duration is {toc - tic:0.4f} seconds")
        return result

    return wrapper


@check_execute
def execute_client(client: BaseGraphQLClient, **kwargs) -> Any:
    return client.execute(**kwargs)


def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT, token=GITHUB_TOKEN
    )

    with client:
        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "FastUI"),
            variables={},
        )

        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "pydantic"),
            variables={},
        )

        execute_client(
            client,
            query=get_repository_issues_query("pydantic", "pydantic-core"),
            variables={},
        )

    print(f'client.session = {client.session}')


if __name__ == "__main__":
    main()
