from typing import Any
from graphql_query import Operation, Argument, Variable, Field, Query


var_owner = Variable(name="Owner", type="String!")
var_name = Variable(name="Name", type="String!")

f_node = Field(name="node", fields=["title", "url"])


def get_repository_issues_query(
    owner: str, name: str
) -> tuple[str, dict[str, Any]]:
    f_issues = Field(
        name="issues",
        arguments=[
            Argument(name="last", value=2),
            Argument(name="states", value="CLOSED"),
        ],
        fields=[Field(name="edges", fields=[f_node])],
    )

    operation = Operation(
        type="query",
        name="getRepositoryIssues",
        variables=[var_owner, var_name],
        queries=[
            Query(
                name="repository",
                arguments=[
                    Argument(name="owner", value=var_owner),
                    Argument(name="name", value=var_name),
                ],
                fields=[f_issues],
            )
        ],
    )

    return operation.render(), {var_owner.name: owner, var_name.name: name}
