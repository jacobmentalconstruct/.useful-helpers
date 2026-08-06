# tools/ — small re-homed CLI tools

One directory per tool. A `tools/*` entry is a **single-purpose headless CLI** (no GUI, or an
optional thin GUI). Anything carrying a substantial GUI or its own data store belongs in
`apps/` instead.

## The Tool Contract (every `tools/*` and `apps/*` satisfies)
1. **Headless CLI** — `cli.py` defines `run(args: dict) -> dict` decorated with
   `@tool_main` from `tools._toolkit`; the toolkit handles `--args-json` parsing and the
   `ok`/`error` JSON envelope, so a tool is just its logic. The seam calls
   `<interpreter> cli.py --args-json <json>` with the toolkit home on PYTHONPATH so the import
   resolves. See `tools/ping/` (minimal) and `tools/host_probe/` (fuller).

**Don't hand-write a new tool — generate it:** `cli tool-call --tool stamp --args-json
'{"id":"myTool","summary":"...","category":"...","authority":"Observe"}'` stamps
`tools/myTool/` (or `apps/` with `"kind":"app"`) ready to fill in.
2. **Manifest** — a `tool.json` (schema in `config/README.md`) so the registry can discover it.
   It declares `authority`, `operates_on`, and `writes` — the seam enforces the last for Observe
   tools (see `_docs/ARCHITECTURE.md` §5).
3. **Subprocess-only** — invoked by `core.invoke()` as a subprocess via the shared root
   `.venv`; never imported across package boundaries.
4. **Graceful** — non-zero exit + structured error on failure, never a silent crash.

See `tools/_template/` for the exemplar.
