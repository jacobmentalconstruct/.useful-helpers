"""TheCELL tool contract and reference implementation map.

This module is intentionally semantic, not operational. It records the
TheCELL behavior Useful Helpers may re-home from the reference app before
runtime adapters start exposing cell/workflow orchestration.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
TheCELL tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "the_cell"
TOOL_LABEL = "TheCELL"
STATUS = "contract reviewed; implementation pending; lifecycle not final; DAC required"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_theCELL/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_BACKEND_PATH = f"{SOURCE_REFERENCE}src/backend.py"
REFERENCE_UI_PATH = f"{SOURCE_REFERENCE}src/ui.py"
REFERENCE_README_PATH = f"{SOURCE_REFERENCE}README.md"
REFERENCE_REQUIREMENTS_PATH = f"{SOURCE_REFERENCE}requirements.txt"
REFERENCE_IDENTITY_PATH = f"{SOURCE_REFERENCE}src/cell_identity.py"
REFERENCE_SIGNAL_BUS_PATH = f"{SOURCE_REFERENCE}src/microservices/_SignalBusMS.py"
REFERENCE_SESSION_MANAGER_PATH = f"{SOURCE_REFERENCE}src/microservices/_SessionManagerMS.py"
REFERENCE_SHELL_PATH = f"{SOURCE_REFERENCE}src/microservices/_TkinterAppShellMS.py"
REFERENCE_WORKFLOW_PATH = f"{SOURCE_REFERENCE}_workflows/feature_developer.json"
REFERENCE_SESSIONS_PATH = f"{SOURCE_REFERENCE}_sessions/"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each TheCELL "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

DAC_LIFECYCLE_RULE = (
    "The inspected TheCELL lifecycle is not final. It is recursively shaped: "
    "cells can spawn child windows, route/push content between live cells, carry "
    "inherited context backward into future prompts, and use signal routing "
    "guards to avoid loops. Useful Helpers must not accept that lifecycle as the "
    "final design. The target lifecycle is DAC shaped: Discover source/context, "
    "Act through a bounded forward step, Capture outputs/evidence/state, then "
    "advance only to the next declared step. No child-cell recursion, no "
    "backward loop, and no hidden cross-cell push path may be part of the final "
    "TheCELL integration."
)

DONE_STATE = (
    "TheCELL integration is complete when Useful Helpers exposes a forward-only "
    "DAC workflow surface for agent-assisted project work: selected explorer "
    "context can be discovered or ingested, a declared task/workflow step can "
    "act against that bounded context, outputs and evidence are captured with "
    "session metadata, and the user can advance to the next step without any "
    "recursive child-window lifecycle or backward content routing. The tool "
    "must preserve personas/prompts/workflow templates only through local "
    "Useful Helpers contracts, keep vector/RAG dependencies optional, keep "
    "runtime state under the side-car state policy, expose HITL review before "
    "writes or follow-on actions, and run entirely from local Useful Helpers "
    "modules with no runtime dependency on the parts-bin reference app."
)

REFERENCE_FRAILTIES = (
    "Reference lifecycle is recursive and multi-window; final Useful Helpers lifecycle must be DAC shaped and forward-only.",
    "Reference README describes child-cell spawning and cross-cell push routing with loop guards, which is evidence of a loop hazard rather than an accepted design.",
    "Reference queue passes prior task output as inherited context, which must become an explicit captured artifact instead of implicit backward prompt injection.",
    "Reference includes checked-in _sessions state that must remain provenance only.",
    "Reference requires requests, pydantic, chromadb, faiss-cpu, and numpy; vector/RAG support must stay optional until accepted by a later tranche.",
    "Reference UI mixes prompt setup, ontological steps, task queue, RAG ingest, HITL, and export in one dense Tk surface; final layout needs a Useful Helpers-native DAC workflow design.",
)


def locator(reference_path: str, label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, reference_path)


LOC_README_IDENTITY = locator(
    REFERENCE_README_PATH,
    "README identity",
    "# _theCELL",
    1,
    "Names the reference app and preserves the source folder spelling.",
)
LOC_README_RECURSIVE = locator(
    REFERENCE_README_PATH,
    "recursive workspace claim",
    "A recursive, multi-window Tkinter workspace",
    3,
    "States that the reference lifecycle is recursive and multi-window.",
)
LOC_README_CHILD_CELLS = locator(
    REFERENCE_README_PATH,
    "child cell spawning",
    "Spawn child cells",
    12,
    "Describes child-cell spawning and inherited context.",
)
LOC_README_PUSH_ROUTING = locator(
    REFERENCE_README_PATH,
    "cross-cell routing",
    "Route/push content to another live cell",
    13,
    "Describes live cell-to-cell content routing and loop guards.",
)
LOC_README_RECURSIVE_WORKFLOW = locator(
    REFERENCE_README_PATH,
    "recursive workflow",
    "Recursive workflow",
    48,
    "Names the recursive workflow behavior to replace with DAC.",
)
LOC_BOOTSTRAP = locator(
    REFERENCE_APP_PATH,
    "app bootstrap",
    "def main",
    6,
    "Bootstraps Backend and Tkinter shell for a single reference cell.",
)
LOC_BACKEND = locator(
    REFERENCE_BACKEND_PATH,
    "backend hub",
    "class Backend",
    34,
    "Owns the reference service stack, state, task queue, and inference.",
)
LOC_DB_SCHEMA = locator(
    REFERENCE_BACKEND_PATH,
    "identity repository schema",
    "CREATE TABLE IF NOT EXISTS personas",
    130,
    "Creates local SQLite persona and prompt tables.",
)
LOC_PROCESS_SUBMISSION = locator(
    REFERENCE_BACKEND_PATH,
    "submission artifact",
    "def process_submission",
    233,
    "Builds a structured inference artifact and starts background streaming.",
)
LOC_INHERITED_CONTEXT = locator(
    REFERENCE_BACKEND_PATH,
    "inherited context injection",
    "inherited_context",
    233,
    "Marks implicit previous-output prompt injection that must become explicit DAC capture.",
)
LOC_RUN_QUEUE = locator(
    REFERENCE_BACKEND_PATH,
    "queue runner",
    "def run_queue",
    314,
    "Starts sequential execution of queued tasks.",
)
LOC_START_TASK = locator(
    REFERENCE_BACKEND_PATH,
    "task step runner",
    "def _start_task",
    321,
    "Runs one queued task and subscribes to completion.",
)
LOC_TASK_DONE = locator(
    REFERENCE_BACKEND_PATH,
    "task output forwarding",
    "def _on_task_done",
    350,
    "Passes previous response into the next task, which must be redesigned as explicit capture.",
)
LOC_SESSION_MANAGER = locator(
    REFERENCE_SESSION_MANAGER_PATH,
    "session persistence",
    "class SessionManagerMS",
    40,
    "Owns session directories, metadata, task JSON, and atomic writes.",
)
LOC_INGEST_FILE = locator(
    REFERENCE_BACKEND_PATH,
    "file ingest",
    "def ingest_file",
    425,
    "Adds file content to the active session vector store.",
)
LOC_INGEST_DIR = locator(
    REFERENCE_BACKEND_PATH,
    "directory ingest",
    "def ingest_directory",
    434,
    "Adds directory content to the active session vector store.",
)
LOC_EXPORT = locator(
    REFERENCE_BACKEND_PATH,
    "artifact export",
    "def export_artifact",
    451,
    "Routes generated artifacts to file, vector, or project capture outputs.",
)
LOC_FEEDBACK = locator(
    REFERENCE_BACKEND_PATH,
    "HITL feedback",
    "def record_feedback",
    465,
    "Records accept/reject feedback for generated artifacts.",
)
LOC_IDENTITY = locator(
    REFERENCE_IDENTITY_PATH,
    "cell identity",
    "class CellIdentity",
    9,
    "Generates cell IDs and display names.",
)
LOC_SIGNAL_BUS = locator(
    REFERENCE_SIGNAL_BUS_PATH,
    "event spine",
    "class SignalBusMS",
    22,
    "Provides pub/sub event routing.",
)
LOC_SIGNAL_SPAWN = locator(
    REFERENCE_SIGNAL_BUS_PATH,
    "spawn signal",
    "SIGNAL_SPAWN_REQUESTED",
    31,
    "Names child-cell spawn event to retire for final DAC flow.",
)
LOC_SIGNAL_PUSH = locator(
    REFERENCE_SIGNAL_BUS_PATH,
    "push signal",
    "SIGNAL_PUSH_DATA",
    36,
    "Names cross-cell push event to retire for final DAC flow.",
)
LOC_SPAWN_WINDOW = locator(
    REFERENCE_SHELL_PATH,
    "child window spawn",
    "def spawn_window",
    200,
    "Creates child Tk windows in the recursive reference lifecycle.",
)
LOC_CELL_UI = locator(
    REFERENCE_UI_PATH,
    "cell UI",
    "class CELL_UI",
    360,
    "Owns the reference prompt, queue, RAG, HITL, and export UI.",
)
LOC_ONTO_STEP = locator(
    REFERENCE_UI_PATH,
    "ontological step append",
    "def add_onto_step",
    432,
    "Adds incoming child/push content as a prompt step.",
)
LOC_SERIALIZE_STEPS = locator(
    REFERENCE_UI_PATH,
    "step serialization",
    "def _serialize_onto_steps",
    547,
    "Serializes ontological steps into prompt context.",
)
LOC_SETUP_UI = locator(
    REFERENCE_UI_PATH,
    "main UI setup",
    "def _setup_main_window",
    572,
    "Builds the dense two-column reference UI.",
)
LOC_LOAD_WORKFLOW_BUTTON = locator(
    REFERENCE_UI_PATH,
    "load workflow button",
    "self.btn_load_workflow",
    1038,
    "Exposes workflow JSON loading in the task queue panel.",
)
LOC_LOAD_WORKFLOW = locator(
    REFERENCE_UI_PATH,
    "workflow loader",
    "def _on_load_workflow",
    1815,
    "Loads workflow JSON tasks into the queue.",
)
LOC_WORKFLOW_TASKS = locator(
    REFERENCE_WORKFLOW_PATH,
    "feature workflow tasks",
    "\"tasks\"",
    5,
    "Shows the reference workflow JSON shape: named tasks with role, prompt, and user content.",
)
LOC_REQUIRE_FAISS = locator(
    REFERENCE_REQUIREMENTS_PATH,
    "faiss dependency",
    "faiss-cpu",
    4,
    "Records optional vector dependency that must not become mandatory by accident.",
)
LOC_REQUIRE_CHROMA = locator(
    REFERENCE_REQUIREMENTS_PATH,
    "chromadb dependency",
    "chromadb",
    3,
    "Records optional vector dependency that must not become mandatory by accident.",
)


CAP_BOOTSTRAP = ToolCapability(
    key="bootstrap_single_cell_workspace",
    label="Bootstrap single cell workspace",
    target_outcome=(
        "Provide an optional TheCELL-inspired workspace hosted inside Useful "
        "Helpers without replacing the explorer-first front door."
    ),
    expected_inputs=("active Useful Helpers session", "selected explorer context", "optional workflow template"),
    expected_outputs=("local workspace state", "visible DAC workflow panel", "session metadata"),
    reference_locators=(LOC_BOOTSTRAP, LOC_BACKEND, LOC_CELL_UI, LOC_SETUP_UI),
    done_when=(
        "The workspace launches from local Useful Helpers modules and has no "
        "runtime import/read dependency on the parts-bin reference."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_DAC_LIFECYCLE = ToolCapability(
    key="enforce_forward_only_dac_lifecycle",
    label="Enforce forward-only DAC lifecycle",
    target_outcome=(
        "Replace recursive spawn/push/inherited-context behavior with explicit "
        "Discover, Act, Capture steps that only advance forward."
    ),
    expected_inputs=("declared workflow step", "captured evidence from prior step", "user approval state"),
    expected_outputs=("next eligible step", "captured artifact", "blocked/complete state"),
    reference_locators=(
        LOC_README_RECURSIVE,
        LOC_README_CHILD_CELLS,
        LOC_README_PUSH_ROUTING,
        LOC_README_RECURSIVE_WORKFLOW,
        LOC_SIGNAL_SPAWN,
        LOC_SIGNAL_PUSH,
        LOC_SPAWN_WINDOW,
        LOC_TASK_DONE,
    ),
    done_when=DAC_LIFECYCLE_RULE,
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_IDENTITY = ToolCapability(
    key="manage_cell_identity_and_state",
    label="Manage cell identity and state",
    target_outcome=(
        "Preserve useful cell identity, naming, and session metadata without "
        "creating recursive window identity trees."
    ),
    expected_inputs=("workspace name", "optional existing session", "side-car state root"),
    expected_outputs=("stable cell/workflow id", "display name", "session metadata"),
    reference_locators=(LOC_IDENTITY, LOC_SESSION_MANAGER, LOC_README_IDENTITY),
    done_when=(
        "Identity is stable, searchable, persisted under side-car state, and "
        "does not imply parent/child cell recursion."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_PERSONAS = ToolCapability(
    key="persist_personas_prompts_and_templates",
    label="Persist personas, prompts, and templates",
    target_outcome=(
        "Provide local repositories for reusable roles, system prompts, task "
        "prompts, and DAC workflow templates."
    ),
    expected_inputs=("persona fields", "role text", "system prompt", "task prompt", "template metadata"),
    expected_outputs=("side-car stored template", "default selection metadata", "loadable workflow config"),
    reference_locators=(LOC_DB_SCHEMA, LOC_WORKFLOW_TASKS, LOC_LOAD_WORKFLOW),
    done_when=(
        "Templates are stored in Useful Helpers-owned state with validation, "
        "versioning, and no implicit read from reference _workflows."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_STREAMING = ToolCapability(
    key="run_streamed_agent_step",
    label="Run streamed agent step",
    target_outcome=(
        "Run one bounded DAC Act step with streaming output and structured "
        "artifact metadata."
    ),
    expected_inputs=("selected context", "model id", "role", "system prompt", "task payload"),
    expected_outputs=("stream events", "final response artifact", "error artifact"),
    reference_locators=(LOC_PROCESS_SUBMISSION, LOC_SIGNAL_BUS),
    done_when=(
        "A single step can stream progress into the workbench and produce a "
        "captured artifact without launching child cells or mutating future "
        "steps implicitly."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_QUEUE = ToolCapability(
    key="execute_declared_task_queue",
    label="Execute declared task queue",
    target_outcome=(
        "Load, edit, validate, and run an ordered workflow queue as explicit "
        "DAC steps."
    ),
    expected_inputs=("workflow JSON", "task list edits", "user start/stop decision"),
    expected_outputs=("step progress", "per-step artifact", "complete/blocked state"),
    reference_locators=(LOC_RUN_QUEUE, LOC_START_TASK, LOC_TASK_DONE, LOC_LOAD_WORKFLOW_BUTTON, LOC_LOAD_WORKFLOW, LOC_WORKFLOW_TASKS),
    done_when=(
        "Queue execution is deterministic, cancellable, resumable, and only "
        "passes prior outputs through named captured artifacts."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_CONTEXT = ToolCapability(
    key="ingest_context_for_retrieval",
    label="Ingest context for retrieval",
    target_outcome=(
        "Optionally ingest selected files/folders into a retrieval store for a "
        "declared workflow session."
    ),
    expected_inputs=("explorer selection", "extension policy", "embedding model", "session id"),
    expected_outputs=("chunk counts", "ingested file manifest", "retrieval status"),
    reference_locators=(LOC_INGEST_FILE, LOC_INGEST_DIR, LOC_REQUIRE_FAISS, LOC_REQUIRE_CHROMA),
    done_when=(
        "Retrieval is optional, dependency-gated, side-car contained, and "
        "reported as unavailable without breaking the base workbench."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_EVENTS = ToolCapability(
    key="surface_signal_bus_events",
    label="Surface signal bus events",
    target_outcome=(
        "Expose a local event spine for workflow progress, logs, errors, and "
        "UI updates."
    ),
    expected_inputs=("workflow event", "subscriber contract", "thread boundary"),
    expected_outputs=("delivered event count", "UI-safe update", "audit log entry"),
    reference_locators=(LOC_SIGNAL_BUS, LOC_PROCESS_SUBMISSION),
    done_when=(
        "Event names are local Useful Helpers contracts and cross-thread UI "
        "updates are marshalled safely."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_CAPTURE = ToolCapability(
    key="capture_outputs_feedback_and_exports",
    label="Capture outputs, feedback, and exports",
    target_outcome=(
        "Capture generated artifacts, HITL decisions, export routing, and "
        "evidence records for each DAC step."
    ),
    expected_inputs=("step artifact", "accept/reject decision", "export destination"),
    expected_outputs=("captured artifact", "feedback record", "export result"),
    reference_locators=(LOC_EXPORT, LOC_FEEDBACK, LOC_SESSION_MANAGER),
    done_when=(
        "Each output has provenance, review status, and an explicit storage or "
        "export location under Useful Helpers policy."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)

CAP_ONTO_STEPS = ToolCapability(
    key="replace_ontological_steps_with_captured_evidence",
    label="Replace ontological steps with captured evidence",
    target_outcome=(
        "Convert ad hoc ontological step prompt stacking into explicit captured "
        "evidence objects shown in the DAC workflow."
    ),
    expected_inputs=("captured previous result", "source step id", "user inclusion decision"),
    expected_outputs=("evidence card", "prompt context manifest", "audit trail"),
    reference_locators=(LOC_ONTO_STEP, LOC_SERIALIZE_STEPS, LOC_INHERITED_CONTEXT),
    done_when=(
        "Prior outputs are never silently injected; the user can see, include, "
        "exclude, and audit every captured evidence item."
    ),
    implementation_owner="useful_helpers.tools.the_cell",
)


CAPABILITIES = (
    CAP_BOOTSTRAP,
    CAP_DAC_LIFECYCLE,
    CAP_IDENTITY,
    CAP_PERSONAS,
    CAP_STREAMING,
    CAP_QUEUE,
    CAP_CONTEXT,
    CAP_EVENTS,
    CAP_CAPTURE,
    CAP_ONTO_STEPS,
)


THE_CELL_CONTRACT = ToolContract(
    key=TOOL_KEY,
    label=TOOL_LABEL,
    status=STATUS,
    source_reference=SOURCE_REFERENCE,
    reference_app_path=REFERENCE_APP_PATH,
    reference_retirement_rule=REFERENCE_RETIREMENT_RULE,
    done_state=DONE_STATE,
    capabilities=CAPABILITIES,
)


def get_contract() -> ToolContract:
    """Return the semantic integration contract for the TheCELL tool."""
    return THE_CELL_CONTRACT


def get_capabilities() -> tuple[ToolCapability, ...]:
    """Return all TheCELL capabilities currently planned for re-homing."""
    return CAPABILITIES
