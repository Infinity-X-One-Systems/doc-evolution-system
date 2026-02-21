"""
pat_validator.py — Singularity Prime PAT Protocol Validator

Validates that the repository complies with PAT (Pull Request, Approval, Transition)
governance protocol on every PR.

Checks:
  1. singularity/_STATE/state.json is present and valid.
  2. singularity/evolution/checklist.json exists.
  3. singularity/blueprint/master_invocation.md exists.
  4. No forbidden file patterns are present in the diff (secrets check).

Exit code 0 = PAT compliant.
Exit code 1 = PAT violation (CI fails).
"""

import json
import os
import sys
from pathlib import Path

REQUIRED_FILES = [
    "singularity/_STATE/state.json",
    "singularity/evolution/checklist.json",
    "singularity/blueprint/master_invocation.md",
    "singularity/agents/state_machine.py",
    ".github/CODEOWNERS",
]

FORBIDDEN_PATTERNS = [
    "password=",
    "secret=",
    "api_key=",
    "private_key",
    "-----BEGIN RSA",
    "-----BEGIN EC",
    "ghp_",
    "github_pat_",
]


def check_required_files() -> list[str]:
    errors = []
    for path in REQUIRED_FILES:
        if not Path(path).exists():
            errors.append(f"Required file missing: {path}")
    return errors


def check_state_json() -> list[str]:
    errors = []
    state_path = Path("singularity/_STATE/state.json")
    if not state_path.exists():
        return errors  # Already caught by check_required_files
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        for field in ("current", "version", "schema_version"):
            if field not in state:
                errors.append(f"state.json missing required field: '{field}'")
    except json.JSONDecodeError as exc:
        errors.append(f"state.json is invalid JSON: {exc}")
    return errors


def check_secret_leakage() -> list[str]:
    """Scan tracked files for obvious secret patterns (variable assignments only)."""
    # Match patterns that look like actual assignments: key=value or key: value
    # This avoids false positives from files that merely reference these strings
    # (e.g. this validator file itself, documentation, or config schema files).
    import re
    assignment_re = re.compile(
        r'(?:^|[;\n])\s*["\']?(?:' +
        '|'.join(re.escape(p.rstrip("=").rstrip()) for p in FORBIDDEN_PATTERNS) +
        r')["\']?\s*[:=]\s*[^\s{}\[\]#\'"]{4,}',
        re.IGNORECASE | re.MULTILINE,
    )
    errors = []
    # Skip this file itself — it intentionally lists the forbidden patterns
    self_path = os.path.abspath(__file__)
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "__pycache__", ".venv"}]
        for fname in files:
            if not fname.endswith((".json", ".yml", ".yaml", ".env", ".sh", ".ps1")):
                continue
            fpath = os.path.join(root, fname)
            if os.path.abspath(fpath) == self_path:
                continue
            try:
                content = Path(fpath).read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if assignment_re.search(content):
                errors.append(
                    f"Potential secret assignment in {fpath}: review for hardcoded credentials."
                )
    return errors


def main() -> None:
    all_errors: list[str] = []

    all_errors.extend(check_required_files())
    all_errors.extend(check_state_json())
    all_errors.extend(check_secret_leakage())

    if all_errors:
        print("[pat_validator] PAT PROTOCOL VIOLATIONS DETECTED:", file=sys.stderr)
        for err in all_errors:
            print(f"  ✗ {err}", file=sys.stderr)
        sys.exit(1)

    print("[pat_validator] PAT Protocol: All checks passed ✓")


if __name__ == "__main__":
    main()
