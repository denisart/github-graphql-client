def get_repository_issues_query(owner: str, name: str) -> str:
    return """query {
  repository(owner:"%s", name:"%s") {
    issues(last:2, states:CLOSED) {
      edges {
        node {
          title
          url
        }
      }
    }
  }
}
""" % (
        owner,
        name,
    )
