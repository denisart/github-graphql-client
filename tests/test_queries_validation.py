from pathlib import Path

from gql import Client
from graphql import Source, parse

from github_graphql_client.queries.repository import repository_issues_query

SCHEMA_FILENAME = Path(__file__).parent / Path("data/schema.docs.graphql")

with SCHEMA_FILENAME.open("r", encoding="utf8") as f:
    schema_str = f.read()


client = Client(schema=schema_str)


def test_repository_issues_query():
    source = Source(repository_issues_query)
    client.validate(parse(source))
