"""WASM Inference Wrapper tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the target
shape for packaging a local agent behind a WASM-shaped deployable runtime
boundary. The current parts-bin reference is useful bootstrap evidence, but it
is Python/FastAPI/llama.cpp rather than a real WASM deployment wrapper.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
WASM Inference Wrapper tool no longer depends on the reference app for design
recovery, runtime modules must not import from, read from, or require the parts
bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "wasm_inference_wrapper"
TOOL_LABEL = "WASM Inference Wrapper"
STATUS = "contract scaffolded; implementation pending; reference is not true WASM"

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_WasmInferenceWRAPPER/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}wrapper_installer.py"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each WASM Inference "
    "Wrapper capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

WASM_INTENT_RULE = (
    "The accepted product intent is a deployable local-agent wrapper with a "
    "WASM-shaped runtime boundary. The reference installer is only a bootstrap "
    "guide because it creates a Python FastAPI llama.cpp node, not a WASM module."
)

LOCAL_INSTALL_SAFETY_RULE = (
    "No install/build/download action is complete until the destination is an "
    "explicit side-car/output folder, the model/runtime source is previewed, "
    "network and dependency installation are separately confirmed, generated "
    "files are listed, and no process-kill or server-start mutation runs silently."
)

DONE_STATE = (
    "WASM Inference Wrapper integration is complete when Useful Helpers can "
    "package or scaffold a local agent runtime behind an explicit WASM-shaped "
    "deployment boundary, define its manifest, model/runtime inputs, sandboxed "
    "filesystem/network permissions, request/response contract, build/install "
    "plan, generated artifacts, local test harness, and deployment handoff; can "
    "preview and confirm downloads, dependency installs, and output writes; can "
    "record node registry metadata without stale entries; and can do all of that "
    "from local Useful Helpers modules with no runtime dependency on the "
    "parts-bin reference installer."
)

REFERENCE_FRAILTIES = (
    "Reference name says WASM, but current code generates a Python FastAPI llama-cpp-python server, not a WASM module.",
    "Installer performs network model downloads and pip installs from a GUI action without a reusable dry-run plan.",
    "Generated killtheUVICORN.py can force-kill processes by port and must not be adopted blindly.",
    "Generated wrapper likely indexes llama.cpp chat response incorrectly as response['choices']['message']['content'] instead of choices[0].",
    "Generated registry can retain stale nodes and has only ad-hoc cleanup through the chat UI.",
    "Default model URL points to a remote Hugging Face GGUF and requires explicit user/network consent before use.",
)


def locator(label: str, symbol: str, line: int, purpose: str) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, REFERENCE_APP_PATH)


LOC_REQUIREMENTS = locator("generated requirements", "REQUIREMENTS_TEXT", 12, "Defines generated Python dependencies including FastAPI, Uvicorn, pydantic, llama-cpp-python, and requests.")
LOC_WRAPPER = locator("generated wrapper payload", "WRAPPER_TEXT", 19, "Defines the generated FastAPI model node wrapper.")
LOC_REGISTRY = locator("swarm registry", "REGISTRY_FILE", 25, "Stores generated node metadata in a sibling swarm_registry.json file.")
LOC_LIFESPAN = locator("registry lifespan", "async def lifespan", 54, "Registers and unregisters node metadata on FastAPI lifespan events.")
LOC_MODEL_PATH = locator("model path", "MODEL_PATH", 60, "Reads the model path from environment or ./models/model.gguf.")
LOC_LLAMA = locator("llama cpp load", "Llama(model_path=MODEL_PATH", 63, "Loads a GGUF model through llama-cpp-python.")
LOC_GENERATE = locator("generate endpoint", "@app.post(\"/generate\")", 68, "Defines the generated HTTP inference endpoint.")
LOC_RESPONSE_INDEX = locator("chat response extraction", "response[\"choices\"][\"message\"][\"content\"]", 75, "Shows likely incorrect llama.cpp response indexing that must be repaired.")
LOC_RUN_BAT = locator("Windows server runner", "RUN_BAT_TEXT", 78, "Defines generated run.bat for Uvicorn server startup.")
LOC_RUN_SH = locator("POSIX server runner", "RUN_SH_TEXT", 94, "Defines generated run.sh for Uvicorn server startup.")
LOC_KILL = locator("port kill helper", "KILL_SCRIPT_TEXT", 108, "Defines generated process-kill helper; dangerous and reference-only.")
LOC_CHAT_UI = locator("generated chat UI", "CHAT_UI_TEXT", 146, "Defines generated Tk chat UI for active nodes.")
LOC_CHAT_POST = locator("chat requests post", "requests.post", 247, "Sends prompts to the selected generated node endpoint.")
LOC_PY_DISCOVERY = locator("Python discovery", "def get_valid_pythons", 281, "Finds Python 3.8-3.11 interpreters for llama-cpp-python compatibility.")
LOC_INSTALLER = locator("installer GUI", "def start_installer", 304, "Defines the bootstrapper GUI and install flow.")
LOC_DEFAULT_MODEL = locator("default model URL", "Qwen2.5-0.5B-Instruct-GGUF", 328, "Uses a remote Hugging Face GGUF as the default model download.")
LOC_WRITE_PAYLOADS = locator("payload file writes", "with open(os.path.join(target_dir", 376, "Writes generated requirements, wrapper, chat UI, kill helper, and run scripts.")
LOC_VENV = locator("venv creation", "subprocess.check_call([target_python_exe, \"-m\", \"venv\"", 396, "Creates a local virtual environment.")
LOC_PIP_INSTALL = locator("dependency install", "pip_exe, \"install\", \"-r\"", 405, "Installs generated Python dependencies.")
LOC_MODEL_DOWNLOAD = locator("model download", "urllib.request.urlopen", 412, "Downloads the configured GGUF model URL.")


CAPABILITIES = (
    ToolCapability(
        key="define_wasm_agent_manifest",
        label="Define WASM Agent Manifest",
        target_outcome="Describe the agent package boundary: name, runtime type, entrypoints, model/runtime inputs, permissions, resources, and deployment target.",
        expected_inputs=("agent name", "runtime kind", "model source", "permissions", "resource limits", "deployment target"),
        expected_outputs=("manifest preview", "validation findings", "artifact plan"),
        reference_locators=(LOC_INSTALLER, LOC_DEFAULT_MODEL),
        done_when="A user can see exactly what local agent wrapper will be generated before any write/download/install occurs.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper manifest module",
    ),
    ToolCapability(
        key="repair_runtime_boundary",
        label="Repair Runtime Boundary",
        target_outcome="Replace the reference Python-server-only shape with an explicit WASM-shaped adapter boundary or a clearly marked Python fallback mode.",
        expected_inputs=("reference payload", "target runtime mode", "fallback policy"),
        expected_outputs=("runtime boundary plan", "WASM/fallback decision", "unsupported-case warnings"),
        reference_locators=(LOC_WRAPPER, LOC_LLAMA, LOC_GENERATE),
        done_when="The tool no longer pretends the Python FastAPI node is WASM; the runtime boundary is explicit and testable.",
        implementation_owner="wasm_inference_wrapper architecture tranche",
    ),
    ToolCapability(
        key="plan_local_agent_install",
        label="Plan Local Agent Install",
        target_outcome="Create a dry-run plan for output folder creation, generated files, dependencies, model files, scripts, registry records, and test commands.",
        expected_inputs=("manifest", "output folder", "model URL or local model", "dependency policy"),
        expected_outputs=("install plan", "file list", "network actions", "dependency actions", "risk prompts"),
        reference_locators=(LOC_REQUIREMENTS, LOC_WRITE_PAYLOADS, LOC_VENV, LOC_PIP_INSTALL, LOC_MODEL_DOWNLOAD),
        done_when=LOCAL_INSTALL_SAFETY_RULE,
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper planner module",
    ),
    ToolCapability(
        key="generate_runtime_artifacts",
        label="Generate Runtime Artifacts",
        target_outcome="Generate wrapper/runtime source, run scripts, metadata, and optional UI/test harness into an approved side-car output folder.",
        expected_inputs=("approved install plan", "output folder", "template selections"),
        expected_outputs=("generated artifact paths", "checksums", "write result records"),
        reference_locators=(LOC_WRAPPER, LOC_RUN_BAT, LOC_RUN_SH, LOC_CHAT_UI, LOC_WRITE_PAYLOADS),
        done_when="All generated files are listed, written locally, and can be removed without affecting the target project.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper generator module",
    ),
    ToolCapability(
        key="model_source_and_download_gate",
        label="Model Source And Download Gate",
        target_outcome="Support local model selection or URL download with explicit network consent, file size/status reporting, and checksum metadata when available.",
        expected_inputs=("model URL or local path", "network consent", "destination", "checksum option"),
        expected_outputs=("download plan", "model file path", "download result", "checksum record"),
        reference_locators=(LOC_DEFAULT_MODEL, LOC_MODEL_DOWNLOAD, LOC_MODEL_PATH),
        done_when="No remote model is downloaded until the user confirms the URL, destination, and expected artifact.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper model module",
    ),
    ToolCapability(
        key="node_registry_management",
        label="Node Registry Management",
        target_outcome="Record, list, validate, and clean local agent node registry entries without stale hidden state.",
        expected_inputs=("node metadata", "health-check result", "cleanup decision"),
        expected_outputs=("registry record", "active/stale state", "cleanup result"),
        reference_locators=(LOC_REGISTRY, LOC_LIFESPAN, LOC_CHAT_UI),
        done_when="Registry records are transparent, scoped, health-checkable, and removable from the Useful Helpers UI.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper registry module",
    ),
    ToolCapability(
        key="inference_endpoint_contract",
        label="Inference Endpoint Contract",
        target_outcome="Define request/response schema for prompt generation and repair reference response parsing before runtime use.",
        expected_inputs=("prompt", "generation settings", "endpoint URL"),
        expected_outputs=("result text", "error payload", "timing/metadata"),
        reference_locators=(LOC_GENERATE, LOC_RESPONSE_INDEX, LOC_CHAT_POST),
        done_when="Endpoint behavior is schema-tested and response extraction handles real llama.cpp return payloads.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper endpoint module",
    ),
    ToolCapability(
        key="safe_process_controls",
        label="Safe Process Controls",
        target_outcome="Replace force-kill helper behavior with visible process plans, health checks, and explicit user confirmation.",
        expected_inputs=("port", "process list", "user confirmation"),
        expected_outputs=("process plan", "start/stop result", "blocked risky action"),
        reference_locators=(LOC_KILL, LOC_RUN_BAT, LOC_RUN_SH),
        done_when="No server start/stop/kill command executes silently or broadly; force-kill remains blocked unless explicitly designed later.",
        implementation_owner="useful_helpers.tools.wasm_inference_wrapper process module",
    ),
    ToolCapability(
        key="local_test_harness",
        label="Local Test Harness",
        target_outcome="Provide a local test surface for generated wrappers without making the reference chat UI the final UX.",
        expected_inputs=("running node", "test prompt", "endpoint contract"),
        expected_outputs=("test result", "logs", "failure explanation"),
        reference_locators=(LOC_CHAT_UI, LOC_CHAT_POST),
        done_when="Generated agents can be smoke-tested from Useful Helpers with clear logs and no dependency on the reference chat UI.",
        implementation_owner="Useful Helpers UI plus wasm_inference_wrapper backend",
    ),
)


WASM_INFERENCE_WRAPPER_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the WASM Inference Wrapper tool."""

    return WASM_INFERENCE_WRAPPER_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all WASM Inference Wrapper capabilities currently planned for re-homing."""

    return WASM_INFERENCE_WRAPPER_CONTRACT.capabilities


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(WASM_INFERENCE_WRAPPER_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return WASM_INFERENCE_WRAPPER_CONTRACT.reference_retirement_rule