"""ChatWindowKERNAL tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the
ChatWindowKERNAL behavior Useful Helpers may re-home from the reference app
before runtime adapters start exposing chat, agent-host, or workspace surfaces.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
ChatWindowKERNAL tool no longer depends on the reference app for design
recovery, runtime modules must not import from, read from, or require the parts
bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "chat_window_kernal"
TOOL_LABEL = "ChatWindowKERNAL"
STATUS = "contract reviewed; implementation pending; layout not final"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_ChatWindowKERNAL/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}app.py"
REFERENCE_README_PATH = f"{SOURCE_REFERENCE}README.md"
REFERENCE_REQUIREMENTS_PATH = f"{SOURCE_REFERENCE}requirements.txt"
REFERENCE_CONFIG_PATH = f"{SOURCE_REFERENCE}config/app_config.json"
REFERENCE_UI_DEFAULTS_PATH = f"{SOURCE_REFERENCE}config/ui_defaults.json"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each "
    "ChatWindowKERNAL capability is re-homed into Useful Helpers runtime "
    "modules, remove parts-bin references from runtime tool code and keep "
    "historical provenance in docs only."
)

LAYOUT_REWORK_RULE = (
    "The inspected ChatWindowKERNAL layout is not final. It functions in a "
    "perfunctory, non-chat way today: plain role/text transcript appends, a "
    "basic text input, command-like send behavior, and utility-heavy workspace "
    "panels. Useful Helpers must not accept this as the final chat UX; a later "
    "design tranche must define a real chat UX with conversational message objects, visual message "
    "grouping, streaming/progress states, tool-call and HITL affordances, input "
    "ergonomics, and how it coexists with the explorer-first workbench."
)

DONE_STATE = (
    "ChatWindowKERNAL integration is complete when Useful Helpers can expose a "
    "polished optional chat/agent-host workspace that does not replace the "
    "explorer-first front door, provides real conversational message rendering "
    "for user, assistant, system, tool, error, and HITL events, preserves draft "
    "and session state intentionally, supports model/loop/session controls only "
    "through local contracts, runs background work through a queue-safe task "
    "manager, surfaces activity/events/data hooks/tool executions/inspector "
    "state in a coherent secondary workspace, writes runtime snapshots and crash "
    "reports without leaking reference state databases, keeps vendored agent "
    "runtime imports behind a single optional adapter seam, and runs entirely "
    "from local Useful Helpers modules with no runtime dependency on the "
    "parts-bin reference app."
)

REFERENCE_FRAILTIES = (
    "Reference layout is not final and currently feels perfunctory/non-chat despite README chat-first claims.",
    "Transcript rendering is plain role/text appending, not a finished conversational message surface.",
    "Reference includes checked-in runtime state databases, crash reports, logs, and snapshots that must remain provenance only.",
    "Vendored Mindshard code and numpy dependency are too broad to import into Useful Helpers without an explicit adapter tranche.",
    "Debug crash-test controls and enable_debug_logging=true must not ship blindly into the Useful Helpers workbench.",
)


def locator(reference_path: str, label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, reference_path)


LOC_README_IDENTITY = locator(
    REFERENCE_README_PATH,
    "README identity",
    "ChatWindowKERNAL",
    1,
    "Names the reference shell and preserves the source spelling.",
)
LOC_README_CHAT_FIRST = locator(
    REFERENCE_README_PATH,
    "README chat-first claim",
    "chat-first layout",
    3,
    "Claims a chat-first layout with persistent UI state and host runtime seams.",
)
LOC_README_FEATURES = locator(
    REFERENCE_README_PATH,
    "README features",
    "## Features",
    5,
    "Lists chat header, workspace tabs, logging, task plumbing, snapshots, tools, and Mindshard seam.",
)
LOC_README_WORKSPACE = locator(
    REFERENCE_README_PATH,
    "workspace tabs",
    "## Workspace Tabs",
    64,
    "Describes Agent HUD, Tools, Events, and Inspector tabs.",
)
LOC_BOOTSTRAP = locator(
    REFERENCE_APP_PATH,
    "bootstrap launch",
    "from src.shell.app_kernel import launch",
    5,
    "Shows the standalone entrypoint delegates to the shell app kernel.",
)
LOC_MAIN = locator(
    REFERENCE_APP_PATH,
    "main entrypoint",
    "def main",
    8,
    "Launches the reference app from its folder root.",
)
LOC_REQUIRE_NUMPY = locator(
    REFERENCE_REQUIREMENTS_PATH,
    "numpy dependency",
    "numpy>=2.0,<3.0",
    1,
    "Records the reference runtime's numpy dependency through vendored Mindshard pieces.",
)
LOC_APP_ID = locator(
    REFERENCE_CONFIG_PATH,
    "app id",
    "chat_window_kernal",
    2,
    "Defines reference app id and preserves source spelling.",
)
LOC_APP_CONFIG = locator(
    REFERENCE_CONFIG_PATH,
    "app name",
    "ChatWindowKERNAL",
    3,
    "Defines reference app name.",
)
LOC_DEBUG_CONFIG = locator(
    REFERENCE_CONFIG_PATH,
    "debug logging default",
    "enable_debug_logging",
    7,
    "Enables debug/crash-test behavior in the reference config.",
)
LOC_UI_DEFAULTS = locator(
    REFERENCE_UI_DEFAULTS_PATH,
    "secondary panel defaults",
    "secondary_panel_width",
    7,
    "Defines default secondary workspace visibility and width.",
)
LOC_KERNEL = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "app kernel",
    "class AppKernel",
    53,
    "Owns startup, runtime polling, panel mounting, shutdown, and host services.",
)
LOC_KERNEL_START = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "kernel start",
    "def start",
    83,
    "Creates Tk root, mounts panels, restores state, installs crash handler, and enters mainloop.",
)
LOC_BUILD_SERVICES = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "service construction",
    "def _build_services",
    112,
    "Builds event bus, lifecycle, state, activity stream, data hooks, status, tasks, registry, layout, panels, and tool service.",
)
LOC_RUNTIME_SERVICES = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "runtime services",
    "def _build_runtime_services",
    139,
    "Builds Mindshard adapter plus host session and agent controllers.",
)
LOC_MOUNT_PANELS = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "panel mounting",
    "def _mount_panels",
    202,
    "Mounts ChatPanel as primary and WorkspacePanel as secondary.",
)
LOC_POLL = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "runtime polling",
    "def _poll_runtime",
    275,
    "Polls task results, session header, agent output, status, workspace refresh, and shutdown requests.",
)
LOC_SYNC_AGENT_OUTPUT = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "agent output sync",
    "def _sync_agent_chat_output",
    314,
    "Appends agent/system messages into the chat panel from agent snapshots.",
)
LOC_SEND_MESSAGE = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "send message",
    "def _handle_send_message",
    347,
    "Appends user message, clears input, records activity, submits agent turn, and sets status.",
)
LOC_SUBMIT_TURN = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "submit user turn",
    "submit_user_turn",
    358,
    "Hands user text to the agent controller.",
)
LOC_RUN_TOOL = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "run tool",
    "def _run_tool",
    441,
    "Starts a tool package from the workspace panel.",
)
LOC_SAVE_SNAPSHOT = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "save snapshot",
    "def _save_snapshot",
    537,
    "Writes a manual runtime snapshot from the header.",
)
LOC_DATA_HOOKS = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "data hook registration",
    "def _register_data_hooks",
    608,
    "Registers shell, session, widget, status, task, panel, UI, and activity previews.",
)
LOC_SHUTDOWN = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "shutdown",
    "def _shutdown",
    695,
    "Persists state, shuts down tasks, disposes panels, closes adapter, and destroys root.",
)
LOC_PERSIST = locator(
    f"{SOURCE_REFERENCE}src/shell/app_kernel.py",
    "persist state",
    "def _persist_state",
    738,
    "Captures window, UI, session state, and writes shutdown snapshot.",
)
LOC_CHAT_PANEL = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "chat panel",
    "class ChatPanel",
    16,
    "Owns the current chat surface composition and callbacks.",
)
LOC_CHAT_BUILD = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "chat panel build",
    "def build",
    54,
    "Builds session header, model/loop pickers, runtime/hardware lines, transcript, input, send/stop/pause buttons.",
)
LOC_TRANSCRIPT = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "plain transcript",
    "self._transcript = tk.Text",
    128,
    "Uses a Tk Text widget as the transcript surface.",
)
LOC_INPUT = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "plain input",
    "self._input = tk.Text",
    139,
    "Uses a Tk Text widget as the draft input.",
)
LOC_APPEND_MESSAGE = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "append message",
    "def append_message",
    365,
    "Appends role and text blocks to the transcript.",
)
LOC_DRAFT_STATE = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "draft state",
    "def get_draft_text",
    381,
    "Reads draft text with end-1c trimming.",
)
LOC_HANDLE_SEND = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/chat_panel.py",
    "send clicked",
    "def _handle_send_clicked",
    414,
    "Strips draft and invokes on_send when non-empty.",
)
LOC_MAIN_WINDOW = locator(
    f"{SOURCE_REFERENCE}src/ui/main_window.py",
    "main window",
    "class MainWindow",
    26,
    "Builds header, primary/secondary pane, status bar, and debug buttons.",
)
LOC_MAIN_WINDOW_TEXT = locator(
    f"{SOURCE_REFERENCE}src/ui/main_window.py",
    "observable shell header",
    "Observable chat shell",
    68,
    "Shows current framing as an observable shell rather than a polished chat product.",
)
LOC_PANED_SHELL = locator(
    f"{SOURCE_REFERENCE}src/ui/paned_shell.py",
    "paned shell",
    "class PanedShell",
    13,
    "Owns primary and secondary pane visibility/width behavior.",
)
LOC_WORKSPACE_PANEL = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/workspace_panel.py",
    "workspace panel",
    "class WorkspacePanel",
    25,
    "Hosts the tabbed secondary workspace.",
)
LOC_WORKSPACE_REFRESH = locator(
    f"{SOURCE_REFERENCE}src/ui/panels/workspace_panel.py",
    "workspace refresh",
    "def refresh",
    92,
    "Refreshes Agent HUD, Tools, Events, and Inspector from runtime snapshots.",
)
LOC_AGENT_HUD = locator(
    f"{SOURCE_REFERENCE}src/ui/workspace/agent_hud_tab.py",
    "agent HUD",
    "class AgentHudTab",
    16,
    "Shows agent state, pending HITL approvals, and data hooks.",
)
LOC_TOOLS_TAB = locator(
    f"{SOURCE_REFERENCE}src/ui/workspace/tools_tab.py",
    "tools tab",
    "class ToolsTab",
    17,
    "Shows package catalog, execution history, argument input, details, run and cancel controls.",
)
LOC_EVENTS_TAB = locator(
    f"{SOURCE_REFERENCE}src/ui/workspace/events_tab.py",
    "events tab",
    "class EventsTab",
    17,
    "Shows filtered runtime activity events.",
)
LOC_INSPECTOR_TAB = locator(
    f"{SOURCE_REFERENCE}src/ui/workspace/inspector_tab.py",
    "inspector tab",
    "class InspectorTab",
    17,
    "Shows widget-registry tree and selected widget details.",
)
LOC_AGENT_CONTRACT = locator(
    f"{SOURCE_REFERENCE}src/runtime/contracts/agent.py",
    "agent contract",
    "class AgentSnapshot",
    44,
    "Defines host-facing agent snapshot including last messages, pending approvals, model, session, pause/stop state.",
)
LOC_AGENT_CONTROLLER = locator(
    f"{SOURCE_REFERENCE}src/runtime/agent_host/controller.py",
    "agent controller",
    "class HostAgentController",
    85,
    "Owns user-turn submission, stop/pause/resume, HITL resolution, slash commands, tool calls, and agent snapshots.",
)
LOC_PARSE_TURN = locator(
    f"{SOURCE_REFERENCE}src/runtime/agent_host/controller.py",
    "turn parser",
    "def _parse_user_turn",
    700,
    "Parses slash commands such as /tool list and /tool <id>.",
)
LOC_SESSION_CONTRACT = locator(
    f"{SOURCE_REFERENCE}src/runtime/contracts/session.py",
    "session contract",
    "class SessionSnapshot",
    39,
    "Defines active session, available sessions/models/loops, current model/loop, use_echo, and hardware.",
)
LOC_SESSION_CONTROLLER = locator(
    f"{SOURCE_REFERENCE}src/runtime/agent_host/session_controller.py",
    "session controller",
    "class HostSessionController",
    32,
    "Owns model, loop, session CRUD, session snapshots, and hardware probes.",
)
LOC_SESSION_DIALOG = locator(
    f"{SOURCE_REFERENCE}src/ui/dialogs/session_manager_dialog.py",
    "session manager dialog",
    "class SessionManagerDialog",
    27,
    "Provides session CRUD modal mounted from the chat header.",
)
LOC_TOOL_CONTRACT = locator(
    f"{SOURCE_REFERENCE}src/runtime/contracts/tools.py",
    "tool contract",
    "class ToolRuntimeSnapshot",
    49,
    "Defines available tools, recent executions, and active execution ids.",
)
LOC_TOOL_SERVICE = locator(
    f"{SOURCE_REFERENCE}src/runtime/tools/service.py",
    "tool service",
    "class PackageToolService",
    66,
    "Discovers tool packages, runs tools through task manager, tracks execution snapshots.",
)
LOC_MANIFESTS = locator(
    f"{SOURCE_REFERENCE}src/runtime/tools/manifests.py",
    "tool manifests",
    "def discover_tool_packages",
    25,
    "Loads portable tool manifests from tool_packages.",
)
LOC_INVOKE_TOOL = locator(
    f"{SOURCE_REFERENCE}src/runtime/tools/manifests.py",
    "invoke tool",
    "def invoke_tool",
    55,
    "Loads a runner module and calls its configured entrypoint.",
)
LOC_TOOL_PACKAGES = locator(
    f"{SOURCE_REFERENCE}tool_packages/README.md",
    "tool packages README",
    "Portable tool packages",
    3,
    "Describes manifest-plus-runner package layout.",
)
LOC_ACTIVITY_STREAM = locator(
    f"{SOURCE_REFERENCE}src/runtime/activity_stream.py",
    "activity stream",
    "class ActivityStream",
    37,
    "Records normalized runtime events with subscribers and recent-event filters.",
)
LOC_DATA_HOOK_CATALOG = locator(
    f"{SOURCE_REFERENCE}src/runtime/data_hooks.py",
    "data hook catalog",
    "class DataHookCatalog",
    30,
    "Registers previewable data hooks with capacity and safe preview behavior.",
)
LOC_TASK_MANAGER = locator(
    f"{SOURCE_REFERENCE}src/shell/task_manager.py",
    "task manager",
    "class TaskManager",
    66,
    "Runs background work and returns task results to the UI thread through polling.",
)
LOC_EVENT_BUS = locator(
    f"{SOURCE_REFERENCE}src/shell/event_bus.py",
    "event bus",
    "class EventBus",
    31,
    "Publishes typed shell events with wildcard subscribers and recent event history.",
)
LOC_STATE_MANAGER = locator(
    f"{SOURCE_REFERENCE}src/shell/state_manager.py",
    "state manager",
    "class StateManager",
    57,
    "Loads and saves window, UI, and session state.",
)
LOC_RUNTIME_SNAPSHOT = locator(
    f"{SOURCE_REFERENCE}src/shell/runtime_snapshot.py",
    "runtime snapshot",
    "class RuntimeSnapshotBuilder",
    21,
    "Builds runtime snapshots from shell, UI, session, agent, tools, activity, hooks, and widgets.",
)
LOC_CRASH_HANDLER = locator(
    f"{SOURCE_REFERENCE}src/shell/crash_handler.py",
    "crash handler",
    "class CrashHandler",
    29,
    "Captures uncaught exceptions, writes crash reports, and requests shutdown.",
)
LOC_LOGGING_SETUP = locator(
    f"{SOURCE_REFERENCE}src/shell/logging_setup.py",
    "logging setup",
    "def configure_logging",
    19,
    "Configures structured logging with fallback behavior.",
)
LOC_MINDSHARD_ADAPTER = locator(
    f"{SOURCE_REFERENCE}src/runtime/adapters/mindshard_adapter.py",
    "Mindshard adapter",
    "class MindshardAdapter",
    39,
    "Owns the bridge between host contracts and vendored Mindshard runtime.",
)
LOC_ECHO_MODEL = locator(
    f"{SOURCE_REFERENCE}src/runtime/adapters/mindshard_adapter.py",
    "echo model",
    "ECHO_MODEL",
    21,
    "Provides local echo/test model fallback behavior.",
)
LOC_LOAD_IMPORTS = locator(
    f"{SOURCE_REFERENCE}src/runtime/adapters/mindshard_adapter.py",
    "vendored import seam",
    "def _load_imports",
    357,
    "Imports vendored agent loops, shell, and LLM bridges from the adapter only.",
)
LOC_VENDOR_BOOTSTRAP = locator(
    f"{SOURCE_REFERENCE}src/runtime/vendors/mindshard/bootstrap.py",
    "vendored bootstrap",
    "def ensure_bootstrap",
    25,
    "Registers top-level aliases for the vendored runtime copy.",
)


CAPABILITIES = (
    ToolCapability(
        key="chat_layout_rework_required",
        label="Chat Layout Rework Required",
        target_outcome=(
            "Before implementation, replace the perfunctory reference layout with "
            "a real chat UX specification that fits the Useful Helpers explorer-first workbench."
        ),
        expected_inputs=("reference chat panel", "Useful Helpers front-door layout", "user chat UX requirements"),
        expected_outputs=("approved chat layout spec", "message object model", "interaction states", "integration placement decision"),
        reference_locators=(LOC_README_CHAT_FIRST, LOC_CHAT_PANEL, LOC_CHAT_BUILD, LOC_TRANSCRIPT, LOC_INPUT, LOC_APPEND_MESSAGE, LOC_MAIN_WINDOW_TEXT),
        done_when=LAYOUT_REWORK_RULE,
        implementation_owner="future Useful Helpers UI design tranche",
    ),
    ToolCapability(
        key="bootstrap_host_kernel",
        label="Bootstrap Host Kernel",
        target_outcome="Use a thin entrypoint to build shell context, services, root window, mounted panels, polling, and shutdown.",
        expected_inputs=("project root", "app config", "UI defaults"),
        expected_outputs=("host kernel", "root window", "service graph", "shutdown hooks"),
        reference_locators=(LOC_BOOTSTRAP, LOC_MAIN, LOC_KERNEL, LOC_KERNEL_START, LOC_BUILD_SERVICES, LOC_RUNTIME_SERVICES),
        done_when="Useful Helpers can reuse kernel patterns without replacing src/app.py or importing the reference app.",
        implementation_owner="Useful Helpers shell/orchestration layer",
    ),
    ToolCapability(
        key="compose_chat_and_workspace_shell",
        label="Compose Chat And Workspace Shell",
        target_outcome="Mount an optional primary chat surface and secondary workspace while preserving the existing explorer-first workbench.",
        expected_inputs=("main window host", "chat panel", "workspace panel", "layout state"),
        expected_outputs=("mounted optional chat/workspace shell", "panel visibility state", "status surface"),
        reference_locators=(LOC_MAIN_WINDOW, LOC_PANED_SHELL, LOC_MOUNT_PANELS, LOC_WORKSPACE_PANEL, LOC_WORKSPACE_REFRESH, LOC_UI_DEFAULTS),
        done_when="Chat/workspace composition is opt-in or tool-scoped and never displaces the folder explorer front door.",
        implementation_owner="Useful Helpers UI shell",
    ),
    ToolCapability(
        key="render_conversational_messages",
        label="Render Conversational Messages",
        target_outcome=(
            "Render user, assistant, system, tool, error, status, and HITL messages "
            "as structured conversation objects rather than plain transcript appends."
        ),
        expected_inputs=("message records", "role", "content", "metadata", "stream/progress state"),
        expected_outputs=("message list view", "transcript state", "scroll/focus behavior"),
        reference_locators=(LOC_APPEND_MESSAGE, LOC_SYNC_AGENT_OUTPUT, LOC_SEND_MESSAGE),
        done_when="The chat surface feels conversational, inspectable, and recoverable after session restore.",
        implementation_owner="future Useful Helpers chat UI module",
    ),
    ToolCapability(
        key="capture_chat_input_and_controls",
        label="Capture Chat Input And Controls",
        target_outcome="Provide draft input, send shortcut/button, stop, pause/resume, model picker, loop picker, and session manager controls.",
        expected_inputs=("draft text", "selected model", "selected loop", "active turn state", "session snapshot"),
        expected_outputs=("submitted turn", "cleared or preserved draft", "control enabled states", "activity event"),
        reference_locators=(LOC_DRAFT_STATE, LOC_HANDLE_SEND, LOC_SUBMIT_TURN, LOC_AGENT_CONTRACT, LOC_AGENT_CONTROLLER),
        done_when="Controls are ergonomic, state-driven, and cannot send empty turns or unsafe hidden commands.",
        implementation_owner="future Useful Helpers chat controller",
    ),
    ToolCapability(
        key="manage_sessions_models_and_loops",
        label="Manage Sessions Models And Loops",
        target_outcome="Expose current session, available sessions, model/loop choices, hardware summary, and session CRUD through local contracts.",
        expected_inputs=("session snapshot", "model choice", "loop choice", "session action"),
        expected_outputs=("updated session snapshot", "session dialog state", "activity/status events"),
        reference_locators=(LOC_SESSION_CONTRACT, LOC_SESSION_CONTROLLER, LOC_SESSION_DIALOG, LOC_ECHO_MODEL),
        done_when="Session/model/loop state is visible, testable, and stored locally without importing vendored code outside an adapter.",
        implementation_owner="future Useful Helpers session/chat state layer",
    ),
    ToolCapability(
        key="host_agent_turns_and_hitl",
        label="Host Agent Turns And HITL",
        target_outcome="Submit turns, parse slash commands, run/pause/stop/resume agent work, and resolve human approval gates.",
        expected_inputs=("user message", "slash command", "agent controller state", "HITL decision"),
        expected_outputs=("agent snapshot", "pending approvals", "last agent message", "activity events"),
        reference_locators=(LOC_AGENT_CONTRACT, LOC_AGENT_CONTROLLER, LOC_PARSE_TURN, LOC_AGENT_HUD),
        done_when="Agent turns and HITL gates are observable and reversible enough for user control.",
        implementation_owner="future Useful Helpers agent host adapter",
    ),
    ToolCapability(
        key="discover_and_run_tool_packages",
        label="Discover And Run Tool Packages",
        target_outcome="Discover portable manifest-plus-runner tool packages, execute them with arguments, and track execution history.",
        expected_inputs=("tool package directory", "manifest files", "tool id", "arguments", "cancel request"),
        expected_outputs=("tool descriptors", "execution snapshots", "result/error state", "activity events"),
        reference_locators=(LOC_TOOL_CONTRACT, LOC_TOOL_SERVICE, LOC_MANIFESTS, LOC_INVOKE_TOOL, LOC_TOOL_PACKAGES, LOC_TOOLS_TAB, LOC_RUN_TOOL),
        done_when="Useful Helpers tool execution uses local reviewed adapters and does not execute arbitrary reference package code silently.",
        implementation_owner="future Useful Helpers tool runtime",
    ),
    ToolCapability(
        key="show_activity_events_hooks_and_inspector",
        label="Show Activity Events Hooks And Inspector",
        target_outcome="Surface runtime events, previewable data hooks, and widget registry inspection for debugging and observability.",
        expected_inputs=("activity events", "data hooks", "widget records", "widget tree"),
        expected_outputs=("Events tab", "Agent HUD hooks", "Inspector tree/details", "filtered views"),
        reference_locators=(LOC_ACTIVITY_STREAM, LOC_DATA_HOOK_CATALOG, LOC_DATA_HOOKS, LOC_EVENTS_TAB, LOC_INSPECTOR_TAB),
        done_when="Observability helps development without cluttering the primary user workflow.",
        implementation_owner="future Useful Helpers observability layer",
    ),
    ToolCapability(
        key="queue_background_tasks",
        label="Queue Background Tasks",
        target_outcome="Run long operations off the UI thread and hand results back through a predictable polling/drain path.",
        expected_inputs=("task function", "arguments", "success/error handlers", "shutdown request"),
        expected_outputs=("task id", "task records", "completed task results", "status updates"),
        reference_locators=(LOC_TASK_MANAGER, LOC_EVENT_BUS, LOC_POLL),
        done_when="Background work cannot mutate Tk widgets directly and reports completion/failure safely.",
        implementation_owner="Useful Helpers task/runtime layer",
    ),
    ToolCapability(
        key="persist_state_and_runtime_snapshots",
        label="Persist State And Runtime Snapshots",
        target_outcome="Persist window/UI/session state and write runtime snapshots for debugging without carrying old reference state files.",
        expected_inputs=("window state", "UI state", "session state", "runtime providers", "snapshot label"),
        expected_outputs=("state files", "runtime snapshot JSON", "restored draft/layout/session hints"),
        reference_locators=(LOC_STATE_MANAGER, LOC_RUNTIME_SNAPSHOT, LOC_SAVE_SNAPSHOT, LOC_PERSIST, LOC_SHUTDOWN),
        done_when="State persistence is scoped to Useful Helpers side-car paths and excludes checked-in reference databases/logs/snapshots.",
        implementation_owner="Useful Helpers state/runtime snapshot layer",
    ),
    ToolCapability(
        key="structured_logging_and_crash_reports",
        label="Structured Logging And Crash Reports",
        target_outcome="Configure logs and crash reports with safe defaults and without shipping reference debug crash controls.",
        expected_inputs=("logging config", "exception", "snapshot writer", "shutdown callback"),
        expected_outputs=("log records", "crash report", "status/event updates"),
        reference_locators=(LOC_LOGGING_SETUP, LOC_CRASH_HANDLER, LOC_DEBUG_CONFIG),
        done_when="Crash/log behavior is useful in development and intentionally gated for user-facing builds.",
        implementation_owner="Useful Helpers diagnostics layer",
    ),
    ToolCapability(
        key="optional_mindshard_adapter_seam",
        label="Optional Mindshard Adapter Seam",
        target_outcome="Keep vendored agent runtime imports behind one optional adapter seam with echo fallback and explicit dependency gates.",
        expected_inputs=("agent database path", "model", "loop", "session id", "use echo setting"),
        expected_outputs=("adapter instance", "model list", "loop list", "agent/session operations", "closed resources"),
        reference_locators=(LOC_REQUIRE_NUMPY, LOC_MINDSHARD_ADAPTER, LOC_LOAD_IMPORTS, LOC_VENDOR_BOOTSTRAP),
        done_when="Useful Helpers does not import vendored Mindshard or require numpy unless a later tranche explicitly accepts that integration.",
        implementation_owner="deferred optional agent runtime tranche",
    ),
)


CHAT_WINDOW_KERNAL_CONTRACT = ToolContract(
    key=TOOL_KEY,
    label=TOOL_LABEL,
    status=STATUS,
    source_reference=SOURCE_REFERENCE,
    reference_app_path=REFERENCE_APP_PATH,
    reference_retirement_rule=REFERENCE_RETIREMENT_RULE,
    done_state=DONE_STATE,
    capabilities=CAPABILITIES,
)


def get_tool_contract() -> ToolContract:
    """Return the semantic integration contract for the ChatWindowKERNAL tool."""

    return CHAT_WINDOW_KERNAL_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all ChatWindowKERNAL capabilities currently planned for re-homing."""

    return CHAT_WINDOW_KERNAL_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(CHAT_WINDOW_KERNAL_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return CHAT_WINDOW_KERNAL_CONTRACT.reference_retirement_rule
