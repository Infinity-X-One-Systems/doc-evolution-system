"""
admin_project_register.py — Singularity Prime Admin Control Plane Auto-Registration

On repository initialisation (called by admin-sync.yml), this script:
  1. Creates a GitHub Project entry inside infinity-admin-control-plane.
  2. Links the new repository to that project.
  3. Creates a standard issue template on the repository.
  4. Registers the repository in the org-level admin registry JSON.

Uses the GitHub GraphQL API.

Required environment variables:
  GH_TOKEN  — PAT with org:read, project, repo scope
  ORG       — GitHub organisation (e.g. Infinity-X-One-Systems)
  REPO      — Repository name being registered

Optional environment variables:
  ADMIN_REPO  — Admin control plane repository name
                (default: infinity-admin-control-plane)
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.error

GH_GRAPHQL = "https://api.github.com/graphql"
GH_REST    = "https://api.github.com"


# ─── HTTP helpers ──────────────────────────────────────────────────────────

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gql(token: str, query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        GH_GRAPHQL,
        data=payload,
        headers=_headers(token),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read())
            if "errors" in data:
                print(f"[admin_register] GraphQL errors: {data['errors']}", file=sys.stderr)
            return data
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[admin_register] GraphQL HTTP {exc.code}: {body}", file=sys.stderr)
        return {}


def rest_post(token: str, path: str, payload: dict) -> dict | None:
    url = f"{GH_REST}{path}"
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=_headers(token), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[admin_register] REST POST {path} HTTP {exc.code}: {body}", file=sys.stderr)
        return None


def rest_get(token: str, path: str) -> dict | list | None:
    url = f"{GH_REST}{path}"
    req = urllib.request.Request(url, headers=_headers(token), method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[admin_register] REST GET {path} HTTP {exc.code}: {body}", file=sys.stderr)
        return None


# ─── Step 1: Get org node ID ────────────────────────────────────────────────

def get_org_node_id(token: str, org: str) -> str | None:
    query = """
    query($login: String!) {
      organization(login: $login) { id }
    }
    """
    result = gql(token, query, {"login": org})
    return result.get("data", {}).get("organization", {}).get("id")


# ─── Step 2: Find or create the admin project ───────────────────────────────

def find_or_create_project(token: str, org_node_id: str, project_title: str) -> str | None:
    """Return the project node ID, creating it if it doesn't exist."""
    list_query = """
    query($orgId: ID!, $cursor: String) {
      node(id: $orgId) {
        ... on Organization {
          projectsV2(first: 50, after: $cursor) {
            nodes { id title }
            pageInfo { hasNextPage endCursor }
          }
        }
      }
    }
    """
    cursor = None
    while True:
        result = gql(token, list_query, {"orgId": org_node_id, "cursor": cursor})
        projects = (
            result.get("data", {})
            .get("node", {})
            .get("projectsV2", {})
        )
        for p in projects.get("nodes", []):
            if p["title"] == project_title:
                print(f"[admin_register] Found existing project: {project_title} ({p['id']})")
                return p["id"]
        page_info = projects.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            break
        cursor = page_info.get("endCursor")

    # Create new project
    create_mutation = """
    mutation($orgId: ID!, $title: String!) {
      createProjectV2(input: {ownerId: $orgId, title: $title}) {
        projectV2 { id title }
      }
    }
    """
    result = gql(token, create_mutation, {"orgId": org_node_id, "title": project_title})
    project = result.get("data", {}).get("createProjectV2", {}).get("projectV2", {})
    if project.get("id"):
        print(f"[admin_register] Created project: {project_title} ({project['id']})")
        return project["id"]

    print(f"[admin_register] ERROR: Could not create project '{project_title}'", file=sys.stderr)
    return None


# ─── Step 3: Get repository node ID ─────────────────────────────────────────

def get_repo_node_id(token: str, org: str, repo: str) -> str | None:
    query = """
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) { id }
    }
    """
    result = gql(token, query, {"owner": org, "name": repo})
    return result.get("data", {}).get("repository", {}).get("id")


# ─── Step 4: Link repository to project ─────────────────────────────────────

def link_repo_to_project(token: str, project_id: str, repo_node_id: str) -> bool:
    mutation = """
    mutation($projectId: ID!, $contentId: ID!) {
      addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
        item { id }
      }
    }
    """
    result = gql(token, mutation, {"projectId": project_id, "contentId": repo_node_id})
    item = result.get("data", {}).get("addProjectV2ItemById", {}).get("item", {})
    if item.get("id"):
        print(f"[admin_register] Repository linked to project (item: {item['id']})")
        return True
    print("[admin_register] WARNING: Could not link repository to project.", file=sys.stderr)
    return False


# ─── Step 5: Create standard issue template ─────────────────────────────────

ISSUE_TEMPLATE = """\
---
name: Singularity Prime — State Transition Request
about: Request a state transition in the Singularity Prime lifecycle
title: "[STATE TRANSITION] <current> → <next>"
labels: ["singularity", "state-transition"]
assignees: []
---

## State Transition Request

| Field | Value |
|---|---|
| Current State | <!-- e.g. VALIDATION --> |
| Requested Next State | <!-- e.g. APPROVAL --> |
| Requested by | @<!-- your GitHub handle --> |
| Reason | <!-- Brief justification --> |

## Validation Matrix

- [ ] PAT check passed
- [ ] CodeQL check passed
- [ ] Docs check passed
- [ ] State machine check passed
- [ ] Playwright check passed

## Notes

<!-- Any additional context -->
"""


def create_issue_template(token: str, org: str, repo: str) -> bool:
    """Create .github/ISSUE_TEMPLATE/state_transition.md if it doesn't exist."""
    path = ".github/ISSUE_TEMPLATE/state_transition.md"
    check = rest_get(token, f"/repos/{org}/{repo}/contents/{path}")
    if check:
        print(f"[admin_register] Issue template already exists: {path}")
        return True

    import base64
    content_b64 = base64.b64encode(ISSUE_TEMPLATE.encode()).decode()
    payload = {
        "message": "chore: add Singularity Prime state transition issue template",
        "content": content_b64,
    }
    result = rest_post(token, f"/repos/{org}/{repo}/contents/{path}", payload)
    if result:
        print(f"[admin_register] Issue template created: {path}")
        return True
    print("[admin_register] WARNING: Could not create issue template.", file=sys.stderr)
    return False


# ─── Step 6: Update admin registry JSON ─────────────────────────────────────

def update_admin_registry(
    token: str, org: str, admin_repo: str, repo: str, project_id: str | None
) -> None:
    """Read/create the admin registry JSON and append this repo."""
    registry_path = "registry/repos.json"
    existing = rest_get(token, f"/repos/{org}/{admin_repo}/contents/{registry_path}")

    import base64

    if existing and isinstance(existing, dict) and "content" in existing:
        raw = base64.b64decode(existing["content"]).decode("utf-8")
        registry = json.loads(raw)
        sha = existing["sha"]
    else:
        registry = {"schema_version": "1.0.0", "repos": []}
        sha = None

    # Idempotent: skip if already registered
    if any(r.get("name") == repo for r in registry.get("repos", [])):
        print(f"[admin_register] Repository already in admin registry: {repo}")
        return

    registry.setdefault("repos", []).append(
        {
            "name": repo,
            "org": org,
            "project_id": project_id,
            "registered_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )
    registry["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")

    new_content = base64.b64encode(
        json.dumps(registry, indent=2).encode()
    ).decode()
    payload: dict = {
        "message": f"chore: register {org}/{repo} in admin registry",
        "content": new_content,
    }
    if sha:
        payload["sha"] = sha

    result = rest_post(
        token, f"/repos/{org}/{admin_repo}/contents/{registry_path}", payload
    )
    if result:
        print(f"[admin_register] Admin registry updated with: {repo}")
    else:
        print("[admin_register] WARNING: Could not update admin registry.", file=sys.stderr)


# ─── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    token      = os.environ.get("GH_TOKEN", "")
    org        = os.environ.get("ORG", "Infinity-X-One-Systems")
    repo       = os.environ.get("REPO", "")
    admin_repo = os.environ.get("ADMIN_REPO", "infinity-admin-control-plane")

    if not token:
        print(
            "[admin_register] WARNING: GH_TOKEN not set. Skipping admin registration.",
            file=sys.stderr,
        )
        sys.exit(0)

    if not repo:
        print("[admin_register] ERROR: REPO env var is required.", file=sys.stderr)
        sys.exit(1)

    print(f"[admin_register] Registering {org}/{repo} in admin control plane…")

    # Step 1
    org_node_id = get_org_node_id(token, org)
    if not org_node_id:
        print(f"[admin_register] ERROR: Could not resolve org '{org}'", file=sys.stderr)
        sys.exit(1)

    # Step 2
    project_id = find_or_create_project(
        token, org_node_id, f"Singularity Prime — {admin_repo}"
    )

    # Step 3
    repo_node_id = get_repo_node_id(token, org, repo)

    # Step 4
    if project_id and repo_node_id:
        link_repo_to_project(token, project_id, repo_node_id)

    # Step 5
    create_issue_template(token, org, repo)

    # Step 6
    update_admin_registry(token, org, admin_repo, repo, project_id)

    print("[admin_register] Admin registration complete ✓")


if __name__ == "__main__":
    main()
