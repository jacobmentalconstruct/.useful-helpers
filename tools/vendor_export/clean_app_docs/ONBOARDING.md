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

## It is already pointed at a project

An installed instance is **bound to the folder it lives in** by the identity manifest
(`instance.json`) written at install time. It resolves its target structurally - no folder-name
guess, no marker file, no environment variable - and moving the pair together keeps the
relationship intact.

If you are running an uninstalled copy, set `SUITE_PROJECT_ROOT` to the project you want it to
manage. Where an instance exists, identity wins and a conflicting variable is refused.

To install a sidecar into another folder, use the **setup application** you received - not this
runtime. An installed instance operates on its one target; it does not install more sidecars.

The instance writes only its own home. Target files change only via a governed **Apply** tool you
deliberately invoke, and every such change is recorded in the ledger.

## Read order

1. `AGENTS.md` - product-neutral front door (any agent).
2. `README.md` - what the toolkit is + quick start.
3. `docs/ARCHITECTURE.md` - the structure (spine, governed seam, contracts, memory, playbooks).
4. `docs/TOOLS.md` - the capability catalog (what you can call, with examples).
   `docs/OPERATIONS.md` - how to drive them (sequencing, flags, trust levels).
5. `docs/PROJECT_GOVERNANCE.md` - the optional authority ceiling, engaged per project.

## Entrances

Invoke a launcher **by path** - they are not on `PATH`, but each resolves its own directory, so
the working directory you start from does not matter.

- **Front door:** `run.bat attach` (Windows) / `sh run.sh attach` (Linux, macOS)
- **GUI:** `run.bat ui` - **Project Snapshot:** `run.bat map`
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
