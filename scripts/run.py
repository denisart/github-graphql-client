import os

from dotenv import load_dotenv

from github_graphql_client.client.requests_client import RequestsClient
from github_graphql_client.runner import GraphQLClientRunner
from github_graphql_client.queries.repository import repository_issues_query

load_dotenv()  # take environment variables from .env

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
GITHUB_GRAPHQL_ENDPOINT = os.environ.get("GITHUB_GRAPHQL_ENDPOINT")


def main():
    client = RequestsClient(
        endpoint=GITHUB_GRAPHQL_ENDPOINT,
        token=GITHUB_TOKEN,
        timeout=0.0001,
    )
    r_runner = GraphQLClientRunner(client=client)

    data = r_runner.execute(repository_issues_query, {})
    print(data)


if __name__ == "__main__":
    main()
