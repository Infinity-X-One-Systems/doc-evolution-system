"""
evolution_engine.py — Singularity Prime Evolution Engine

Orchestrates the full document-evolution lifecycle:
  1. Detect technology stack (delegates to tech_detector.py).
  2. Validate state (delegates to state_machine.py).
  3. Validate documentation (delegates to doc_validator.py).
  4. Update validation_report.json with current check results.
  5. Update memory_registry.json with this run.
  6. Optionally push state forward if all checks pass.

Idempotent: safe to re-run at any time.
"""

import datetime
import json
import subprocess
import sys
from pathlib import Path

VALIDATION_REPORT = "singularity/evolution/validation_report.json"
MEMORY_REGISTRY = "singularity/evolution/memory_registry.json"


def run_check(name: str, command: list[str]) -> bool:
    """Run a sub-agent check, return True on success."""
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"[evolution_engine] ✓ {name}")
        return True
    print(f"[evolution_engine] ✗ {name}")
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return False


def update_validation_report(results: dict[str, bool]) -> None:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
    report = {
        "schema_version": "1.0.0",
        "generated_at": now,
        "checks": {
            name: {
                "status": "pass" if passed else "fail",
                "last_run": now,
                "result": "pass" if passed else "fail",
            }
            for name, passed in results.items()
        },
        "overall": "pass" if all(results.values()) else "fail",
    }
    Path(VALIDATION_REPORT).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"[evolution_engine] Validation report updated: {VALIDATION_REPORT}")


def update_memory_registry(results: dict[str, bool]) -> None:
    registry_path = Path(MEMORY_REGISTRY)
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        registry = {"schema_version": "1.0.0", "updated_at": "", "entries": []}

    registry["entries"].append(
        {
            "event": "evolution_engine_run",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z",
            "overall": "pass" if all(results.values()) else "fail",
            "checks": {k: ("pass" if v else "fail") for k, v in results.items()},
        }
    )
    registry["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat() + "Z"
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"[evolution_engine] Memory registry updated: {MEMORY_REGISTRY}")


def main() -> None:
    print("[evolution_engine] Starting Singularity Prime Evolution Engine...")

    checks = {
        "state_machine": run_check(
            "State Machine", ["python", "singularity/agents/state_machine.py"]
        ),
        "pat": run_check(
            "PAT Validator", ["python", "singularity/agents/pat_validator.py"]
        ),
        "docs": run_check(
            "Doc Validator", ["python", "singularity/agents/doc_validator.py"]
        ),
        "tech_detector": run_check(
            "Tech Detector", ["python", "singularity/agents/tech_detector.py"]
        ),
    }

    update_validation_report(checks)
    update_memory_registry(checks)

    overall = all(checks.values())
    print(
        f"[evolution_engine] Overall: {'PASS ✓' if overall else 'FAIL ✗'}"
    )
    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
