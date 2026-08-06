"""manifold-mcp tool contract and reference implementation map.

This module is intentionally semantic, not operational. It defines the target
shape for a reversible text-to-graph capability whose operations are callable
identically by the GUI and by an agent.

The reference has two separable values. Its capability value is reversible
ingest, evidence-span integrity, additive graph projection, evidence-bag query,
and verbatim reconstruction. Its architectural value, and the reason it was
reviewed before the Tool Command Surface Framework, is that it already solves
single-implementation multi-transport dispatch and states the anti-drift rule in
writing.

Envelope conflict rule:
Useful Helpers already has 91 tools under `tools/` with an incompatible envelope
and a stronger safety layer. This adapter records the conflict; it does not
resolve it. Resolution belongs to Root Tranche 15.

Temporary reference rule:
The parts-bin locators below are implementation review anchors only. When the
manifold-mcp tool no longer depends on the reference app for design recovery,
runtime modules must not import from, read from, or require the parts bin.
"""

from __future__ import annotations

from useful_helpers.tools.contracts import ReferenceLocator, ToolCapability, ToolContract


TOOL_KEY = "manifold_mcp"
TOOL_LABEL = "Manifold MCP"
STATUS = (
    "contract reviewed; implementation pending; agent-transport prior art; "
    "envelope conflicts with the existing tools/ convention"
)

SOURCE_REFERENCE = "_PARTS-FOR-PLANS/_manifold-mcp/"
REFERENCE_APP_PATH = f"{SOURCE_REFERENCE}mcp_server.py"
REFERENCE_COMMON_PATH = f"{SOURCE_REFERENCE}common.py"
REFERENCE_CONTRACT_PATH = f"{SOURCE_REFERENCE}CONTRACT.md"
REFERENCE_INGEST_PATH = f"{SOURCE_REFERENCE}tools/manifold_ingest.py"
REFERENCE_STORE_PATH = f"{SOURCE_REFERENCE}lib/manifold_store.py"
REFERENCE_SDK_PATH = f"{SOURCE_REFERENCE}sdk/evidence_package.py"

REFERENCE_RETIREMENT_RULE = (
    "Parts-bin references are temporary review anchors. Once each manifold-mcp "
    "capability is re-homed into Useful Helpers runtime modules, remove "
    "parts-bin references from runtime tool code and keep historical provenance "
    "in docs only."
)

SINGLE_IMPLEMENTATION_RULE = (
    "A tool has exactly one implementation. The GUI path and the agent path call "
    "the same run(arguments) function through different transports, and the "
    "agent-visible input schema is generated from the same metadata the CLI "
    "validates against. Behavior must not fork between transports."
)

PATH_CONTAINMENT_RULE = (
    "No ingest, query, extract, or store operation may read or write outside an "
    "approved root. Paths must be resolved, checked for containment against an "
    "explicit approved root, and rejected with a clear reason when outside. "
    "Relative paths must resolve against an explicitly supplied root rather than "
    "a path depth inferred from the module's own location."
)

ENVELOPE_CONFLICT_RULE = (
    "Useful Helpers already has 91 tools under tools/ using an {'ok': bool} "
    "envelope with tool.json metadata, path containment, confirmation gating, "
    "and an authority model. The reference uses an incompatible "
    "{'status','tool','input','result'} envelope with in-module metadata and no "
    "safety layer, but supplies the MCP transport the existing tools lack. "
    "Root Tranche 15 must settle on one envelope; adopting either wholesale "
    "without the other side's strengths would be a regression."
)

REVERSIBILITY_RULE = (
    "Evidence spans are the irreversible source of truth. Graph structure is "
    "additive and never replaces or mutates evidence text, every inference "
    "stays traceable to evidence spans, and every evidence bag remains "
    "self-sufficient for verbatim extraction."
)

DONE_STATE = (
    "manifold-mcp integration is complete when Useful Helpers can ingest inline "
    "text and approved local files into a reversible corpus with exact evidence "
    "spans; can build additive graph structure that never replaces or mutates "
    "evidence text; can query a corpus and return an evidence bag with traceable "
    "provenance; can reconstruct verbatim source text from a bag; can enforce "
    "path containment on every file read and store write; can expose the same "
    "operations to the GUI and to an agent through one implementation and one "
    "authority check; can scope corpus stores to approved side-car output roots; "
    "and can do all of that with no runtime dependency on the parts bin."
)

REFERENCE_FRAILTIES = (
    "lib/manifold_store.py accepts arbitrary files[] entries and uses absolute paths as given with no containment check, so an agent calling manifold_ingest over MCP can read any file the process can read.",
    "tools/manifold_ingest.py derives repo_root from Path(__file__).resolve().parents[3], a hardcoded path-depth assumption that silently resolves elsewhere if the folder is relocated, which its own VENDORING.md encourages.",
    "store_dir is caller-supplied and unvalidated, so writes can land anywhere.",
    "mcp_server.py returns traceback.format_exc() to the client, disclosing internal paths and structure over the transport.",
    "mcp_server.py frames messages with Content-Length headers, which is LSP framing; MCP stdio uses newline-delimited JSON, so the server is unlikely to interoperate with a real MCP client without a transport rewrite.",
    "protocolVersion is pinned to 2024-11-05.",
    "Only initialize, ping, tools/list, and tools/call are implemented; there is no pagination, no resource or prompt capability, and no graceful shutdown handling.",
    "CONTRACT.md acknowledges the first version reads a whole corpus bundle with no index and no partial load, so memory scales with corpus size.",
    "The SDK and the MCP tools are two entry paths over the same store with no shared locking, so concurrent use is unguarded.",
    "There is no authority or permission model; every tool is equally callable.",
    "There is no confirmation gate on any mutating operation.",
)


def locator(label: str, symbol: str, line: int, purpose: str, path: str = REFERENCE_APP_PATH) -> ReferenceLocator:
    return ReferenceLocator(label, symbol, line, purpose, path)


LOC_MCP_DOCTRINE = locator("anti-drift doctrine", "Do not fork behavior between MCP and CLI paths", 32, "States in writing that MCP and CLI must share one implementation.", REFERENCE_CONTRACT_PATH)
LOC_TOOL_CONTRACT = locator("standard tool contract", "Standard Tool Contract", 15, "Requires FILE_METADATA, run(arguments), metadata, input-json, input-file, and a stable envelope per tool.", REFERENCE_CONTRACT_PATH)
LOC_REVERSIBLE_DATA = locator("reversible data contract", "Reversible Data Contract", 34, "Names the explicit record types: documents, evidence_spans, nodes, hyperedges, bags.", REFERENCE_CONTRACT_PATH)
LOC_ADAPTER_CONTRACT = locator("thin adapter contract", "Thin Adapter Contract", 44, "Defines the app-agnostic SDK surface and minimum reversible fields.", REFERENCE_CONTRACT_PATH)

LOC_ENVELOPE = locator("result envelope", "def tool_result", 24, "Defines the status/tool/input/result envelope that conflicts with the tools/ ok-envelope.", REFERENCE_COMMON_PATH)
LOC_LOAD_INPUT = locator("input loading", "def load_input", 37, "Accepts --input-json or --input-file and requires a JSON object.", REFERENCE_COMMON_PATH)
LOC_PARSER = locator("standard cli", "def build_standard_parser", 51, "Gives every tool the same metadata/run command surface.", REFERENCE_COMMON_PATH)
LOC_STANDARD_MAIN = locator("shared entry", "def standard_main", 79, "Single shared CLI entry point wrapping metadata and run.", REFERENCE_COMMON_PATH)

LOC_TOOL_REGISTRY = locator("tool registry", "TOOL_REGISTRY = {", 36, "Builds the agent-visible registry from the same FILE_METADATA the CLI uses.")
LOC_TOOL_LIST = locator("schema generation", "def _tool_list", 51, "Generates the agent-visible tool list and input schema from tool metadata.")
LOC_CALL_TOOL = locator("transport dispatch", "def _call_tool", 62, "Dispatches tools/call directly into the same run() the CLI calls.")
LOC_TRACEBACK = locator("traceback disclosure", "traceback.format_exc()", 76, "Returns internal traceback text to the client over the transport.")
LOC_FRAMING = locator("message framing", "content-length", 92, "Uses LSP-style Content-Length framing rather than MCP newline-delimited JSON.")
LOC_PROTOCOL = locator("protocol version", "2024-11-05", 120, "Pins an old MCP protocol version.")
LOC_HANDLE = locator("method dispatch", "def _handle_request", 106, "Implements only initialize, ping, tools/list, and tools/call.")

LOC_METADATA = locator("tool metadata", "FILE_METADATA = {", 30, "Declares tool_name, mcp_name, category, summary, and JSON Schema input_schema.", REFERENCE_INGEST_PATH)
LOC_RUN = locator("tool run", "def run(arguments: dict)", 50, "The single implementation both transports call.", REFERENCE_INGEST_PATH)
LOC_REPO_ROOT = locator("fragile root", "parents[3]", 51, "Derives the repo root from a hardcoded path depth that breaks on relocation.", REFERENCE_INGEST_PATH)

LOC_LOAD_TEXT = locator("uncontained file read", "def load_text_inputs", 80, "Reads caller-supplied file paths with no containment check.", REFERENCE_STORE_PATH)
LOC_ABS_PATH = locator("absolute path passthrough", "if not path.is_absolute()", 101, "Uses absolute paths as given and resolves relative paths against an inferred root.", REFERENCE_STORE_PATH)

LOC_SDK = locator("thin adapter", "class EvidencePackage", 35, "In-process object API offering set_goal, ingest_turn, window, reconstruct, and close.", REFERENCE_SDK_PATH)
LOC_SDK_WINDOW = locator("budgeted window", "def window", 90, "Produces a token-budgeted evidence bag for a query.", REFERENCE_SDK_PATH)
LOC_SDK_RECONSTRUCT = locator("reconstruction", "def reconstruct", 125, "Rebuilds verbatim text from an evidence bag.", REFERENCE_SDK_PATH)


CAPABILITIES = (
    ToolCapability(
        key="reversible_ingest",
        label="Reversible Ingest",
        target_outcome="Ingest inline text and approved local files into a corpus of exact, addressable evidence spans.",
        expected_inputs=("corpus id", "approved store root", "inline texts", "approved file paths"),
        expected_outputs=("corpus bundle", "document records", "evidence span records", "ingest counts"),
        reference_locators=(LOC_RUN, LOC_METADATA, LOC_LOAD_TEXT, LOC_REVERSIBLE_DATA),
        done_when="Ingested text can be recovered verbatim from its evidence spans, and every read path was containment-checked first.",
        implementation_owner="useful_helpers.tools.manifold_mcp ingest module",
    ),
    ToolCapability(
        key="evidence_span_integrity",
        label="Evidence Span Integrity",
        target_outcome="Treat evidence spans as the irreversible source of truth, with stable identifiers and exact offsets.",
        expected_inputs=("document text", "span boundaries", "span identifiers"),
        expected_outputs=("span records", "offset integrity checks", "identifier stability guarantees"),
        reference_locators=(LOC_REVERSIBLE_DATA, LOC_ADAPTER_CONTRACT, LOC_LOAD_TEXT),
        done_when=REVERSIBILITY_RULE,
        implementation_owner="useful_helpers.tools.manifold_mcp evidence module",
    ),
    ToolCapability(
        key="additive_graph_projection",
        label="Additive Graph Projection",
        target_outcome="Build nodes and hyperedges over evidence spans without replacing, rewriting, or discarding the underlying text.",
        expected_inputs=("evidence spans", "projection rules"),
        expected_outputs=("node records", "hyperedge records", "span linkage"),
        reference_locators=(LOC_REVERSIBLE_DATA, LOC_ADAPTER_CONTRACT),
        done_when="Graph structure is purely additive and every inference remains traceable back to specific evidence spans.",
        implementation_owner="useful_helpers.tools.manifold_mcp graph module",
    ),
    ToolCapability(
        key="evidence_bag_query",
        label="Evidence Bag Query",
        target_outcome="Query a corpus and return a self-sufficient evidence bag with provenance and an optional token budget.",
        expected_inputs=("corpus id", "query", "result limit", "token budget"),
        expected_outputs=("evidence bag", "matched spans", "provenance", "budget accounting"),
        reference_locators=(LOC_SDK_WINDOW, LOC_REVERSIBLE_DATA),
        done_when="A returned bag contains everything needed to reconstruct its supporting text without re-reading the corpus.",
        implementation_owner="useful_helpers.tools.manifold_mcp query module",
    ),
    ToolCapability(
        key="verbatim_reconstruction",
        label="Verbatim Reconstruction",
        target_outcome="Rebuild exact source text from an evidence bag, with no paraphrase, reflow, or lossy compression.",
        expected_inputs=("evidence bag", "reconstruction options"),
        expected_outputs=("verbatim text", "span ordering", "fidelity report"),
        reference_locators=(LOC_SDK_RECONSTRUCT, LOC_REVERSIBLE_DATA),
        done_when="Reconstructed output is byte-identical to the ingested source for the spans in the bag.",
        implementation_owner="useful_helpers.tools.manifold_mcp extract module",
    ),
    ToolCapability(
        key="contained_path_resolution",
        label="Contained Path Resolution",
        target_outcome="Resolve and containment-check every file read and store write against an explicit approved root.",
        expected_inputs=("raw path", "approved roots", "operation kind"),
        expected_outputs=("resolved path", "containment verdict", "rejection reason"),
        reference_locators=(LOC_LOAD_TEXT, LOC_ABS_PATH, LOC_REPO_ROOT),
        done_when=PATH_CONTAINMENT_RULE,
        implementation_owner="useful_helpers.tools.manifold_mcp path module",
    ),
    ToolCapability(
        key="single_implementation_dispatch",
        label="Single Implementation Dispatch",
        target_outcome="Give each operation exactly one implementation that the GUI and an agent both call, with the agent-visible schema generated from the same metadata the GUI validates against.",
        expected_inputs=("tool metadata", "input schema", "arguments", "calling client"),
        expected_outputs=("uniform result envelope", "generated tool list", "attributed invocation record"),
        reference_locators=(LOC_MCP_DOCTRINE, LOC_TOOL_CONTRACT, LOC_STANDARD_MAIN, LOC_TOOL_REGISTRY, LOC_TOOL_LIST, LOC_CALL_TOOL),
        done_when=SINGLE_IMPLEMENTATION_RULE,
        implementation_owner="Root Tranche 15 Tool Command Surface Framework",
    ),
    ToolCapability(
        key="agent_transport_adapter",
        label="Agent Transport Adapter",
        target_outcome="Expose tools to an agent over a correct transport without duplicating tool logic, and without leaking internal diagnostics to the client.",
        expected_inputs=("tool registry", "transport request", "client identity"),
        expected_outputs=("transport response", "safe error payload", "capability advertisement"),
        reference_locators=(LOC_HANDLE, LOC_FRAMING, LOC_PROTOCOL, LOC_TRACEBACK, LOC_CALL_TOOL),
        done_when="The transport is protocol-correct, advertises capabilities honestly, and returns actionable errors without internal tracebacks.",
        implementation_owner="Root Tranche 15 plus useful_helpers.tools.manifold_mcp transport module",
    ),
    ToolCapability(
        key="corpus_store_scoping",
        label="Corpus Store Scoping",
        target_outcome="Keep corpus stores, bags, and extraction outputs inside approved side-car output roots, discoverable and removable from the UI.",
        expected_inputs=("store root", "corpus id", "retention policy"),
        expected_outputs=("scoped store path", "artifact inventory", "cleanup result"),
        reference_locators=(LOC_ENVELOPE, LOC_LOAD_INPUT, LOC_PARSER, LOC_ABS_PATH),
        done_when="Every produced artifact is inside an approved root, listed in the UI, and removable without affecting the target project.",
        implementation_owner="useful_helpers.tools.manifold_mcp store module",
    ),
)


MANIFOLD_MCP_CONTRACT = ToolContract(
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
    """Return the semantic integration contract for the manifold-mcp tool."""

    return MANIFOLD_MCP_CONTRACT


def list_capabilities() -> tuple[ToolCapability, ...]:
    """Return all manifold-mcp capabilities currently planned for re-homing."""

    return MANIFOLD_MCP_CONTRACT.capabilities


def single_implementation_notice() -> str:
    """Return the anti-drift rule governing GUI and agent access to one tool."""

    return SINGLE_IMPLEMENTATION_RULE


def path_containment_notice() -> str:
    """Return the rule governing every file read and store write."""

    return PATH_CONTAINMENT_RULE


def envelope_conflict_notice() -> str:
    """Return the recorded, unresolved envelope conflict for Root Tranche 15."""

    return ENVELOPE_CONFLICT_RULE


def reversibility_notice() -> str:
    """Return the rule that keeps evidence spans authoritative and graph structure additive."""

    return REVERSIBILITY_RULE


def has_temporary_reference_locators() -> bool:
    """Return True while runtime tool code still carries parts-bin anchors."""

    return bool(MANIFOLD_MCP_CONTRACT.reference_app_path)


def reference_dependency_notice() -> str:
    """Return the rule that governs when reference locators must be retired."""

    return MANIFOLD_MCP_CONTRACT.reference_retirement_rule
