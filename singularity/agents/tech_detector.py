"""
tech_detector.py — Singularity Prime Technology Detector

Scans the repository for known technology indicators and writes the results
to singularity/evolution/tech_registry.json.

Idempotent: always overwrites the registry with the current scan result.
"""

import json
import datetime
import sys
from pathlib import Path

REGISTRY_PATH = "singularity/evolution/tech_registry.json"

INDICATORS: list[tuple[str, str, str]] = [
    # (glob_pattern, technology_name, category)
    ("*.py", "Python", "language"),
    ("*.js", "JavaScript", "language"),
    ("*.ts", "TypeScript", "language"),
    ("*.go", "Go", "language"),
    ("*.java", "Java", "language"),
    ("*.rs", "Rust", "language"),
    ("*.rb", "Ruby", "language"),
    ("Dockerfile*", "Docker", "infrastructure"),
    ("docker-compose*.yml", "Docker Compose", "infrastructure"),
    (".github/workflows/*.yml", "GitHub Actions", "ci_cd"),
    ("terraform/**/*.tf", "Terraform", "infrastructure"),
    ("*.tf", "Terraform", "infrastructure"),
    ("package.json", "Node.js", "runtime"),
    ("requirements*.txt", "pip (Python)", "package_manager"),
    ("Pipfile", "Pipenv", "package_manager"),
    ("pyproject.toml", "Python Packaging", "package_manager"),
    ("pom.xml", "Maven", "package_manager"),
    ("build.gradle", "Gradle", "package_manager"),
    ("Gemfile", "Bundler (Ruby)", "package_manager"),
    ("go.mod", "Go Modules", "package_manager"),
    ("Cargo.toml", "Cargo (Rust)", "package_manager"),
    ("*.ps1", "PowerShell", "scripting"),
    ("*.sh", "Bash", "scripting"),
]


def detect() -> list[dict]:
    found = []
    seen: set[str] = set()
    repo_root = Path(".")

    for pattern, tech_name, category in INDICATORS:
        matches = list(repo_root.rglob(pattern))
        # Exclude .git and node_modules
        matches = [
            m for m in matches
            if ".git" not in m.parts and "node_modules" not in m.parts
        ]
        if matches and tech_name not in seen:
            seen.add(tech_name)
            found.append(
                {
                    "name": tech_name,
                    "category": category,
                    "detected_via": pattern,
                    "file_count": len(matches),
                }
            )

    return found


def main() -> None:
    technologies = detect()
    registry = {
        "schema_version": "1.0.0",
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "technologies": technologies,
    }
    Path(REGISTRY_PATH).write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(f"[tech_detector] Detected {len(technologies)} technologies → {REGISTRY_PATH}")
    for t in technologies:
        print(f"  • {t['name']} ({t['category']}) — {t['file_count']} file(s)")


if __name__ == "__main__":
    main()
