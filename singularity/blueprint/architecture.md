# Singularity Prime — Architecture

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│           OPERATOR LAYER                                        │
│  Mobile / VSCode / Copilot / ChatGPT / Vizual-X                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ GitHub Issue
┌──────────────────────────▼──────────────────────────────────────┐
│           ADMIN CONTROL PLANE                                   │
│  infinity-admin-control-plane repository                        │
│  GitHub Project State Engine                                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Webhook
┌──────────────────────────▼──────────────────────────────────────┐
│           ORCHESTRATION LAYER                                   │
│  Infinity-Orchestrator GitHub App                               │
│  Sovereign Mesh Node                                            │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Agent Invocation
┌──────────────────────────▼──────────────────────────────────────┐
│           SINGULARITY PRIME EVOLUTION ENGINE                    │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ State Machine│  │ PAT Validator│  │ Doc Validator        │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Tech Detector│  │ GitHub Sync  │  │ Evolution Engine     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Auto-Commit → PR
┌──────────────────────────▼──────────────────────────────────────┐
│           VALIDATION MATRIX (CI Gate)                           │
│  PAT ✔  CodeQL ✔  Docs ✔  State ✔  Playwright ✔               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Pass → Approval Column
┌──────────────────────────▼──────────────────────────────────────┐
│           RELEASE & SYNC LAYER                                  │
│  GitHub Release  ─►  Vault Sync                                │
│  Memory Update   ─►  Google Workspace Sync                     │
│  Pages Dashboard ─►  Admin Control Plane Update                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### Agents (`singularity/agents/`)

| Agent | Responsibility |
|---|---|
| `evolution_engine.py` | Orchestrates the full doc-evolution lifecycle |
| `state_machine.py` | Validates and enforces allowed state transitions |
| `pat_validator.py` | Enforces PAT protocol across all PRs |
| `doc_validator.py` | Validates documentation completeness and structure |
| `tech_detector.py` | Auto-detects technology stack for registry |
| `github_sync.py` | Syncs project state with GitHub Projects and Issues |
| `google_workspace.py` | Gmail, Drive, and Sheets integration |
| `vault_agent.py` | Vault read/write for secrets and release data |
| `mesh_hook.py` | Sends events to the Sovereign Mesh Node |

### State Files (`singularity/_STATE/`)

| File | Purpose |
|---|---|
| `state.json` | Current and next state of the repository lifecycle |
| `history.json` | Append-only log of all state transitions |
| `transitions.json` | Allowed state transition graph |

### Evolution Data (`singularity/evolution/`)

| File | Purpose |
|---|---|
| `checklist.json` | Governance checklist items and completion status |
| `todo.json` | Active task queue |
| `index.json` | Master index of all evolution artefacts |
| `tech_registry.json` | Detected and registered technology components |
| `sop_registry.json` | Standard Operating Procedures registry |
| `memory_registry.json` | Persistent memory log (releases, benchmarks, risks) |
| `validation_report.json` | Latest validation matrix results |

---

## Security Model

- All PRs require PAT validation before merge.
- CodeQL scans run on every PR and weekly.
- Dependency review blocks high-severity vulnerabilities.
- Branch protection enforces all status checks.
- CODEOWNERS ensures owner review on sensitive paths.
- Vault agent handles all secrets — no secrets in code.

---

## Scalability Hooks

- All JSON registries follow a `schema_version` field for forward compatibility.
- All agents are idempotent and safe to re-run.
- Memory registry supports append-only growth.
- Mesh hook is async and non-blocking.
- Admin sync is triggered on every push to `main`.
