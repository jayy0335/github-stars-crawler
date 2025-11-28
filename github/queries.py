from __future__ import annotations

REPO_FRAGMENT = """
node {
  ... on Repository {
    id
    name
    nameWithOwner
    url
    stargazerCount
    createdAt
    owner { login }
  }
}
cursor
"""

SEARCH_REPOS = f"""
query($q:String!, $after:String) {{
  search(query: $q, type: REPOSITORY, first: 100, after: $after) {{
    pageInfo {{ hasNextPage endCursor }}
    edges {{ {REPO_FRAGMENT} }}
  }}
  rateLimit {{ limit cost remaining resetAt }}
}}
"""
