"""
state_machine.py — Singularity Prime State Machine Validator

Reads singularity/_STATE/state.json, validates that the requested transition
is allowed, and appends to history.json on success.

Exit code 0 = valid transition.
Exit code 1 = invalid transition (CI fails).
"""

import json
import sys
import datetime

STATE_FILE = "singularity/_STATE/state.json"
HISTORY_FILE = "singularity/_STATE/history.json"
TRANSITIONS_FILE = "singularity/_STATE/transitions.json"

ALLOWED = {
    "NEW_IDEA": ["DISCOVERY_RUNNING"],
    "DISCOVERY_RUNNING": ["EVOLUTION_COMPLETE"],
    "EVOLUTION_COMPLETE": ["BUILD_RUNNING"],
    "BUILD_RUNNING": ["VALIDATION"],
    "VALIDATION": ["APPROVAL"],
    "APPROVAL": ["RELEASED"],
}


def load_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        print(f"[state_machine] ERROR: Required file not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as exc:
        print(f"[state_machine] ERROR: Invalid JSON in {path}: {exc}", file=sys.stderr)
        sys.exit(1)


def save_json(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def main() -> None:
    state = load_json(STATE_FILE)

    current = state.get("current", "")
    next_state = state.get("next", "")

    if not current:
        print("[state_machine] ERROR: 'current' field is missing from state.json", file=sys.stderr)
        sys.exit(1)

    if not next_state:
        print(f"[state_machine] INFO: No transition requested (next is empty). Current state: {current}")
        sys.exit(0)

    allowed_next = ALLOWED.get(current, [])
    if next_state not in allowed_next:
        print(
            f"[state_machine] ERROR: Invalid state transition: {current} → {next_state}. "
            f"Allowed: {allowed_next}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[state_machine] OK: Valid transition {current} → {next_state}")

    # Append to history
    try:
        history = load_json(HISTORY_FILE)
    except SystemExit:
        history = {"schema_version": "1.0.0", "transitions": []}

    history.setdefault("transitions", []).append(
        {
            "from": current,
            "to": next_state,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )
    save_json(HISTORY_FILE, history)
    print("[state_machine] History updated.")


if __name__ == "__main__":
    main()
