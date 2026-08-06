# Project Governance (optional)

The Useful Helpers toolkit enforces an **authority ceiling** on every tool call:

| Authority | Means |
|-----------|-------|
| **Observe** | read-only (scans, searches, reports) |
| **Sandbox** | writes only to temp / `_artifacts/` |
| **Apply**   | writes real files, git, external targets |

Enforcement is **always on** and every call is audit-logged (`tools/event_log`). This is
plumbing  -  it travels with the toolkit and cannot be turned off.

What is **optional** is how tightly you clamp it. By default the ceiling is **Apply**
(permissive  -  the toolkit does whatever a tool is rated for). Engage constraints deliberately:

- **Per session:** `SUITE_MAX_AUTHORITY=Observe` (or `Sandbox`) in the environment.
- **Per project:** set `"max_authority"` in `config/governance.json`:
  ```json
  { "max_authority": "Sandbox" }
  ```
- A per-call `allow=` can only **tighten** the ceiling, never loosen it.

Resolution order: `SUITE_MAX_AUTHORITY` env -> `config/governance.json` -> default `Apply`.

## Authoring a per-project contract

There is **no binding contract imposed by default.** If a project deserves explicit rules
(e.g. "this is a production repo  -  Observe/Sandbox only, no direct commits"), record them here
and set the matching ceiling above. Until you do, this layer stays dormant and out of your way.
