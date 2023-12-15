repository_issues_query = """
query {
  repository(owner:"pydantic", name:"FastUI") {
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
"""
