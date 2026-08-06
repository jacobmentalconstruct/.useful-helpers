"""MonacoVIEWER tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the target
shape for the shared human/agent editing surface of the workbench: a Monaco
editor session that a person and an agent operate together, where either party's
actions are visible to the other through one command path and one event record.

The parts-bin reference supplies a working Python-to-Monaco bridge and a correct
range-edit primitive. It does not supply the shared-session behavior; its "agent"
path is a modal textarea a human pastes JSON into.

Host model rule:
The reference is Qt/pywebview, not Tk, despite an unused `import tkinter` marked
"contract compliance". Qt and Tk cannot share a process event loop, so the
accepted shape is a separate Monaco session process exposing a session service
that the Tk workbench and an agent both call as equal clients.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
MonacoVIEWER tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "monaco_viewer"
TOOL_LABEL = "MonacoVIEWER"
STATUS = (
    "contract reviewed; implementation pending; reference is Qt-hosted and must "
    "be re-homed as a separate-process session service"
)

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_MonacoVIEWER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_UI_PATH = f"{SOURCE_REFERENCE}assets/index.js"
REFERENCE_SHELL_PATH = f"{SOURCE_REFERENCE}assets/index.html"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each MonacoVIEWER "
    "capability is re-homed into Useful Helpers runtime modules, remove parts-bin "
    "references from runtime tool code and keep historical provenance in docs only."
)

HOST_MODEL_RULE = (
    "The accepted host model is a separate Monaco session process exposing an "
    "editor session service over local IPC. The Tk workbench and any agent are "
    "equal clients of that service. The reference forces a Qt pywebview backend "
    "and blocks the main thread, so it cannot be embedded in the Tk workbench "
    "process; its unused tkinter import does not make it a Tk integration."
)

SHARED_SESSION_RULE = (
    "A GUI-initiated action and an agent-initiated action must travel the same "
    "command path and produce the same event record. Neither client is "
    "privileged, and every client observes every mutation regardless of which "
    "client caused it."
)

SAVE_GATE_RULE = (
    "No save completes unless the target path is explicit and inside an approved "
    "root, on-disk content is checked for modification since the buffer was "
    "loaded, a conflicting on-disk change is surfaced rather than overwritten, "
    "the write is atomic or equivalently non-truncating, the acting client is "
    "recorded, and the resulting change is announced on the event stream."
)

ASSET_VENDORING_RULE = (
    "Monaco must be vendored locally under the tool's assets directory with a "
    "pinned version and recorded provenance. The reference loads the editor from "
    "a public CDN and permits remote script, unsafe-eval, and unsafe-inline in "
    "its Content-Security-Policy."
)

DONE_STATE = (
    "MonacoVIEWER integration is complete when Useful Helpers can launch and "
    "supervise a Monaco session process without blocking the Tk event loop; can "
    "expose one documented session API that the Tk UI and an agent call "
    "identically; can report open tabs, active tab, cursor, selection, dirty "
    "state, and buffer text to any client; can emit an event stream so every "
    "client observes every mutation regardless of origin; can apply "
    "range-precise undoable edits into a live buffer; can open, close, and focus "
    "tabs on request; can save to disk only behind an explicit gate that never "
    "silently overwrites newer on-disk content or discards unsaved buffer state; "
    "can load Monaco from vendored local assets with no runtime network "
    "dependency; can survive session-process death without corrupting workbench "
    "state; and can do all of that with no runtime dependency on the parts bin."
)

AGENT_SURFACE_SCOPE = (
    "observe_session_state",
    "apply_ranged_edits",
    "manage_tabs",
    "save_buffer_behind_gate",
)

REFERENCE_FRAILTIES = (
    "src/app.py:9 imports tkinter as 'contract compliance' and never uses it; the app is Qt/pywebview, not a Tk integration.",
    "src/app.py:13 hard-forces the Qt pywebview backend at import time, and webview.start() blocks and owns the main thread.",
    "src/app.py:255 runs webview.start() inside contextlib.redirect_stderr(os.devnull), discarding all launch diagnostics.",
    "The 'Agent Surgical Replace' feature is a modal textarea a human pastes JSON into; there is no socket, RPC, or endpoint an agent can drive.",
    "There is no channel into a running instance; CLI edit arguments launch a new window per invocation instead of propagating into an open session.",
    "There is no event stream; set_active_tab reports state to the Python host only to update the window title.",
    "Headless regex mode runs re.subn and rewrites the file in place with no dry run, preview, diff, backup, or confirmation, and can silently clobber a buffer open in the GUI.",
    "_save_logic writes with a plain truncating open(path, 'w'); there is no atomic write and no backup, so a mid-write failure can destroy the original.",
    "Save performs no staleness check against on-disk content before overwriting.",
    "Monaco is loaded from a public CDN at runtime, so the editor silently fails with no network.",
    "The Content-Security-Policy permits unsafe-eval, unsafe-inline, and remote script from jsdelivr and unpkg.",
    "apply_log_filter replaces sys.stdout and sys.stderr process-wide and rewrites 'ERROR' to 'WARNING (safe to ignore)' and 'failed' to 'note: failed', suppressing genuine diagnostics.",
    "NamedTemporaryFile(delete=False) leaks a temp file on every untitled launch, and _update_title string-matches 'Untitled-*.txt' to hide the leak.",
    "Language inference is duplicated: a hardcoded extension map in the CLI and a separate Monaco language-registry query in the UI.",
)


def locator(label: str, symbol: str, line: int, purpose: str, path: str = REFERENCE_APP_PATH) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, path)


LOC_TK_IMPORT = locator("misleading tk import", "import tkinter as tk", 9, "Unused tkinter import labelled 'contract compliance'; proves the reference is not a Tk integration.")
LOC_QT_FORCE = locator("forced Qt backend", "PYWEBVIEW_GUI", 13, "Forces the Qt pywebview backend at import time.")
LOC_LOG_FILTER = locator("global log filter", "def apply_log_filter", 33, "Replaces stdout/stderr process-wide and rewrites error text; must not be adopted.")
LOC_API_CLASS = locator("JS-to-Python bridge", "class Api", 98, "Bridge object exposed to JavaScript as js_api; the reusable half of the reference.")
LOC_SET_ACTIVE_TAB = locator("active tab report", "def set_active_tab", 118, "Only state push from UI to host; title-only, not a general event stream.")
LOC_OPEN_DIALOG = locator("file open", "def open_dialog", 123, "Host-side file open returning path and text to the UI.")
LOC_SAVE_LOGIC = locator("save write", "def _save_logic", 143, "Truncating non-atomic write with no staleness check or backup.")
LOC_RUN_GUI = locator("window creation", "def run_gui", 184, "Builds boot payload, native menus, and the pywebview window.")
LOC_BOOT = locator("boot payload", "boot = {", 197, "Base64 JSON payload injected into the page as initial session state.")
LOC_MENU_SURGICAL = locator("surgical menu action", "Agent Surgical Replace", 233, "Native menu entry that opens the paste-JSON modal.")
LOC_CREATE_WINDOW = locator("js_api binding", "js_api=api", 239, "Binds the Python Api object into the page as window.pywebview.api.")
LOC_START_SILENCED = locator("silenced start", "redirect_stderr", 254, "Discards launch diagnostics during webview.start().")
LOC_CLI = locator("cli entry", "def run_cli", 259, "Argument surface for GUI launch and headless mode.")
LOC_HEADLESS = locator("headless regex", "args.regex_find and args.regex_replace", 283, "Headless branch that edits files without opening a window.")
LOC_SUBN = locator("in-place regex write", "re.subn", 294, "Unguarded in-place rewrite with no dry run, preview, backup, or confirmation.")
LOC_TEMPFILE = locator("leaked temp file", "NamedTemporaryFile", 310, "Creates an untitled temp file with delete=False that is never cleaned up.")
LOC_LANG_MAP = locator("cli language map", "'.py':'python'", 318, "Hardcoded extension-to-language map duplicated against the UI language registry.")

LOC_BOOT_DECODE = locator("boot decode", "JSON.parse(atob('%BOOT%'))", 1, "Decodes the injected boot payload in the page.", REFERENCE_UI_PATH)
LOC_SCHEMA = locator("surgical schema", "const SURGICAL_SCHEMA", 13, "Declares the range-edit JSON schema shown to the operator.", REFERENCE_UI_PATH)
LOC_SHOW_SURGICAL = locator("surgical modal", "function showSurgicalReplace", 100, "Prefills the schema from the current selection and opens the paste modal.", REFERENCE_UI_PATH)
LOC_APPLY_SURGICAL = locator("surgical apply", "function applySurgicalReplace", 126, "Validates and clamps the range, then applies the edit; the reusable edit primitive.", REFERENCE_UI_PATH)
LOC_PUSH_EDIT = locator("undoable edit", "pushEditOperations", 165, "Applies a ranged replacement as an undoable Monaco operation.", REFERENCE_UI_PATH)
LOC_MONACO_CDN = locator("monaco cdn", "cdn.jsdelivr.net/npm/monaco-editor", 203, "Loads the Monaco AMD bundle from a public CDN at runtime.", REFERENCE_UI_PATH)
LOC_JS_BRIDGE = locator("python-to-js bridge", "window.__doNew", 256, "Exposes UI commands to the Python host for evaluate_js invocation.", REFERENCE_UI_PATH)
LOC_API_CALLBACK = locator("ui-to-host callback", "window.pywebview.api.set_active_tab", 326, "Reports active tab and dirty state back to the Python host.", REFERENCE_UI_PATH)
LOC_ADD_TAB = locator("tab model", "function addTab", 350, "Creates a Monaco model per tab and tracks dirty state.", REFERENCE_UI_PATH)
LOC_CLOSE_TAB = locator("tab close", "async function closeTab", 373, "Confirms before discarding a dirty tab.", REFERENCE_UI_PATH)
LOC_CSP = locator("content security policy", "Content-Security-Policy", 5, "Permits unsafe-eval, unsafe-inline, and remote script from jsdelivr and unpkg.", REFERENCE_SHELL_PATH)


CAPABILITIES = (
    ToolCapability(
        key="session_process_lifecycle",
        label="Session Process Lifecycle",
        target_outcome="Launch, supervise, health-check, and shut down a Monaco session process without blocking or destabilizing the Tk workbench event loop.",
        expected_inputs=("session config", "workspace root", "launch confirmation"),
        expected_outputs=("session handle", "process state", "startup diagnostics", "exit reason"),
        reference_locators=(LOC_QT_FORCE, LOC_RUN_GUI, LOC_CREATE_WINDOW, LOC_START_SILENCED, LOC_TK_IMPORT),
        done_when="The Tk workbench can start and stop a Monaco session, sees real startup diagnostics, and survives session-process death without corrupting workbench state.",
        implementation_owner="useful_helpers.tools.monaco_viewer session process module",
    ),
    ToolCapability(
        key="session_state_inspection",
        label="Session State Inspection",
        target_outcome="Report open tabs, active tab, cursor, selection, dirty flags, and live buffer text to any client on demand.",
        expected_inputs=("session handle", "optional tab selector"),
        expected_outputs=("tab list", "active tab record", "cursor/selection", "dirty state", "buffer text"),
        reference_locators=(LOC_SET_ACTIVE_TAB, LOC_API_CALLBACK, LOC_ADD_TAB, LOC_BOOT, LOC_BOOT_DECODE),
        done_when="An agent can read the same session state the human is looking at, with no GUI interaction required.",
        implementation_owner="useful_helpers.tools.monaco_viewer session state module",
    ),
    ToolCapability(
        key="session_event_stream",
        label="Session Event Stream",
        target_outcome="Emit an ordered event record for every session mutation so all clients observe changes regardless of which client caused them.",
        expected_inputs=("session handle", "client subscription", "event filter"),
        expected_outputs=("ordered events", "originating client", "resulting state delta"),
        reference_locators=(LOC_API_CALLBACK, LOC_SET_ACTIVE_TAB),
        done_when=SHARED_SESSION_RULE,
        implementation_owner="useful_helpers.tools.monaco_viewer event stream module",
    ),
    ToolCapability(
        key="ranged_edit_application",
        label="Ranged Edit Application",
        target_outcome="Apply a start/end line and column replacement into a live buffer as a single undoable operation, with range clamping and validation.",
        expected_inputs=("session handle", "tab selector", "start/end line", "start/end column", "replacement text"),
        expected_outputs=("applied range", "undo entry", "validation findings", "resulting buffer state"),
        reference_locators=(LOC_SCHEMA, LOC_SHOW_SURGICAL, LOC_APPLY_SURGICAL, LOC_PUSH_EDIT),
        done_when="An agent call produces a visible, undoable edit in the human's live window, and the human sees it without reloading.",
        implementation_owner="useful_helpers.tools.monaco_viewer edit module",
    ),
    ToolCapability(
        key="tab_management",
        label="Tab Management",
        target_outcome="Open, close, and focus tabs on request from either client, preserving dirty-state confirmation semantics.",
        expected_inputs=("session handle", "file path", "tab selector", "close policy"),
        expected_outputs=("tab record", "focus change event", "dirty-discard prompt", "close result"),
        reference_locators=(LOC_ADD_TAB, LOC_CLOSE_TAB, LOC_OPEN_DIALOG),
        done_when="Either party can bring a file into the shared session or change what both are looking at, and a dirty tab is never closed silently.",
        implementation_owner="useful_helpers.tools.monaco_viewer tab module",
    ),
    ToolCapability(
        key="gated_buffer_save",
        label="Gated Buffer Save",
        target_outcome="Commit a buffer to disk only behind staleness detection, conflict surfacing, atomic write, client attribution, and event announcement.",
        expected_inputs=("session handle", "tab selector", "target path", "approved root", "conflict decision", "confirmation"),
        expected_outputs=("save plan", "conflict report", "write result", "attributed event"),
        reference_locators=(LOC_SAVE_LOGIC, LOC_SUBN, LOC_HEADLESS),
        done_when=SAVE_GATE_RULE,
        implementation_owner="useful_helpers.tools.monaco_viewer save module",
    ),
    ToolCapability(
        key="vendored_monaco_assets",
        label="Vendored Monaco Assets",
        target_outcome="Serve Monaco from pinned local assets with recorded provenance and a Content-Security-Policy that does not permit remote script.",
        expected_inputs=("vendored monaco version", "asset root", "license record"),
        expected_outputs=("local asset manifest", "provenance entry", "tightened CSP"),
        reference_locators=(LOC_MONACO_CDN, LOC_CSP),
        done_when=ASSET_VENDORING_RULE,
        implementation_owner="useful_helpers.tools.monaco_viewer asset module",
    ),
    ToolCapability(
        key="headless_text_operations",
        label="Headless Text Operations",
        target_outcome="Provide dry-run-first headless text operations that respect open buffers instead of rewriting files behind the session's back.",
        expected_inputs=("selected paths", "operation", "pattern/replacement", "dry-run flag", "open-buffer state"),
        expected_outputs=("preview diff", "conflict warnings for open dirty buffers", "write result"),
        reference_locators=(LOC_CLI, LOC_HEADLESS, LOC_SUBN, LOC_LANG_MAP),
        done_when="No headless operation writes a file that a live session holds dirty, and every write is previewable first, consistent with Tokenizing Patcher doctrine.",
        implementation_owner="useful_helpers.tools.monaco_viewer headless module",
    ),
    ToolCapability(
        key="shared_session_provenance",
        label="Shared Session Provenance",
        target_outcome="Record which client performed each action so session history is attributable and reviewable after the fact.",
        expected_inputs=("client identity", "command record", "event record"),
        expected_outputs=("attributed history", "replayable action log", "review surface"),
        reference_locators=(LOC_MENU_SURGICAL, LOC_JS_BRIDGE, LOC_LOG_FILTER),
        done_when="A human can review what the agent changed and when, and the reference's diagnostic-suppressing log filter is not carried forward.",
        implementation_owner="useful_helpers.tools.monaco_viewer provenance module",
    ),
)


MONACO_VIEWER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the MonacoVIEWER tool."""

    return MONACO_VIEWER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all MonacoVIEWER capabilities currently planned for re-homing."""

    return MONACO_VIEWER_CONTRACT.capabilities


def agent_surface_scope() -> tuple[str, ...]:
    """Return the accepted agent-facing capability scope for the first implementation."""

    return AGENT_SURFACE_SCOPE


def host_model_notice() -> str:
    """Return the accepted host model rule and why the reference cannot be embedded in Tk."""

    return HOST_MODEL_RULE


def shared_session_notice() -> str:
    """Return the symmetry rule governing human and agent access to one session."""

    return SHARED_SESSION_RULE


def save_gate_notice() -> str:
    """Return the rule that governs any write to disk from a session buffer."""

    return SAVE_GATE_RULE


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(MONACO_VIEWER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return MONACO_VIEWER_CONTRACT.reference_retirement_rule
