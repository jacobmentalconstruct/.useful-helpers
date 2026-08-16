# Useful Helpers - a governed toolkit you can point at any project

This is a clean, standalone copy of the toolkit. It carries no history from wherever it was
built - its memory (`journal` / `evidence`) starts empty and fills with **your** project's work.
A local toolkit of headless tools for understanding, changing, packaging, and remembering a
codebase, dataset, or body of records. Every tool is reachable by an **agent** (MCP) and a
**human** (GUI/CLI), and every call flows through one **governed** `invoke()` seam -
authority-checked and audit-logged.

## Install (once, at this location)

The control plane (`src/`) is Python-standard-library only, so `tool-list` and most tools run on
plain Python immediately. For the tools with dependencies (PDF, embeddings), create the env:

```bat
setup_env.bat                     :: Windows - builds .venv and installs requirements
:: or, cross-platform:
python -m venv .venv && .venv\Scripts\pip install -r requirements.txt
```

## Point it at a project

The toolkit operates on a **work target**. By default that is the current directory; override it
so the toolkit can sit anywhere and manage a project elsewhere:

```bat
set SUITE_PROJECT_ROOT=C:\path\to\your\project     :: the toolkit reads/writes THAT project
```

The toolkit writes no trace of *itself* into the target: no pointer file, no `.gitignore` line,
no config key. Delete this folder and every trace of the instrument is gone.

That is a rule about the instrument's footprint, not about your work. Target files **are**
modified by a governed **Apply** tool you deliberately invoke - editing them is the point - and
every such change is preview-first, confined to a declared write scope, and recorded in the
ledger. Those changes are yours and survive removing the sidecar.

To install a sidecar into another folder, use the **setup application** you received. It writes
exactly one `.useful-helpers/` directory and nothing else. An installed instance belongs to one
target and does not install further sidecars.

## Start here

- **Agents:** read `AGENTS.md` - the product-neutral front door. Then `attach` to map the target.
- **Humans:** `run.bat` (Windows) for the operator menu, or the commands below.

## Entrances

```bat
run.bat list                 :: list every tool (the live catalog - authoritative)
run.bat ui                   :: browse + run any tool (GUI)
run.bat map                  :: Project Snapshot - a shareable map/dump of a folder
run.bat mcp                  :: agent entrance (MCP, JSON-RPC 2.0 over stdio)
python -m src.app cli tool-list
python -m src.app cli tool-call --tool <id> --args-json "{...}"
python -m src.app cli run-playbook --file playbooks/<name>.json
python smoke_test.py         :: self-check
```

## Layout

- `src/` - the control plane (registry + governed `invoke()` seam + policy + event log; MCP + CLI + GUI).
- `tools/` + `apps/` - the capabilities. `config/` - the generated registry. `playbooks/` - reusable tool chains.
- `_docs/` - `ARCHITECTURE.md` (how it works), `TOOLS.md` (catalog), `OPERATIONS.md` (how to drive them),
  `ONBOARDING.md`, `PROJECT_GOVERNANCE.md`.

## Memory and governance

`journal` + `evidence` are **your** project's durable memory - empty on this fresh copy until you
use them. Governance enforcement is always on and defaults to permissive; clamp it per project via
`config/governance.json` (see `_docs/PROJECT_GOVERNANCE.md`).

## How many tools?

Whatever `run.bat list` reports. The catalog is generated from the manifests in `tools/`, so the
live list is the only authoritative count - this document deliberately does not name a number.
