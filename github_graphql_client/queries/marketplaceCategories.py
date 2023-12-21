from typing import Any

from graphql_query import Operation, Argument, Variable, Field, Query


var_exclude_empty = Variable(name="excludeEmpty", type="Boolean")
var_exclude_subcategories = Variable(
    name="excludeSubcategories", type="Boolean"
)
var_include_categories = Variable(name="includeCategories", type="[String!]")


def get_marketplace_categories(
    exclude_empty: bool,
    exclude_subcategories: bool,
    include_categories: list[str],
) -> tuple[str, dict[str, Any]]:
    marketplace_categories_query = Query(
        name="marketplaceCategories",
        arguments=[
            Argument(name="excludeEmpty", value=var_exclude_empty),
            Argument(
                name="excludeSubcategories",
                value=var_exclude_subcategories,
            ),
            Argument(name="includeCategories", value=var_include_categories),
        ],
        fields=["id", "description"],
    )

    operation = Operation(
        type="query",
        name="getMarketplaceCategories",
        variables=[
            var_exclude_empty,
            var_exclude_subcategories,
            var_include_categories,
        ],
        queries=[marketplace_categories_query],
    )

    variables = {
        var_exclude_empty.name: exclude_empty,
        var_exclude_subcategories.name: exclude_subcategories,
        var_include_categories.name: include_categories,
    }

    return operation.render(), variables
