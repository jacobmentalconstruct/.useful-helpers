# config/ — the generated registry + domain cartridges

`registry.json` here is **derived state** — regenerated from the `tool.json` manifests under
`tools/` and `apps/` by `src/core/registry.py` (discoverable, owned, regeneratable via
`cli registry-refresh`; never hand-edited). It is the single source of truth every entrance
(MCP server, CLI, GUI) reads. `cartridges/` holds the domain knowledge `attach` selects from
(see `cartridges/README.md`).

## Manifest schema (each `tool.json`, mirrored into `registry.json`)

| Field | Meaning |
|---|---|
| `id` | unique tool id (e.g. `attach`, `file_tree`) |
| `summary` | one-line description |
| `category` | grouping (e.g. `introspection`, `code-intel`, `memory`, `pdf`) |
| `authority` | `Observe` (read-only) · `Sandbox` (isolated execute) · `Apply` (writes for real) |
| `operates_on` | the tool's subject: `project` (the work target) or `toolkit` |
| `writes` | what it may write: `none` · `toolkit` · `target` — enforced at the seam for Observe tools |
| `invocation` | `{ "interpreter": "${ROOT_VENV_PYTHON}", "entry": "tools/<id>/cli.py" }` — the seam calls `<interpreter> <entry> --args-json <json>` |
| `input_schema` | JSON-schema of accepted arguments |
| `output_shape` | expected structured result shape |

The generated catalog lives in `_docs/TOOLS.md` (`cli docs-refresh`).

## `governance.json` — the authority policy

`governance.json` is **committed config** (not generated). It sets the seam's authority
**ceiling** — the highest authority `invoke()` will run:

```json
{ "max_authority": "Apply" }
```

- `Observe` → only read-only tools run · `Sandbox` → + isolated execute · `Apply` → everything (**default**).
- Resolution at the seam: env `SUITE_MAX_AUTHORITY` → this file → default `Apply`. A per-call
  `allow=` argument can only *tighten* it. Denied calls are blocked and recorded in the event log
  (`tools/event_log`). Ships permissive so nothing is blocked until you (or a caller) clamp it.
