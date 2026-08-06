"""TheDISMANTLER tool contract and reference implementation map.

This module is intentionally semantic, not operational. It records the third and
last parts-bin input to the Tool Command Surface Framework: a single GUI-side
dispatch chokepoint, demonstrated in Tkinter, that a human UI and an automated
non-human caller already share.

Dispatch doctrine:
The reference states in its own source that all UI-backend communication goes
through `BackendEngine.execute_task()`, and its `WorkflowEngine` drives the same
entry point with zero UI dependencies. This is the third independent statement of
the single-chokepoint principle across three references, which settles it as a
Root Tranche 15 requirement rather than a per-tool preference.

Unsafe pattern warning:
The reference's tool auto-discovery executes arbitrary `.py` files found in a
drop-in directory during boot. That pattern must not be adopted, and is
materially more dangerous in a workbench an agent can write files into.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
TheDISMANTLER tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "the_dismantler"
TOOL_LABEL = "TheDISMANTLER"
STATUS = (
    "contract reviewed; implementation pending; GUI dispatch prior art; "
    "auto-discovery is unsafe to adopt as-is"
)

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_TheDISMANTLER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/backend/main.py"
REFERENCE_BOOTSTRAP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_BASE_TOOL_PATH = f"{SOURCE_REFERENCE}src/backend/tools/base_tool.py"
REFERENCE_WORKFLOW_PATH = f"{SOURCE_REFERENCE}src/backend/modules/workflow_engine.py"
REFERENCE_REFINEMENT_PATH = f"{SOURCE_REFERENCE}src/backend/modules/refinement_engine.py"
REFERENCE_UI_PATH = f"{SOURCE_REFERENCE}src/ui/main_window.py"
REFERENCE_TOOLS_README_PATH = f"{SOURCE_REFERENCE}TOOLS_README.md"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each TheDISMANTLER "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

SINGLE_CHOKEPOINT_RULE = (
    "Every tool operation is dispatched through one owned chokepoint. The GUI, "
    "the agent, and automated workflows all call it, and the backend cannot "
    "tell them apart. No caller may reach a tool implementation by any other "
    "path."
)

SAFE_LOADING_RULE = (
    "Tools must be loaded from a declared, reviewed registry. Discovery must not "
    "mean executing arbitrary .py files found in a directory at boot. Any "
    "drop-in path must require an explicit manifest entry, and the loader must "
    "never grant a newly-dropped file the ability to run code merely by "
    "existing."
)

STABLE_ROUTING_RULE = (
    "Routing identity is a stable declared identifier, never a mutable display "
    "name. Tool namespaces stay separate from core subsystem namespaces, and "
    "collision protection is derived from what is actually registered rather "
    "than from a hardcoded list of known names."
)

CONVERGENT_DOCTRINE_NOTE = (
    "Three parts-bin references state the single-chokepoint principle "
    "independently: MonacoVIEWER requires session symmetry with one shared event "
    "record, manifold-mcp requires that MCP and CLI never fork behavior, and "
    "TheDISMANTLER requires that all UI-backend communication go through "
    "execute_task(). Convergence across three unrelated designs settles it as a "
    "Root Tranche 15 requirement."
)

FRAMEWORK_INPUT_NOTE = (
    "Root Tranche 15 has four complementary inputs. The repository's own tools/ "
    "supplies the only safety and authority layer. manifold-mcp supplies the "
    "agent transport and machine-readable input schema. TheDISMANTLER supplies "
    "the GUI dispatch chokepoint and in-process tool interface in Tk, plus a "
    "workflow orchestrator proving a non-human caller can share it. "
    "MonacoVIEWER supplies the requirement that the event record be observable "
    "by every client. None of the three parts-bin references has a safety layer."
)

DONE_STATE = (
    "TheDISMANTLER integration is complete when Useful Helpers can dispatch "
    "every tool operation through one owned chokepoint used by the GUI, the "
    "agent, and automated workflows alike; can declare each tool's input schema "
    "in machine-readable form; can route by a stable declared identifier rather "
    "than a mutable display name; can keep tool namespaces separate from core "
    "subsystem namespaces; can load tools without executing arbitrary code found "
    "in a drop-in directory; can enforce authority and containment on every "
    "dispatched operation; can run long operations without blocking the Tk event "
    "loop; can record every dispatch with its originating client; and can do all "
    "of that with no runtime dependency on the parts bin."
)

REFERENCE_FRAILTIES = (
    "BackendEngine._discover_and_load_tools lists src/backend/tools/, dynamically imports every .py file not starting with _, and calls spec.loader.exec_module on it during boot(); TOOLS_README advertises drop-in loading as a feature, which is arbitrary code execution in a workbench an agent can write files into.",
    "There is no signature, manifest, allowlist, or review gate on discovered tools.",
    "tool.initialize() runs during discovery, so a dropped file executes code before any user action.",
    "The routing key is derived from tool.name.lower().replace(' ', '_'), so a display-name change silently breaks routing and similarly-named tools collide.",
    "Tools are registered into the same controllers dict as core controllers, and _RESERVED_KEYS is a hardcoded literal guarding only the five known core names rather than being derived from what is registered.",
    "BaseTool.handle(schema) takes an untyped dict with no declared input schema, so no caller can discover a tool's parameters without reading its source.",
    "validate_schema is opt-in and requires the tool to supply its own required_keys.",
    "WorkflowEngine._STEP_REGISTRY is a class attribute and register_step mutates it at runtime, making workflow vocabulary global mutable state.",
    "There is no authority model and no confirmation gate; every registered controller and tool is equally callable through execute_task.",
    "There is no path containment, and project_root is derived from os.path.dirname applied three times to __file__, the same fragile path-depth pattern found in manifold-mcp.",
    "execute_task catches every exception and returns str(e), discarding the traceback; failures are diagnosable only through the log callback.",
    "UI call sites invoke execute_task directly on the Tk thread, so long operations block the event loop; WorkflowEngine.run documents that it needs a background thread but nothing enforces it.",
    "The envelope is {'status': 'ok'|'error', 'message': ...}, matching manifold-mcp and conflicting with the repository's own {'ok': bool} convention.",
)


def locator(label: str, symbol: str, line: int, purpose: str, path: str = REFERENCE_APP_PATH) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, path)


LOC_DOCTRINE = locator("dispatch doctrine", "All UI-backend communication goes through BackendEngine.execute_task()", 228, "States the single-chokepoint rule in the app's own source.", REFERENCE_REFINEMENT_PATH)
LOC_EXECUTE_TASK = locator("dispatch chokepoint", "def execute_task", 70, "The single entry point taking a schema with system and action keys.")
LOC_SYSTEM_ROUTE = locator("route resolution", "target = schema.get(\"system\")", 76, "Resolves the target controller or tool from the schema.")
LOC_RESERVED = locator("reserved names", "_RESERVED_KEYS", 20, "Hardcoded literal guarding only the five known core controller names.")
LOC_PROJECT_ROOT = locator("fragile root", "os.path.dirname(", 34, "Derives project root from a triple dirname of __file__, a path-depth assumption.")
LOC_DISCOVERY = locator("tool auto-discovery", "def _discover_and_load_tools", 104, "Scans a directory and loads any BaseTool subclass it finds.")
LOC_LISTDIR = locator("drop-in scan", "for filename in os.listdir(tools_dir)", 118, "Iterates every .py file in the tools directory with no allowlist.")
LOC_EXEC_MODULE = locator("arbitrary execution", "spec.loader.exec_module(module)", 135, "Executes discovered module code during boot; the unsafe pattern.")
LOC_TOOL_KEY = locator("display-name routing", "tool.name.lower().replace(\" \", \"_\")", 153, "Derives the routing key from a mutable display name.")
LOC_REGISTER = locator("shared namespace", "self.controllers[tool_key] = tool", 160, "Registers tools into the same dict as core controllers.")
LOC_LIST_TOOLS = locator("tool listing", "def list_tools", 166, "Returns registered tool metadata, the closest thing to a tool list.")

LOC_BASE_TOOL = locator("tool interface", "class BaseTool", 9, "Abstract in-process tool interface with metadata and lifecycle.", REFERENCE_BASE_TOOL_PATH)
LOC_HANDLE = locator("untyped entry", "def handle", 67, "Single tool entry point taking an untyped schema dict.", REFERENCE_BASE_TOOL_PATH)
LOC_VALIDATE = locator("opt-in validation", "def validate_schema", 87, "Optional key-presence check the tool must invoke itself.", REFERENCE_BASE_TOOL_PATH)
LOC_SUCCESS = locator("status envelope", "def success", 125, "Builds the status/message envelope conflicting with the tools/ ok envelope.", REFERENCE_BASE_TOOL_PATH)
LOC_METADATA = locator("tool metadata", "def get_metadata", 138, "Returns name, version, description, tags, requires, and initialized state.", REFERENCE_BASE_TOOL_PATH)

LOC_WORKFLOW_BIND = locator("non-human caller", "execute_fn=backend.execute_task", 17, "Workflow orchestrator drives the same chokepoint the UI uses, with zero UI dependencies.", REFERENCE_WORKFLOW_PATH)
LOC_STEP_REGISTRY = locator("workflow vocabulary", "_STEP_REGISTRY", 26, "Class-level mapping of step names to system/action pairs.", REFERENCE_WORKFLOW_PATH)
LOC_REGISTER_STEP = locator("runtime mutation", "def register_step", 50, "Mutates class-level workflow vocabulary at runtime.", REFERENCE_WORKFLOW_PATH)

LOC_TK_BOOTSTRAP = locator("tk bootstrapper", "class AppBootstrapper(tk.Tk)", 20, "Genuine Tk application shell, unlike the Qt-hosted MonacoVIEWER reference.", REFERENCE_BOOTSTRAP_PATH)
LOC_THREAD_LAUNCH = locator("threaded boot", "threading.Thread(target=self._launch_sequence, daemon=True)", 48, "Boots the backend off the Tk thread to keep the console responsive.", REFERENCE_BOOTSTRAP_PATH)
LOC_UI_CALL = locator("ui call site", "result = self.backend.execute_task({", 452, "Representative UI dispatch made directly on the Tk thread.", REFERENCE_UI_PATH)
LOC_DROPIN_README = locator("drop-in advertised", "Auto-discovered", 6, "Documents drop-in loading as an intended feature.", REFERENCE_TOOLS_README_PATH)


CAPABILITIES = (
    ToolCapability(
        key="single_dispatch_chokepoint",
        label="Single Dispatch Chokepoint",
        target_outcome="Route every tool operation through one owned entry point shared by the GUI, the agent, and automated workflows.",
        expected_inputs=("target identifier", "action", "arguments", "calling client"),
        expected_outputs=("uniform result envelope", "dispatch record", "routing failure reason"),
        reference_locators=(LOC_DOCTRINE, LOC_EXECUTE_TASK, LOC_SYSTEM_ROUTE, LOC_WORKFLOW_BIND, LOC_UI_CALL),
        done_when=SINGLE_CHOKEPOINT_RULE,
        implementation_owner="Root Tranche 15 Tool Command Surface Framework",
    ),
    ToolCapability(
        key="declared_tool_interface",
        label="Declared Tool Interface",
        target_outcome="Give every tool a declared, machine-readable input schema and metadata so callers can discover parameters without reading source.",
        expected_inputs=("tool identifier", "declared schema", "declared metadata"),
        expected_outputs=("discoverable tool description", "validated arguments", "schema violation report"),
        reference_locators=(LOC_BASE_TOOL, LOC_HANDLE, LOC_VALIDATE, LOC_METADATA, LOC_LIST_TOOLS),
        done_when="An agent can enumerate available tools and their parameters from declared metadata alone, with validation enforced by the framework rather than by each tool.",
        implementation_owner="Root Tranche 15 plus useful_helpers.tools.the_dismantler interface module",
    ),
    ToolCapability(
        key="stable_routing_identity",
        label="Stable Routing Identity",
        target_outcome="Route by a stable declared identifier that is independent of display labels and safe against collision.",
        expected_inputs=("declared tool id", "display label", "existing registrations"),
        expected_outputs=("resolved route", "collision rejection", "rename safety"),
        reference_locators=(LOC_TOOL_KEY, LOC_REGISTER, LOC_RESERVED),
        done_when=STABLE_ROUTING_RULE,
        implementation_owner="useful_helpers.tools registry",
    ),
    ToolCapability(
        key="namespace_isolation",
        label="Namespace Isolation",
        target_outcome="Keep tool identifiers in a separate namespace from core subsystem identifiers, with collision protection derived from actual registrations.",
        expected_inputs=("registered core subsystems", "registered tools", "candidate identifier"),
        expected_outputs=("namespace verdict", "rejection reason", "registration record"),
        reference_locators=(LOC_RESERVED, LOC_REGISTER),
        done_when="A tool can never shadow a core subsystem, and the guard cannot go stale when a new subsystem is added.",
        implementation_owner="useful_helpers.tools registry",
    ),
    ToolCapability(
        key="safe_tool_loading",
        label="Safe Tool Loading",
        target_outcome="Load tools from a declared reviewed registry without executing arbitrary code discovered in a directory.",
        expected_inputs=("declared tool manifest", "candidate module", "review state"),
        expected_outputs=("loaded tool set", "rejected candidates", "load diagnostics"),
        reference_locators=(LOC_DISCOVERY, LOC_LISTDIR, LOC_EXEC_MODULE, LOC_DROPIN_README),
        done_when=SAFE_LOADING_RULE,
        implementation_owner="useful_helpers.tools loader",
    ),
    ToolCapability(
        key="authority_enforced_dispatch",
        label="Authority Enforced Dispatch",
        target_outcome="Check declared authority and path containment on every dispatched operation before the tool runs.",
        expected_inputs=("tool authority", "operation scope", "approved roots", "calling client", "confirmation"),
        expected_outputs=("authorization verdict", "containment verdict", "blocked-operation reason"),
        reference_locators=(LOC_EXECUTE_TASK, LOC_PROJECT_ROOT, LOC_SYSTEM_ROUTE),
        done_when="No dispatched operation reaches a tool without an authority check and a containment check, using the model already present in the repository's tools/ convention.",
        implementation_owner="Root Tranche 15 plus useful_helpers.tools authority module",
    ),
    ToolCapability(
        key="workflow_orchestration",
        label="Workflow Orchestration",
        target_outcome="Run declared multi-step sequences through the same chokepoint, threading each step's output into the next, without UI dependencies.",
        expected_inputs=("workflow definition", "initial context", "status callback"),
        expected_outputs=("step results", "threaded context", "workflow record", "failure stop point"),
        reference_locators=(LOC_WORKFLOW_BIND, LOC_STEP_REGISTRY, LOC_REGISTER_STEP),
        done_when="Workflows are declared data rather than class-level mutable state, and a workflow run is indistinguishable from a human or agent run at the chokepoint.",
        implementation_owner="useful_helpers.tools.the_dismantler workflow module",
    ),
    ToolCapability(
        key="non_blocking_execution",
        label="Non-Blocking Execution",
        target_outcome="Run long operations off the Tk event loop with progress, cancellation, and safe result marshalling back to the UI thread.",
        expected_inputs=("operation handle", "cancellation token", "progress sink"),
        expected_outputs=("progress events", "cancellation result", "marshalled result"),
        reference_locators=(LOC_UI_CALL, LOC_THREAD_LAUNCH, LOC_TK_BOOTSTRAP),
        done_when="No dispatched operation can freeze the workbench UI, and the framework enforces the threading rule rather than documenting it.",
        implementation_owner="Root Tranche 15 plus useful_helpers.ui execution module",
    ),
    ToolCapability(
        key="dispatch_provenance",
        label="Dispatch Provenance",
        target_outcome="Record every dispatch with its originating client, arguments, outcome, and diagnostics so history is reviewable.",
        expected_inputs=("dispatch record", "client identity", "outcome", "diagnostics"),
        expected_outputs=("attributed history", "reviewable log", "preserved failure detail"),
        reference_locators=(LOC_EXECUTE_TASK, LOC_SUCCESS, LOC_LIST_TOOLS),
        done_when="A human can review what the agent dispatched and what happened, and failures retain enough detail to diagnose rather than only a stringified message.",
        implementation_owner="Root Tranche 15 plus useful_helpers.tools provenance module",
    ),
)


THE_DISMANTLER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the TheDISMANTLER tool."""

    return THE_DISMANTLER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all TheDISMANTLER capabilities currently planned for re-homing."""

    return THE_DISMANTLER_CONTRACT.capabilities


def single_chokepoint_notice() -> str:
    """Return the rule requiring one dispatch path for every caller."""

    return SINGLE_CHOKEPOINT_RULE


def safe_loading_notice() -> str:
    """Return the rule that forbids adopting drop-in arbitrary code execution."""

    return SAFE_LOADING_RULE


def stable_routing_notice() -> str:
    """Return the rule governing routing identity and namespace separation."""

    return STABLE_ROUTING_RULE


def convergent_doctrine_notice() -> str:
    """Return the record of three references independently stating one principle."""

    return CONVERGENT_DOCTRINE_NOTE


def framework_input_notice() -> str:
    """Return what each of the four Root Tranche 15 inputs contributes."""

    return FRAMEWORK_INPUT_NOTE


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(THE_DISMANTLER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return THE_DISMANTLER_CONTRACT.reference_retirement_rule
