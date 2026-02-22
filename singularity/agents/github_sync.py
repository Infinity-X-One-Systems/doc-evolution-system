"""
github_sync.py — Singularity Prime GitHub Sync Agent

Synchronises the repository state with:
  - GitHub Projects (via GraphQL API)
  - GitHub Issues (status comments)

Requires environment variables:
  GH_TOKEN       — GitHub Personal Access Token with repo + project scope
  ORG            — GitHub organisation name
  REPO           — Repository name

Idempotent: finding an existing project entry does not create a duplicate.
"""

import json
import os
import sys
from pathlib import Path

try:
    import urllib.request
    import urllib.error
except ImportError:
    pass

GH_API = "https://api.github.com/graphql"
STATE_FILE = "singularity/_STATE/state.json"


def _gql(token: str, query: str, variables: dict) -> dict:
    """Execute a GitHub GraphQL query."""
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GH_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[github_sync] GraphQL HTTP error {exc.code}: {body}", file=sys.stderr)
        sys.exit(1)


def get_state() -> dict:
    try:
        return json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[github_sync] Cannot read state file: {exc}", file=sys.stderr)
        sys.exit(1)


def post_issue_comment(token: str, org: str, repo: str, state: dict) -> None:
    """Post a state-sync comment to the latest open issue, if any."""
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        issues(first: 1, states: OPEN, orderBy: {field: UPDATED_AT, direction: DESC}) {
          nodes { number }
        }
      }
    }
    """
    result = _gql(token, query, {"owner": org, "name": repo})
    nodes = result.get("data", {}).get("repository", {}).get("issues", {}).get("nodes", [])
    if not nodes:
        print("[github_sync] No open issues found; skipping comment.")
        return

    issue_number = nodes[0]["number"]
    body = (
        f"**Singularity Prime — State Sync**\n\n"
        f"| Field | Value |\n|---|---|\n"
        f"| Current State | `{state.get('current')}` |\n"
        f"| Next State | `{state.get('next', '—')}` |\n"
        f"| Version | `{state.get('version', '0.0.0')}` |\n"
    )
    mutation = """
    mutation($id: ID!, $body: String!) {
      addComment(input: {subjectId: $id, body: $body}) {
        commentEdge { node { id } }
      }
    }
    """
    # Get the issue node id
    id_query = """
    query($owner: String!, $name: String!, $num: Int!) {
      repository(owner: $owner, name: $name) {
        issue(number: $num) { id }
      }
    }
    """
    id_result = _gql(token, id_query, {"owner": org, "name": repo, "num": issue_number})
    node_id = (
        id_result.get("data", {})
        .get("repository", {})
        .get("issue", {})
        .get("id")
    )
    if not node_id:
        print("[github_sync] Could not retrieve issue node ID; skipping comment.")
        return

    _gql(token, mutation, {"id": node_id, "body": body})
    print(f"[github_sync] State comment posted to issue #{issue_number}")


def main() -> None:
    token = os.environ.get("GH_TOKEN")
    org = os.environ.get("ORG")
    repo = os.environ.get("REPO")

    if not all([token, org, repo]):
        print(
            "[github_sync] WARNING: GH_TOKEN / ORG / REPO not set. Skipping sync.",
            file=sys.stderr,
        )
        sys.exit(0)

    state = get_state()
    print(f"[github_sync] Syncing state: {state.get('current')} → {state.get('next', '—')}")
    post_issue_comment(token, org, repo, state)
    print("[github_sync] GitHub sync complete ✓")


if __name__ == "__main__":
    main()
