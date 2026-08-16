# Useful Helpers  -  a governed sidecar for your project

A local sidecar you **install into one folder**. That folder becomes its target  -  code, records,
documents, mixed files, or empty. The sidecar reads it with a catalog of deterministic tools, all
running on your machine, and lets a human or an agent **inspect, transform and verify** it through
one governed seam.

**Today** `attach` maps the target and hands back a project map, a per-target workbench and an
ordered list of next calls. Human and agent each reach every tool through the same seam and can
see each other act.

**Not yet:** one compact orientation that human and agent can prove is the *same* revision, and a
change loop that shows you a diff before you approve it. Those are the next two tranches (T7 and
T8 in `.bcc/TRANCHE_PLAN.md`), and this README will say so plainly rather than early.

Run `run.bat list` / `sh run.sh list` for the live tool catalog.

Every tool is reachable by an **agent** (MCP) and a **human** (GUI/CLI), and every call flows
through one **governed** `invoke()` seam  -  authority-checked, containment-checked and
audit-logged. Whichever way a call arrives, it takes the same path and lands in the same record.

**The target never learns the sidecar exists.** The sidecar writes no trace of *itself* into the
target: no pointer file, no `.gitignore` line, no config key. Delete the sidecar folder and
**every trace of the instrument is gone**  -  which is what makes it safe to remove before shipping
the project to its own users.

Two different things, and it matters that they are not confused:

| | |
|---|---|
| **Sidecar footprint** | one folder, `.useful-helpers/`. Removing it restores the target to a state where nothing knows the sidecar was ever here. |
| **Your work** | a governed **Apply** operation modifies target files deliberately  -  editing them is the point. Those changes are **yours**, they persist after removal, and removing the sidecar does not undo them. |

So "delete the folder and the project is exactly as it was" is true of the *instrument*, and
false of any change you asked it to make. Apply is preview-first, confined to a declared write
scope, and recorded in the ledger with the client that requested it.

The sidecar is bound to its target by an identity manifest written at install time
(`instance.json`), which records where the target is *relative* to the instance. Move the pair
together and the relationship survives; there is no basename guess, no marker file and no
environment inference. Uninstalled, there is no target and calls refuse rather than guess.

## Start here
- **Agents:** read `AGENTS.md`  -  the product-neutral front door.
- **Humans:** `run.bat` (Windows) or `run.sh` (Linux/macOS). Invoke either **by path**  -  they are
  not on `PATH`, but each resolves its own directory, so the working directory you start from
  does not matter.

## Entrances
```bat
run.bat attach               :: what is this target, and what should I do next
run.bat list                 :: list every tool
run.bat ui                   :: browse + run any tool (GUI)
run.bat map                  :: Project Snapshot  -  a shareable map/dump of a folder
run.bat plan                 :: cockpit  -  plan and build a new project from an intention
run.bat mcp                  :: agent entrance (MCP, JSON-RPC 2.0 over stdio)
run.bat smoke                :: verify this installation
```
From the target root, prefix the path: `.useful-helpers\run.bat attach` or
`sh .useful-helpers/run.sh attach`. Underneath, each launcher `cd`s to its own directory and
calls `python -m src.app`.

## Layout
- `src/`  -  the control plane (registry + governed `invoke()` seam + policy + event log - MCP + CLI - GUI).
- `tools/` - `apps/`  -  the capabilities. `config/`  -  the generated registry. `playbooks/`  -  reusable tool chains.
- `docs/`  -  `ARCHITECTURE.md` (how it works), `TOOLS.md` (catalog), `OPERATIONS.md` (how to
  drive them), `ONBOARDING.md`, `PROJECT_GOVERNANCE.md`.

## Memory & governance
`journal` + `evidence` are **this project's** durable memory  -  empty until you use them.
Governance enforcement is always on and defaults to permissive; clamp it per project via
`config/governance.json` (see `docs/PROJECT_GOVERNANCE.md`).
"# .useful-helpers" 
