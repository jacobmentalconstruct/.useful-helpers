# Onboarding

**Cold-booting agent, do this first:** read `AGENTS.md`, then run `run.bat list` / `sh run.sh list`
(or `python -m src.app cli tool-list` from inside the instance) to see the live tool registry; then skim `README.md`,
`docs/ARCHITECTURE.md`, and `docs/TOOLS.md`.

## Read order
1. `AGENTS.md`  -  product-neutral front door (any agent).
2. `README.md`  -  what the toolkit is + quick start.
3. `docs/ARCHITECTURE.md`  -  the structure (spine, governed seam, contracts, memory, playbooks).
4. `docs/TOOLS.md`  -  the capability catalog (what you can call, with examples).
   `docs/OPERATIONS.md`  -  how to drive them (sequencing, flags, trust levels).
5. `docs/PROJECT_GOVERNANCE.md`  -  the optional authority ceiling, engaged per project.

## Entrances

**Invoke a launcher by path.** `run.bat` and `run.sh` are not on `PATH`; each resolves its own
directory and then changes into it, so the *working directory* you start from does not matter,
but the *path you type* must reach the launcher.

```
cd <target>
.useful-helpers\run.bat attach        :: Windows
sh .useful-helpers/run.sh attach      :: Linux / macOS
```
From inside the instance directory itself, `run.bat attach` and `sh run.sh attach` work.

- **Front door:** `run.bat attach` / `run.sh attach`
- **GUI:** `run.bat ui` / `run.sh ui`  -  **Project Snapshot:** `run.bat map`  -  **New project:** `run.bat plan`
- **CLI:** `run.bat cli ...` / `run.sh cli ...`  -  raw form `python -m src.app cli ...` requires the instance directory as the working directory
- **MCP (agents):** `run.bat mcp` / `run.sh mcp`
- **Playbooks:** `run.bat cli run-playbook --file playbooks/<name>.json`

## Memory is this project's memory
Record work with `journal add`; ground claims with `evidence attach`. Both start empty on a
fresh install and accumulate the history of **this** project.

## Conventions
- **Add a capability:** `stamp` a skeleton -> implement `run(args)` -> enrich `tool.json` -> it is
  auto-registered -> dogfood it (see `docs/ARCHITECTURE.md`).
- **Done = dogfooded:** a capability isn't done until you've used it through a real surface.
- **Generated:** `_artifacts/` and `config/registry.json` are regeneratable.
