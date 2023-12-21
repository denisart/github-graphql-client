from typing import Any
from graphql_query import Operation, Argument, Variable, Field, Query


var_owner = Variable(name="Owner", type="String!")
var_name = Variable(name="Name", type="String!")
var_last = Variable(name="Last", type="Int")
var_issue_state = Variable(name="IssueState", type="[IssueState!]")

f_node = Field(name="node", fields=["title", "url"])


def get_repository_issues_query(
    owner: str,
    name: str,
    last: int,
    state: str,
) -> tuple[str, dict[str, Any]]:
    f_issues = Field(
        name="issues",
        arguments=[
            Argument(name="last", value=var_last),
            Argument(name="states", value=var_issue_state),
        ],
        fields=[Field(name="edges", fields=[f_node])],
    )

    operation = Operation(
        type="query",
        name="getRepositoryIssues",
        variables=[var_owner, var_name, var_last, var_issue_state],
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

    return operation.render(), {
        var_owner.name: owner,
        var_name.name: name,
        var_last.name: last,
        var_issue_state.name: state,
    }
