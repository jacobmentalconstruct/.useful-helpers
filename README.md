# Useful Helpers  -  a governed toolkit for your project

A local toolkit of headless tools for understanding, changing, packaging, and remembering
work on the project this folder lives in - run `run.bat list` (or `python -m src.app cli
tool-list`) for the live catalog. Every tool is reachable by an **agent** (MCP) and a
**human** (GUI/CLI), and every call flows through one **governed** `invoke()` seam  - 
authority-checked and audit-logged.

## Start here
- **Agents:** read `AGENTS.md`  -  the product-neutral front door.
- **Humans:** `run.bat` (Windows) for the operator menu, or the commands below.

## Entrances
```bat
run.bat list                 :: list every tool
run.bat ui                   :: browse + run any tool (GUI)
run.bat map                  :: Project Snapshot  -  a shareable map/dump of a folder
run.bat plan                 :: cockpit  -  plan and build a new project from an intention
run.bat mcp                  :: agent entrance (MCP, JSON-RPC 2.0 over stdio)
python -m src.app cli tool-call --tool <id> --args-json "{...}"
python -m src.app cli run-playbook --file playbooks/<name>.json
python smoke_test.py         :: self-check
```

## Layout
- `src/`  -  the control plane (registry + governed `invoke()` seam + policy + event log - MCP + CLI - GUI).
- `tools/` - `apps/`  -  the capabilities. `config/`  -  the generated registry. `playbooks/`  -  reusable tool chains.
- `_docs/`  -  `ARCHITECTURE.md` (how it works), `TOOLS.md` (catalog), `OPERATIONS.md` (how to
  drive them), `ONBOARDING.md`, `PROJECT_GOVERNANCE.md`.

## Memory & governance
`journal` + `evidence` are **this project's** durable memory  -  empty until you use them.
Governance enforcement is always on and defaults to permissive; clamp it per project via
`config/governance.json` (see `_docs/PROJECT_GOVERNANCE.md`).
"# .useful-helpers" 
