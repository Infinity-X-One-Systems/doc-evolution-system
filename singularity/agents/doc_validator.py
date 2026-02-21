"""
doc_validator.py — Singularity Prime Documentation Validator

Validates that the required documentation artefacts exist and are well-formed.

Checks:
  1. README.md exists and is non-empty.
  2. singularity/blueprint/master_invocation.md exists.
  3. singularity/blueprint/architecture.md exists.
  4. singularity/blueprint/roadmap.json is valid JSON with 'milestones'.
  5. singularity/evolution/checklist.json is valid JSON with 'items'.
  6. singularity/evolution/index.json is valid JSON with 'artefacts'.

Exit code 0 = documentation valid.
Exit code 1 = documentation invalid (CI fails).
"""

import json
import sys
from pathlib import Path


REQUIRED_DOCS = [
    ("README.md", None),
    ("singularity/blueprint/master_invocation.md", None),
    ("singularity/blueprint/architecture.md", None),
    ("singularity/blueprint/roadmap.json", "milestones"),
    ("singularity/evolution/checklist.json", "items"),
    ("singularity/evolution/index.json", "artefacts"),
]


def validate() -> list[str]:
    errors = []

    for path_str, required_key in REQUIRED_DOCS:
        path = Path(path_str)

        if not path.exists():
            errors.append(f"Missing required documentation file: {path_str}")
            continue

        content = path.read_text(encoding="utf-8").strip()
        if not content:
            errors.append(f"Documentation file is empty: {path_str}")
            continue

        if path_str.endswith(".json"):
            try:
                data = json.loads(content)
            except json.JSONDecodeError as exc:
                errors.append(f"Invalid JSON in {path_str}: {exc}")
                continue

            if required_key and required_key not in data:
                errors.append(
                    f"{path_str} is missing required top-level key: '{required_key}'"
                )

    return errors


def main() -> None:
    errors = validate()

    if errors:
        print("[doc_validator] DOCUMENTATION VALIDATION FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  ✗ {err}", file=sys.stderr)
        sys.exit(1)

    print("[doc_validator] All documentation checks passed ✓")


if __name__ == "__main__":
    main()
