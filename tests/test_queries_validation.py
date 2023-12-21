from pathlib import Path

from graphql import GraphQLSchema, Source, build_schema, parse, validate

from github_graphql_client.queries.marketplaceCategories import \
    get_marketplace_categories
from github_graphql_client.queries.repository import \
    get_repository_issues_query

SCHEMA_FILENAME = Path(__file__).parent / Path("data/schema.docs.graphql")


def get_schema() -> GraphQLSchema:
    with SCHEMA_FILENAME.open("r", encoding="utf8") as f:
        schema_str = f.read()

    return build_schema(schema_str)


schema = get_schema()


def test_repository_issues_query():
    query, _ = get_repository_issues_query("pydantic", "FastUI")
    print(query)
    document = parse(Source(query))

    validation_errors = validate(schema, document)
    if validation_errors:
        raise validation_errors[0]


def test_get_marketplace_categories():
    query, _ = get_marketplace_categories(True, False, ["1", "2", "3"])
    document = parse(Source(query))
    print(query)

    validation_errors = validate(schema, document)
    if validation_errors:
        raise validation_errors[0]
