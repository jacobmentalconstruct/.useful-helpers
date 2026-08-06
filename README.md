# Useful Helpers  -  a governed sidecar for your project

A local sidecar you **install into a project folder**. That folder becomes its target: the
sidecar maps it, works on it through a toolkit of headless tools, and keeps its own record
of both. Run `run.bat list` (or `python -m src.app cli tool-list`) for the live catalog.

Every tool is reachable by an **agent** (MCP) and a **human** (GUI/CLI), and every call flows
through one **governed** `invoke()` seam  -  authority-checked, containment-checked and
audit-logged. Whichever way a call arrives, it takes the same path and lands in the same record.

**The target never learns the sidecar exists.** Nothing is written into it, no pointer file, no
`.gitignore` line. Delete the sidecar folder and the project is exactly as it was  -  which is
what makes it safe to remove before shipping the project to its own users.

The sidecar has no target until it is installed into one, or given an explicit
`SUITE_PROJECT_ROOT`. It never infers a target from its surroundings; see
[AGENTS.md](AGENTS.md) for the rules.

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
