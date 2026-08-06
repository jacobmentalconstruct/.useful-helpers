# Onboarding

**Cold-booting agent, do this first:** read `AGENTS.md`, then run `run.bat list`
(or `python -m src.app cli tool-list`) to see the live tool registry; then skim `README.md`,
`_docs/ARCHITECTURE.md`, and `_docs/TOOLS.md`.

## Read order
1. `AGENTS.md`  -  product-neutral front door (any agent).
2. `README.md`  -  what the toolkit is + quick start.
3. `_docs/ARCHITECTURE.md`  -  the structure (spine, governed seam, contracts, memory, playbooks).
4. `_docs/TOOLS.md`  -  the capability catalog (what you can call, with examples).
   `_docs/OPERATIONS.md`  -  how to drive them (sequencing, flags, trust levels).
5. `_docs/PROJECT_GOVERNANCE.md`  -  the optional authority ceiling, engaged per project.

## Entrances
- **GUI:** `python -m src.app ui` / `run.bat ui`  -  **Project Snapshot:** `run.bat map`  -  **New project:** `run.bat plan`
- **CLI:** `python -m src.app cli ...`
- **MCP (agents):** `python -m src.app mcp`
- **Playbooks:** `python -m src.app cli run-playbook ...`

## Memory is this project's memory
Record work with `journal add`; ground claims with `evidence attach`. Both start empty on a
fresh install and accumulate the history of **this** project.

## Conventions
- **Add a capability:** `stamp` a skeleton -> implement `run(args)` -> enrich `tool.json` -> it is
  auto-registered -> dogfood it (see `_docs/ARCHITECTURE.md`).
- **Done = dogfooded:** a capability isn't done until you've used it through a real surface.
- **Generated:** `_artifacts/` and `config/registry.json` are regeneratable.
