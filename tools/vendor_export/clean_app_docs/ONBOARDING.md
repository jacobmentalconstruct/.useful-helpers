# Onboarding

This is a clean, standalone copy of the toolkit - no history carried from where it was built. Its
memory starts empty and accumulates **your** project's work.

**Cold-booting agent, do this first:** read `AGENTS.md`, then run `run.bat list`
(or `python -m src.app cli tool-list`) to see the live tool registry; then skim `README.md`,
`_docs/ARCHITECTURE.md`, and `_docs/TOOLS.md`. Finally run `attach` to map the work target.

## Install (once)

The spine runs on plain Python; for dependency-backed tools (PDF, embeddings) build the env:

```
setup_env.bat                                   (Windows)
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
```

## Point it at a project

Set `SUITE_PROJECT_ROOT` to the project you want the toolkit to manage (default: the current
directory). The toolkit writes only its own home; the target changes only via Apply tools you
invoke. To install it into a project as a sidecar folder, use the `sidecar_install` tool.

## Read order

1. `AGENTS.md` - product-neutral front door (any agent).
2. `README.md` - what the toolkit is + quick start.
3. `_docs/ARCHITECTURE.md` - the structure (spine, governed seam, contracts, memory, playbooks).
4. `_docs/TOOLS.md` - the capability catalog (what you can call, with examples).
   `_docs/OPERATIONS.md` - how to drive them (sequencing, flags, trust levels).
5. `_docs/PROJECT_GOVERNANCE.md` - the optional authority ceiling, engaged per project.

## Entrances

- **GUI:** `python -m src.app ui` / `run.bat ui` - **Project Snapshot:** `run.bat map`
- **CLI:** `python -m src.app cli ...`
- **MCP (agents):** `python -m src.app mcp`
- **Playbooks:** `python -m src.app cli run-playbook ...`

## Memory is your project's memory

Record work with `journal add`; ground claims with `evidence attach`. Both start empty on this
fresh copy and accumulate the history of the project you point it at.

## Conventions

- **Add a capability:** `stamp` a skeleton -> implement `run(args)` -> enrich `tool.json` -> it is
  auto-registered -> dogfood it (see `_docs/ARCHITECTURE.md`).
- **Done = dogfooded:** a capability isn't done until you've used it through a real surface.
- **Generated:** `_artifacts/` and `config/registry.json` are regeneratable.
