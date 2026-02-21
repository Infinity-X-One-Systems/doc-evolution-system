# SINGULARITY PRIME — Enterprise Document Evolution & Autonomous Control Fabric

**Organization:** Infinity-X-One-Systems  
**Version:** 1.0.0  
**Authority:** Org-Wide Mandatory Baseline

---

## Overview

This repository implements the **Singularity Prime** governance, document evolution, and
orchestration fabric for the Infinity-X-One-Systems GitHub Enterprise Organization.
Every repository derived from `infinity-templates` inherits this fabric automatically.

---

## Repository Structure

```
.
├── .github/
│   ├── workflows/          # 9 mandatory CI/CD workflows
│   │   ├── pat.yml         # PAT protocol enforcement
│   │   ├── codeql.yml      # CodeQL security scanning
│   │   ├── dependency.yml  # Dependency vulnerability review
│   │   ├── state-machine.yml # State transition validation
│   │   ├── docs.yml        # Documentation + Pages deploy
│   │   ├── playwright.yml  # UI test suite
│   │   ├── chaos.yml       # Chaos engineering validation
│   │   ├── release.yml     # Automated release pipeline
│   │   └── admin-sync.yml  # Admin control plane sync
│   ├── CODEOWNERS          # Org-wide code ownership
│   └── branch-protection.json
│
├── singularity/
│   ├── blueprint/          # master_invocation.md, roadmap.json, architecture.md
│   ├── evolution/          # Living data: checklist, todo, tech registry, memory
│   ├── agents/             # 9 Python automation agents
│   ├── ui/                 # Pages enterprise dashboard (HTML/CSS/JS)
│   └── _STATE/             # state.json, history.json, transitions.json
│
├── org-sync/
│   └── admin_project_register.py  # GitHub GraphQL auto-registration
│
├── vscode/                 # VS Code settings + extension recommendations
├── singularity.code-workspace
└── bootstrap-singularity-enterprise.ps1
```

---

## Quick Start

### Bootstrap a new repository

```powershell
.\bootstrap-singularity-enterprise.ps1
```

### Run the evolution engine locally

```bash
python singularity/agents/evolution_engine.py
```

### Validate state machine

```bash
python singularity/agents/state_machine.py
```

---

## State Lifecycle

| State | Next Allowed State |
|---|---|
| `NEW_IDEA` | `DISCOVERY_RUNNING` |
| `DISCOVERY_RUNNING` | `EVOLUTION_COMPLETE` |
| `EVOLUTION_COMPLETE` | `BUILD_RUNNING` |
| `BUILD_RUNNING` | `VALIDATION` |
| `VALIDATION` | `APPROVAL` |
| `APPROVAL` | `RELEASED` |

---

## Governance

- All PRs require PAT validation, CodeQL, state-machine, docs, and Playwright checks.
- Branch protection is enforced via `.github/branch-protection.json`.
- CODEOWNERS ensures owner review on all sensitive paths.
- No secrets in code — use Vault or GitHub Secrets.

---

## Documentation

- [Master Invocation](singularity/blueprint/master_invocation.md)
- [Architecture](singularity/blueprint/architecture.md)
- [Roadmap](singularity/blueprint/roadmap.json)
- [Evolution README](singularity/evolution/README.md)
