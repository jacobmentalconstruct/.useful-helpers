# ChatWindowKERNAL

`ChatWindowKERNAL` is a reusable Tkinter desktop shell built around a chat-first layout, persistent UI state, structured logging, live widget introspection, and safe background task plumbing. It now runs as the host shell for a vendored Mindshard runtime while keeping agent imports out of `src/ui/`.

## Features

- Chat-centered main window with expandable side panel
- Session-aware chat header with model picker, loop picker, runtime status, hardware summary, and session manager modal
- Tabbed secondary workspace with `Agent HUD`, `Tools`, `Events`, and `Inspector`
- Persistent window geometry, panel visibility, and draft state
- Theme system with a soft light palette and an atmospheric dark variant
- Structured logging and crash reports
- Thread-safe task execution with queue-based UI handoff
- Live widget registry, activity stream, and data-hook catalog
- Runtime snapshot export for debugging and later agent integration
- Portable `tool_packages/` discovery for tool-first host prep
- Vendored Mindshard runtime seam with session control, slash-command support, pause/stop checkpoints, and evidence summaries

## Themes

- `harbor_mist`: a low-glare coastal light theme with sea-glass accents
- `cinder_tide`: a dark variant with charcoal, ember, and teal highlights

## Run

```powershell
python app.py
```

Or use:

```powershell
run.bat
```

## Test

```powershell
python -m unittest discover -s tests -v
```

## Structure

- `app.py`: thin bootstrap entrypoint
- `config/`: app, logging, and UI defaults
- `state/`: persisted window, layout, and session state
- `runtime/`: snapshots and crash reports
- `src/shell/`: orchestration, persistence, registry, tasks, and lifecycle
- `src/runtime/`: host-owned agent/tool contracts, activity stream, data hooks, adapters, and tool runtime
- `src/ui/`: Tkinter composition, themes, and panels
- `tool_packages/`: portable tool manifests and runners
- `scripts/`: developer/bootstrap helpers only
- `tests/`: isolated subsystem tests

## Runtime Host

- `src/runtime/contracts/`: typed contracts for agent, session, and tool seams
- `src/runtime/agent_host/`: host controllers for live agent turns, session state, and hardware probes
- `src/runtime/tools/`: tool discovery, execution tracking, and runtime snapshots
- `src/runtime/adapters/mindshard_adapter.py`: the only host-owned adapter allowed to import vendored Mindshard code
- `src/runtime/vendors/mindshard/`: vendored upstream runtime copy for agent, graph/projector, evidence bag, and memory layers
- `src/ui/dialogs/session_manager_dialog.py`: session CRUD modal mounted from the chat header

## Workspace Tabs

- `Agent HUD`: controller state, recent steps, pending approvals, evidence summary, and key data hooks
- `Tools`: tool catalog, execution history, arguments, and detail views
- `Events`: live runtime activity with family/level filters
- `Inspector`: structural widget registry diagnostics
