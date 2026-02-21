"""
mesh_hook.py — Singularity Prime Sovereign Mesh Hook

Sends Orchestrator events to the configured Sovereign Mesh Node webhook endpoint.

Event schema:
  {
    "event": "STATE_TRANSITION",
    "repository": "repo-name",
    "current_state": "VALIDATION",
    "next_state": "APPROVAL",
    "validation_matrix": { ... },
    "timestamp": "UTC ISO8601"
  }

Environment variables:
  MESH_HOOK_URL     — Webhook URL of the Sovereign Mesh Node
  MESH_HOOK_SECRET  — Optional HMAC-SHA256 shared secret for request signing
  ORG               — GitHub organisation
  REPO              — Repository name

Gracefully degrades if MESH_HOOK_URL is not set.
"""

import hashlib
import hmac
import json
import os
import sys
import datetime
import urllib.request
import urllib.error
from pathlib import Path


STATE_FILE = "singularity/_STATE/state.json"
VALIDATION_REPORT = "singularity/evolution/validation_report.json"


def _build_event(state: dict, validation: dict) -> dict:
    checks = validation.get("checks", {})
    matrix = {k: v.get("status") == "pass" for k, v in checks.items()}
    return {
        "event": "STATE_TRANSITION",
        "repository": os.environ.get("REPO", "unknown"),
        "org": os.environ.get("ORG", "Infinity-X-One-Systems"),
        "current_state": state.get("current"),
        "next_state": state.get("next", ""),
        "validation_matrix": matrix,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _sign(payload: bytes, secret: str) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()


def send_event(event: dict) -> bool:
    url = os.environ.get("MESH_HOOK_URL")
    if not url:
        print("[mesh_hook] WARNING: MESH_HOOK_URL not set. Skipping mesh event.")
        return False

    payload = json.dumps(event, indent=2).encode()
    headers = {"Content-Type": "application/json"}

    secret = os.environ.get("MESH_HOOK_SECRET")
    if secret:
        headers["X-Hub-Signature-256"] = _sign(payload, secret)

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            print(f"[mesh_hook] Event sent: HTTP {resp.status}")
            return True
    except urllib.error.HTTPError as exc:
        print(f"[mesh_hook] HTTP error {exc.code}", file=sys.stderr)
        return False
    except OSError as exc:
        print(f"[mesh_hook] Connection error: {exc}", file=sys.stderr)
        return False


def main() -> None:
    try:
        state = json.loads(Path(STATE_FILE).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"[mesh_hook] Cannot read state: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        validation = json.loads(Path(VALIDATION_REPORT).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        validation = {}

    event = _build_event(state, validation)
    print(f"[mesh_hook] Dispatching event: {event['event']}")
    send_event(event)
    print("[mesh_hook] Mesh hook run complete.")


if __name__ == "__main__":
    main()
