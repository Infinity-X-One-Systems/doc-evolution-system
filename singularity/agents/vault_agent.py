"""
vault_agent.py — Singularity Prime Vault Agent

Reads and writes secrets from/to HashiCorp Vault.

Capabilities:
  - Read secrets at a given KV path.
  - Write release metadata to Vault on deployment.
  - Gracefully degrades if VAULT_ADDR / VAULT_TOKEN are not set.

Environment variables:
  VAULT_ADDR    — Vault server address (e.g. https://vault.example.com)
  VAULT_TOKEN   — Vault token with kv read/write policy
  VAULT_KV_PATH — KV path prefix (default: secret/singularity)
"""

import json
import os
import sys
import datetime
import urllib.request
import urllib.error
from pathlib import Path


def _vault_url() -> str | None:
    return os.environ.get("VAULT_ADDR")


def _vault_token() -> str | None:
    return os.environ.get("VAULT_TOKEN")


def _kv_path() -> str:
    return os.environ.get("VAULT_KV_PATH", "secret/singularity")


def read_secret(secret_name: str) -> dict | None:
    """Read a KV secret from Vault. Returns the data dict or None."""
    addr = _vault_url()
    token = _vault_token()
    if not addr or not token:
        print("[vault_agent] WARNING: VAULT_ADDR or VAULT_TOKEN not set. Skipping read.")
        return None

    url = f"{addr}/v1/{_kv_path()}/{secret_name}"
    req = urllib.request.Request(
        url,
        headers={"X-Vault-Token": token},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            data = json.loads(resp.read())
            return data.get("data", {})
    except urllib.error.HTTPError as exc:
        print(f"[vault_agent] Read error {exc.code} when accessing Vault secret.", file=sys.stderr)
        return None


def write_secret(secret_name: str, payload: dict) -> bool:
    """Write a KV secret to Vault. Returns True on success."""
    addr = _vault_url()
    token = _vault_token()
    if not addr or not token:
        print("[vault_agent] WARNING: VAULT_ADDR or VAULT_TOKEN not set. Skipping write.")
        return False

    url = f"{addr}/v1/{_kv_path()}/{secret_name}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"X-Vault-Token": token, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
            print(f"[vault_agent] Secret write completed (HTTP {resp.status})")
            return True
    except urllib.error.HTTPError as exc:
        print(f"[vault_agent] Secret write error (HTTP {exc.code})", file=sys.stderr)
        return False


def sync_release_to_vault() -> None:
    """Write the current state and version to Vault on release."""
    state_path = Path("singularity/_STATE/state.json")
    if not state_path.exists():
        print("[vault_agent] state.json not found; skipping release sync.")
        return

    state = json.loads(state_path.read_text(encoding="utf-8"))
    payload = {
        "current_state": state.get("current"),
        "version": state.get("version", "0.0.0"),
        "synced_at": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
    }
    write_secret("release/latest", payload)


def main() -> None:
    action = os.environ.get("VAULT_ACTION", "sync_release")
    if action == "sync_release":
        sync_release_to_vault()
    elif action == "read":
        secret_name = os.environ.get("VAULT_SECRET_NAME", "")
        if secret_name:
            data = read_secret(secret_name)
            if data:
                print(f"[vault_agent] Secret '{secret_name}' read successfully with {len(data)} field(s).")
    else:
        print(f"[vault_agent] Unknown action: {action}", file=sys.stderr)
        sys.exit(1)

    print("[vault_agent] Vault agent run complete.")


if __name__ == "__main__":
    main()
