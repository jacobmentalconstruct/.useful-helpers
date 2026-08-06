# apps/ — larger re-homed applications

One directory per app. An `apps/*` entry carries a **substantial GUI and/or its own data
store**, but still satisfies the full **Tool Contract** (see `tools/README.md`): a headless
`cli.py` + a `tool.json`, so the agent entrance drives it without the GUI. The GUI is the
human skin over the same headless surface.

Each app stays a **self-owned package** — never merged into a monolith. Heavy or conflicting
dependencies may get an isolated env instead of the shared root `.venv`.

## Members
- `projectmapper` — Project Snapshot: a shareable, deterministic map/dump of a folder.
