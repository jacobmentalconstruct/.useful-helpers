"""UiMAPPER tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the UiMAPPER
behavior Useful Helpers may re-home from the reference app before runtime
adapters start scanning projects for UI surfaces.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
UiMAPPER tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "ui_mapper"
TOOL_LABEL = "UiMAPPER"
STATUS = "contract reviewed; implementation pending"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_UiMAPPER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}src/app.py"
REFERENCE_UI_PATH = f"{SOURCE_REFERENCE}src/ui.py"
REFERENCE_BACKEND_PATH = f"{SOURCE_REFERENCE}src/backend.py"
REFERENCE_README_PATH = f"{SOURCE_REFERENCE}README.md"
REFERENCE_TOOLS_PATH = f"{SOURCE_REFERENCE}tools/"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each UiMAPPER "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

DONE_STATE = (
    "UiMAPPER integration is complete when Useful Helpers can run a local, "
    "stdlib-friendly UI-mapping pipeline over an explorer-selected Python "
    "project, honor exclusions and gitignore rules, enumerate Python files, "
    "parse ASTs, detect Tkinter/customtkinter windows, widgets, layout calls, "
    "configuration calls, bindings, menu calls, and callback targets, build a "
    "callback graph, collect unknown cases, optionally prepare inference/HITL "
    "decision plans only when configured, serialize markdown/json/jsonl report "
    "artifacts, surface progress/cancel/log/session state in the GUI, and do "
    "all of that from local Useful Helpers modules with no runtime dependency "
    "on the parts-bin reference app."
)

OPTIONAL_INFERENCE_RULE = (
    "Ollama/inference/HITL behavior is optional and must not be required for "
    "the base UiMAPPER done state. A missing Ollama model or service must be a "
    "visible skipped state, not a hard failure."
)

REFERENCE_FRAILTIES = (
    "Reference app is Python/Tkinter focused; Useful Helpers must not treat it as a general UI detector yet.",
    "Reference inference path depends on local Ollama configuration and must remain optional.",
    "Reference GUI helper microservices overlap with Useful Helpers shell concerns and should inform design, not replace local UI modules wholesale.",
    "Reference maintenance scripts rewrite imports and inspect microservice constructors; they are provenance/repair tools, not runtime features.",
)


def locator(reference_path: str, label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, reference_path)


LOC_README_GOAL = locator(
    REFERENCE_README_PATH,
    "README goal",
    "UI map + callback graph + report artifacts",
    6,
    "Defines the product output target for the reference app.",
)
LOC_APP_SHELL = locator(
    REFERENCE_APP_PATH,
    "dumb shell entrypoint",
    "def main",
    32,
    "Creates the Tk root, gets backend, builds UI, and enters mainloop.",
)
LOC_APP_WIRING = locator(
    REFERENCE_APP_PATH,
    "shell wiring",
    "build_ui(root, backend)",
    56,
    "Shows app-shell composition between backend and UI orchestrator.",
)
LOC_UI_ORCHESTRATOR = locator(
    REFERENCE_UI_PATH,
    "UI orchestrator",
    "class UiOrchestrator",
    122,
    "Owns Tk layout, controls, results, logs, polling, and decision-plan display.",
)
LOC_UI_PROGRESS = locator(
    REFERENCE_UI_PATH,
    "progress subscription",
    "self.bus.subscribe",
    150,
    "Subscribes UI to backend progress events.",
)
LOC_UI_RUN = locator(
    REFERENCE_UI_PATH,
    "run command",
    "_run_clicked",
    511,
    "Starts a UiMAPPER backend run from GUI settings.",
)
LOC_UI_DECISION = locator(
    REFERENCE_UI_PATH,
    "decision plan view",
    "_view_decision_plan",
    546,
    "Displays staged HITL decision plans from optional inference.",
)
LOC_BACKEND_SETTINGS = locator(
    REFERENCE_BACKEND_PATH,
    "backend settings",
    "class BackendSettings",
    92,
    "Defines inference toggles, thresholds, and report output flags.",
)
LOC_BACKEND_ORCHESTRATOR = locator(
    REFERENCE_BACKEND_PATH,
    "backend orchestrator",
    "class BackendOrchestrator",
    119,
    "Owns pipeline lifecycle, microservice wiring, session state, and progress emission.",
)
LOC_BACKEND_START = locator(
    REFERENCE_BACKEND_PATH,
    "start run",
    "def start_run",
    170,
    "Starts a mapping run for a selected project root.",
)
LOC_BACKEND_CANCEL = locator(
    REFERENCE_BACKEND_PATH,
    "cancel run",
    "def cancel_run",
    225,
    "Cancels the active backend run.",
)
LOC_BACKEND_UNKNOWN = locator(
    REFERENCE_BACKEND_PATH,
    "unknown consolidation",
    "self.unknown_collector_ms.record",
    361,
    "Moves UI-map unknowns into a collector for reporting and optional inference.",
)
LOC_BACKEND_GRAPH = locator(
    REFERENCE_BACKEND_PATH,
    "callback graph stage",
    "self.cb_graph_ms.build",
    396,
    "Builds a callback graph from parsed ASTs and the UI map.",
)
LOC_BACKEND_INFERENCE = locator(
    REFERENCE_BACKEND_PATH,
    "optional inference stage",
    "settings.enable_inference",
    416,
    "Runs inference only when enabled and configured.",
)
LOC_BACKEND_REPORTS = locator(
    REFERENCE_BACKEND_PATH,
    "report writing stage",
    "self.report_writer_ms.write_markdown",
    531,
    "Writes markdown/json/jsonl report artifacts.",
)
LOC_GITIGNORE = locator(
    f"{SOURCE_REFERENCE}src/microservices/GitignoreFilterMS.py",
    "gitignore filter",
    "class GitignoreFilterMS",
    50,
    "Builds path predicates for gitignore-aware crawling.",
)
LOC_CRAWL = locator(
    f"{SOURCE_REFERENCE}src/microservices/ProjectCrawlMS.py",
    "project crawl",
    "class ProjectCrawlMS",
    50,
    "Crawls a project tree into entries for downstream Python file enumeration.",
)
LOC_ENUMERATE = locator(
    f"{SOURCE_REFERENCE}src/microservices/PythonFileEnumeratorMS.py",
    "Python file enumerator",
    "def enumerate",
    80,
    "Filters crawl entries down to Python files.",
)
LOC_ENTRYPOINTS = locator(
    f"{SOURCE_REFERENCE}src/microservices/EntrypointFinderMS.py",
    "entrypoint finder",
    "def find_candidates",
    80,
    "Scores likely Python UI entrypoint files.",
)
LOC_AST_PARSE = locator(
    f"{SOURCE_REFERENCE}src/microservices/AstParseCacheMS.py",
    "AST parse cache",
    "def parse",
    70,
    "Parses Python files into cached AST results with syntax-error records.",
)
LOC_TK_DETECTOR = locator(
    f"{SOURCE_REFERENCE}src/microservices/TkWidgetDetectorMS.py",
    "Tk widget detector",
    "class TkWidgetDetectorMS",
    60,
    "Detects Tk root, widget constructor, layout, config, bind, and menu calls.",
)
LOC_AST_UI_MAP = locator(
    f"{SOURCE_REFERENCE}src/microservices/AstUiMapMS.py",
    "AST UI mapper",
    "def map_project",
    103,
    "Builds the UiMap from parsed ASTs and parsed-error records.",
)
LOC_UI_MODEL = locator(
    f"{SOURCE_REFERENCE}src/microservices/UiMapModelMS.py",
    "UI map model",
    "class UiMap",
    80,
    "Defines windows, widgets, unknowns, parse errors, metadata, and callback edges.",
)
LOC_CALLBACK_GRAPH = locator(
    f"{SOURCE_REFERENCE}src/microservices/CallbackGraphBuilderMS.py",
    "callback graph builder",
    "def build",
    81,
    "Builds event-to-handler and function-call graph records.",
)
LOC_UNKNOWN_COLLECTOR = locator(
    f"{SOURCE_REFERENCE}src/microservices/UnknownCaseCollectorMS.py",
    "unknown collector",
    "class UnknownCaseCollectorMS",
    74,
    "Records, summarizes, and selects unknown mapping cases.",
)
LOC_PROMPT = locator(
    f"{SOURCE_REFERENCE}src/microservices/InferencePromptBuilderMS.py",
    "inference prompt builder",
    "def build_prompt",
    46,
    "Builds deterministic prompts for selected unknown cases.",
)
LOC_OLLAMA = locator(
    f"{SOURCE_REFERENCE}src/microservices/OllamaClientMS.py",
    "Ollama client",
    "def generate",
    74,
    "Calls a local Ollama model for optional inference.",
)
LOC_VALIDATE = locator(
    f"{SOURCE_REFERENCE}src/microservices/InferenceResultValidatorMS.py",
    "inference result validator",
    "def validate_json_text",
    86,
    "Validates structured inference output before any decision routing.",
)
LOC_HITL = locator(
    f"{SOURCE_REFERENCE}src/microservices/HitlDecisionRouterMS.py",
    "HITL decision router",
    "def build_plan",
    72,
    "Builds auto-apply, ask-user, and reject decision plans from validated inference.",
)
LOC_SERIALIZER = locator(
    f"{SOURCE_REFERENCE}src/microservices/ReportSerializerMS.py",
    "report serializer",
    "class ReportSerializerMS",
    42,
    "Serializes UiMap outputs to JSON and JSONL.",
)
LOC_WRITER = locator(
    f"{SOURCE_REFERENCE}src/microservices/ReportWriterMS.py",
    "markdown report writer",
    "def write_markdown",
    137,
    "Writes a markdown UI map report.",
)
LOC_EVENTS = locator(
    f"{SOURCE_REFERENCE}src/microservices/ProgressEventBusMS.py",
    "progress event bus",
    "class ProgressEventBusMS",
    48,
    "Publishes and subscribes to progress events.",
)
LOC_SESSION = locator(
    f"{SOURCE_REFERENCE}src/microservices/RunSessionStateMS.py",
    "run session state",
    "class RunSessionState",
    47,
    "Stores counters, status, reports, UI map, callback graph, and errors.",
)
LOC_CANCEL = locator(
    f"{SOURCE_REFERENCE}src/microservices/CancellationTokenMS.py",
    "cancellation token",
    "class CancellationTokenMS",
    30,
    "Provides thread-safe cancellation for long-running operations.",
)
LOC_FIX_TOOL = locator(
    f"{REFERENCE_TOOLS_PATH}fix.py",
    "maintenance import rewriter",
    "rewrite_imports_in_file",
    28,
    "Reference maintenance script that rewrites imports; not runtime behavior.",
)
LOC_INIT_CHECK = locator(
    f"{REFERENCE_TOOLS_PATH}check_ms_inits.py",
    "microservice constructor checker",
    "def main",
    10,
    "Reference maintenance script for inspecting microservice constructors.",
)


CAPABILITIES = (
    ToolCapability(
        key="scan_python_project",
        label="Scan Python Project",
        target_outcome=(
            "Given an explorer-selected project root, crawl project entries while "
            "honoring exclusions and gitignore-style filters, then enumerate Python files."
        ),
        expected_inputs=("project root path", "exclusion policy", "gitignore filter", "optional cancellation signal"),
        expected_outputs=("crawl entries", "Python file list", "skipped/ignored path evidence"),
        reference_locators=(LOC_GITIGNORE, LOC_CRAWL, LOC_ENUMERATE),
        done_when=(
            "Useful Helpers can identify the Python files eligible for UI mapping "
            "without importing the reference app or traversing excluded folders."
        ),
        implementation_owner="useful_helpers.tools.ui_mapper discovery module",
    ),
    ToolCapability(
        key="detect_entrypoints",
        label="Detect UI Entrypoints",
        target_outcome="Score likely Tkinter application entrypoints from the enumerated Python files.",
        expected_inputs=("project root path", "Python file list"),
        expected_outputs=("ranked entrypoint candidates", "score reasons"),
        reference_locators=(LOC_ENTRYPOINTS,),
        done_when="The right pane/tool surface can show likely UI entrypoints before or after a full map run.",
        implementation_owner="useful_helpers.tools.ui_mapper entrypoints module",
    ),
    ToolCapability(
        key="parse_ast_cache",
        label="Parse Python AST Cache",
        target_outcome="Parse eligible Python files into reusable AST results with stable parse-error records.",
        expected_inputs=("Python file list", "encoding policy", "optional cancellation signal"),
        expected_outputs=("path-to-AST map", "parse error list", "cache hit/miss metadata"),
        reference_locators=(LOC_AST_PARSE,),
        done_when="Full map runs reuse parsed ASTs and report syntax errors without failing the entire operation.",
        implementation_owner="useful_helpers.tools.ui_mapper ast module",
    ),
    ToolCapability(
        key="map_tkinter_ui_surface",
        label="Map Tkinter UI Surface",
        target_outcome=(
            "Detect Tkinter/customtkinter windows, widgets, layout/config/bind/menu "
            "calls, parent-child structure, callback attributes, and unknown cases."
        ),
        expected_inputs=("project root path", "path-to-AST map", "parse error list"),
        expected_outputs=("UiMap windows", "UiMap widgets", "unknown mapping cases", "parse errors"),
        reference_locators=(LOC_TK_DETECTOR, LOC_AST_UI_MAP, LOC_UI_MODEL),
        done_when=(
            "Useful Helpers can produce a structured UI map for Python Tk projects "
            "and serialize it through local models."
        ),
        implementation_owner="useful_helpers.tools.ui_mapper mapper module",
    ),
    ToolCapability(
        key="build_callback_graph",
        label="Build Callback Graph",
        target_outcome="Build event-to-handler and internal function-call graph records from the UI map and ASTs.",
        expected_inputs=("path-to-AST map", "UiMap"),
        expected_outputs=("graph nodes", "graph edges", "unresolved graph unknowns"),
        reference_locators=(LOC_CALLBACK_GRAPH, LOC_BACKEND_GRAPH),
        done_when="Useful Helpers can show or export callback relationships for mapped UI projects.",
        implementation_owner="useful_helpers.tools.ui_mapper graph module",
    ),
    ToolCapability(
        key="collect_unknown_cases",
        label="Collect Unknown Cases",
        target_outcome="Capture uncertain UI detections for reporting, review, and optional inference routing.",
        expected_inputs=("UiMap unknowns", "AST node context", "selection policy"),
        expected_outputs=("deduplicated unknown cases", "summaries by kind", "summaries by file"),
        reference_locators=(LOC_UNKNOWN_COLLECTOR, LOC_BACKEND_UNKNOWN),
        done_when="Unknowns are visible as first-class evidence instead of silent mapping loss.",
        implementation_owner="useful_helpers.tools.ui_mapper unknowns module",
    ),
    ToolCapability(
        key="optional_inference_hitl",
        label="Optional Inference And HITL",
        target_outcome=(
            "Optionally prepare prompts for unknown cases, validate model output, "
            "and route decisions into auto-apply, ask-user, or reject buckets."
        ),
        expected_inputs=("unknown cases", "project context", "optional Ollama model", "HITL policy thresholds"),
        expected_outputs=("prompt text", "validated decisions", "decision plan", "skipped inference state"),
        reference_locators=(LOC_BACKEND_INFERENCE, LOC_PROMPT, LOC_OLLAMA, LOC_VALIDATE, LOC_HITL, LOC_UI_DECISION),
        done_when=OPTIONAL_INFERENCE_RULE,
        implementation_owner="useful_helpers.tools.ui_mapper optional inference module",
    ),
    ToolCapability(
        key="serialize_and_write_reports",
        label="Serialize And Write Reports",
        target_outcome="Write markdown, JSON, and JSONL artifacts for the UI map and callback graph.",
        expected_inputs=("UiMap", "callback graph", "output directory", "format toggles"),
        expected_outputs=("markdown report path", "JSON report path", "JSONL report path"),
        reference_locators=(LOC_SERIALIZER, LOC_WRITER, LOC_BACKEND_REPORTS),
        done_when="A completed run produces selected report artifacts with paths surfaced in the GUI.",
        implementation_owner="useful_helpers.tools.ui_mapper reports module",
    ),
    ToolCapability(
        key="run_pipeline_with_progress",
        label="Run Pipeline With Progress",
        target_outcome=(
            "Coordinate scan, parse, map, graph, optional inference, and reporting "
            "as a cancellable background operation with session-state updates."
        ),
        expected_inputs=("project root path", "backend settings", "progress subscriber", "cancellation token"),
        expected_outputs=("session status", "progress events", "counters", "errors", "report paths"),
        reference_locators=(LOC_BACKEND_SETTINGS, LOC_BACKEND_ORCHESTRATOR, LOC_BACKEND_START, LOC_BACKEND_CANCEL, LOC_EVENTS, LOC_SESSION, LOC_CANCEL),
        done_when=(
            "The workbench can run UiMAPPER without freezing the GUI, cancel an "
            "active run, and inspect the final session snapshot."
        ),
        implementation_owner="useful_helpers.tools.ui_mapper orchestrator module",
    ),
    ToolCapability(
        key="ui_mapper_gui_workflow",
        label="UiMAPPER GUI Workflow",
        target_outcome=(
            "Expose project selection, run/cancel controls, progress logs, result "
            "summaries, structure tree, report paths, copied JSON, and decision-plan viewing."
        ),
        expected_inputs=("selected project root", "run settings", "backend session state", "progress events"),
        expected_outputs=("tool form state", "log lines", "summary rows", "structure tree", "decision-plan dialog"),
        reference_locators=(LOC_README_GOAL, LOC_APP_SHELL, LOC_APP_WIRING, LOC_UI_ORCHESTRATOR, LOC_UI_PROGRESS, LOC_UI_RUN),
        done_when=(
            "Useful Helpers exposes UiMAPPER as a Tools menu workflow while keeping "
            "the main explorer-first shell as the front door."
        ),
        implementation_owner="Useful Helpers UI plus ui_mapper adapter",
    ),
    ToolCapability(
        key="maintenance_tools_reference_only",
        label="Maintenance Tools Reference Only",
        target_outcome=(
            "Treat reference import-rewrite and constructor-inspection scripts as "
            "historical repair evidence, not product behavior."
        ),
        expected_inputs=("none for runtime",),
        expected_outputs=("deferred maintenance notes",),
        reference_locators=(LOC_FIX_TOOL, LOC_INIT_CHECK),
        done_when="No Useful Helpers runtime command depends on these reference maintenance scripts.",
        implementation_owner="deferred maintenance tranche",
    ),
)


UI_MAPPER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the UiMAPPER tool."""

    return UI_MAPPER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all UiMAPPER capabilities currently planned for re-homing."""

    return UI_MAPPER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(UI_MAPPER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return UI_MAPPER_CONTRACT.reference_retirement_rule
