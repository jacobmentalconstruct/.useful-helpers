# ChatWindowKERNAL Tool Contract

Status: contract reviewed; implementation pending; layout not final

Date: 2026-08-03

## Reference Dependency Rule

Reference app reviewed:

`_PARTS-FOR-PLANS/_ChatWindowKERNAL/`

Primary files reviewed:

- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/README.md`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/app.py`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/config/`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/src/shell/`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/src/ui/`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/src/runtime/`
- `_PARTS-FOR-PLANS/_ChatWindowKERNAL/tool_packages/`

The locators in this document and in
`src/useful_helpers/tools/chat_window_kernal/adapter.py` are temporary review
anchors. They may guide implementation, but the Useful Helpers runtime must not
import from, read from, or require the parts-bin app.

Runtime artifacts under reference `state/`, `logs/`, and `runtime/` are
provenance only. They must not become Useful Helpers runtime dependencies.

## Layout Rework Rule

The inspected ChatWindowKERNAL layout is not final. It functions in a
perfunctory, non-chat way today: plain role/text transcript appends, a basic text
input, command-like send behavior, and utility-heavy workspace panels. Useful
Helpers must not accept this as the final chat UX; a later design tranche must
define a real chat UX with conversational message objects, visual message grouping,
streaming/progress states, tool-call and HITL affordances, input ergonomics, and
how it coexists with the explorer-first workbench.

## Reference Frailties Found

- Reference layout is not final and currently feels perfunctory/non-chat despite README chat-first claims.
- Transcript rendering is plain role/text appending, not a finished conversational message surface.
- Reference includes checked-in runtime state databases, crash reports, logs, and snapshots that must remain provenance only.
- Vendored Mindshard code and numpy dependency are too broad to import into Useful Helpers without an explicit adapter tranche.
- Debug crash-test controls and `enable_debug_logging=true` must not ship blindly into the Useful Helpers workbench.

## Tool Done State

ChatWindowKERNAL integration is done when Useful Helpers can expose a polished
optional chat/agent-host workspace that does not replace the explorer-first
front door; provides real conversational message rendering for user, assistant,
system, tool, error, and HITL events; preserves draft and session state
intentionally; supports model/loop/session controls only through local
contracts; runs background work through a queue-safe task manager; surfaces
activity/events/data hooks/tool executions/inspector state in a coherent
secondary workspace; writes runtime snapshots and crash reports without leaking
reference state databases; keeps vendored agent runtime imports behind a single
optional adapter seam; and runs entirely from local Useful Helpers modules with
no runtime dependency on the parts-bin reference app.

## Capability Map

### Chat Layout Rework Required

Target outcome:

Before implementation, replace the perfunctory reference layout with a real chat
UX specification that fits the Useful Helpers explorer-first workbench.

Reference anchors:

- README `chat-first layout` at line 3
- `class ChatPanel` at line 16
- `def build` at line 54
- `self._transcript = tk.Text` at line 128
- `self._input = tk.Text` at line 139
- `def append_message` at line 365
- `Observable chat shell` at line 68

Done when:

The layout rework rule above has a concrete accepted design tranche.

### Bootstrap Host Kernel

Target outcome:

Use a thin entrypoint to build shell context, services, root window, mounted
panels, polling, and shutdown.

Reference anchors:

- `from src.shell.app_kernel import launch` at line 5
- `def main` at line 8
- `class AppKernel` at line 53
- `def start` at line 83
- `def _build_services` at line 112
- `def _build_runtime_services` at line 139

### Compose Chat And Workspace Shell

Target outcome:

Mount an optional primary chat surface and secondary workspace while preserving
the existing explorer-first workbench.

Reference anchors:

- `class MainWindow` at line 26
- `class PanedShell` at line 13
- `def _mount_panels` at line 202
- `class WorkspacePanel` at line 25
- `def refresh` at line 92
- `secondary_panel_width` at line 7

### Render Conversational Messages

Target outcome:

Render user, assistant, system, tool, error, status, and HITL messages as
structured conversation objects rather than plain transcript appends.

Reference anchors:

- `def append_message` at line 365
- `def _sync_agent_chat_output` at line 314
- `def _handle_send_message` at line 347

### Capture Chat Input And Controls

Target outcome:

Provide draft input, send shortcut/button, stop, pause/resume, model picker,
loop picker, and session manager controls.

Reference anchors:

- `def get_draft_text` at line 381
- `def _handle_send_clicked` at line 414
- `submit_user_turn` at line 358
- `class AgentSnapshot` at line 44
- `class HostAgentController` at line 85

### Manage Sessions Models And Loops

Target outcome:

Expose current session, available sessions, model/loop choices, hardware
summary, and session CRUD through local contracts.

Reference anchors:

- `class SessionSnapshot` at line 39
- `class HostSessionController` at line 32
- `class SessionManagerDialog` at line 27
- `ECHO_MODEL` at line 21

### Host Agent Turns And HITL

Target outcome:

Submit turns, parse slash commands, run/pause/stop/resume agent work, and
resolve human approval gates.

Reference anchors:

- `class AgentSnapshot` at line 44
- `class HostAgentController` at line 85
- `def _parse_user_turn` at line 700
- `class AgentHudTab` at line 16

### Discover And Run Tool Packages

Target outcome:

Discover portable manifest-plus-runner tool packages, execute them with
arguments, and track execution history.

Reference anchors:

- `class ToolRuntimeSnapshot` at line 49
- `class PackageToolService` at line 66
- `def discover_tool_packages` at line 25
- `def invoke_tool` at line 55
- `Portable tool packages` at line 3
- `class ToolsTab` at line 17
- `def _run_tool` at line 441

### Show Activity Events Hooks And Inspector

Target outcome:

Surface runtime events, previewable data hooks, and widget registry inspection
for debugging and observability.

Reference anchors:

- `class ActivityStream` at line 37
- `class DataHookCatalog` at line 30
- `def _register_data_hooks` at line 608
- `class EventsTab` at line 17
- `class InspectorTab` at line 17

### Queue Background Tasks

Target outcome:

Run long operations off the UI thread and hand results back through a predictable
polling/drain path.

Reference anchors:

- `class TaskManager` at line 66
- `class EventBus` at line 31
- `def _poll_runtime` at line 275

### Persist State And Runtime Snapshots

Target outcome:

Persist window/UI/session state and write runtime snapshots for debugging
without carrying old reference state files.

Reference anchors:

- `class StateManager` at line 57
- `class RuntimeSnapshotBuilder` at line 21
- `def _save_snapshot` at line 537
- `def _persist_state` at line 738
- `def _shutdown` at line 695

### Structured Logging And Crash Reports

Target outcome:

Configure logs and crash reports with safe defaults and without shipping
reference debug crash controls.

Reference anchors:

- `def configure_logging` at line 19
- `class CrashHandler` at line 29
- `enable_debug_logging` at line 7

### Optional Mindshard Adapter Seam

Target outcome:

Keep vendored agent runtime imports behind one optional adapter seam with echo
fallback and explicit dependency gates.

Reference anchors:

- `numpy>=2.0,<3.0` at line 1
- `class MindshardAdapter` at line 39
- `def _load_imports` at line 357
- `def ensure_bootstrap` at line 25

Done when:

Useful Helpers does not import vendored Mindshard or require numpy unless a
later tranche explicitly accepts that integration.

## Implementation Notes

- ChatWindowKERNAL is a reference for host-kernel and observability patterns,
  not a finished UI design.
- The Useful Helpers front door remains the folder explorer.
- Any chat integration must be optional or tool/workspace scoped until accepted
  as product shape.
- Checked-in reference databases, logs, snapshots, and crash reports are not
  migration inputs.
- The source spelling `KERNAL` is preserved in locators and tool key because it
  is the actual folder/app spelling.
