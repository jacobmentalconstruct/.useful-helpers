# TheCELL Tool Contract

Date: 2026-08-03

Status: contract reviewed; implementation pending; lifecycle not final; DAC required.

## Source Boundary

Reference app reviewed:

`_PARTS-FOR-PLANS/_theCELL/`

The source folder is spelled `_theCELL` on disk. The Useful Helpers registry and
docs use the readable tool label `TheCELL`.

This reference is provenance only. Runtime Useful Helpers modules must not
import from or read from this parts-bin folder. Locators in this document and in
`src/useful_helpers/tools/the_cell/adapter.py` are temporary implementation
anchors and must be retired from runtime code once the behavior is re-homed.

## Primary Anchors

- `_PARTS-FOR-PLANS/_theCELL/README.md`
- `_PARTS-FOR-PLANS/_theCELL/src/app.py`
- `_PARTS-FOR-PLANS/_theCELL/src/backend.py`
- `_PARTS-FOR-PLANS/_theCELL/src/ui.py`
- `_PARTS-FOR-PLANS/_theCELL/src/cell_identity.py`
- `_PARTS-FOR-PLANS/_theCELL/src/microservices/_SignalBusMS.py`
- `_PARTS-FOR-PLANS/_theCELL/src/microservices/_SessionManagerMS.py`
- `_PARTS-FOR-PLANS/_theCELL/src/microservices/_TkinterAppShellMS.py`
- `_PARTS-FOR-PLANS/_theCELL/_workflows/feature_developer.json`
- `_PARTS-FOR-PLANS/_theCELL/requirements.txt`

## Required Lifecycle Repair

The reference lifecycle is not final. It is recursively shaped:

- README anchor: `A recursive, multi-window Tkinter workspace`
- README anchor: `Spawn child cells`
- README anchor: `Route/push content to another live cell`
- signal anchor: `SIGNAL_SPAWN_REQUESTED`
- signal anchor: `SIGNAL_PUSH_DATA`
- shell anchor: `def spawn_window`
- queue anchor: `def _on_task_done`

Useful Helpers must not accept this recursive lifecycle. The target lifecycle is
DAC shaped:

1. Discover source/context.
2. Act through one bounded forward step.
3. Capture outputs, evidence, metadata, and user decisions.
4. Advance only to the next declared step.

No child-cell recursion, backward loop, implicit inherited-context injection, or
hidden cross-cell push path may be part of the final TheCELL integration.

## Target Done State

TheCELL integration is done when Useful Helpers exposes a forward-only DAC
workflow surface for agent-assisted project work.

The complete state requires:

- explorer-selected context can be discovered or ingested,
- a declared workflow step can act against bounded context,
- streamed output is captured as an artifact with metadata,
- HITL review is available before writes or follow-on actions,
- prior outputs are explicit captured evidence, not hidden inherited prompt text,
- workflow templates can be stored and loaded through Useful Helpers-owned state,
- optional vector/RAG support is dependency-gated and can be unavailable without
  breaking the base workbench,
- session state stays under the side-car state policy,
- no parts-bin runtime dependency remains.

## Capabilities To Re-Home

### `bootstrap_single_cell_workspace`

Create an optional TheCELL-inspired workspace inside Useful Helpers without
replacing the explorer-first front door.

Search anchors:

- `rg -n "def main" "_PARTS-FOR-PLANS/_theCELL/src/app.py"`
- `rg -n "class Backend" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "class CELL_UI" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`
- `rg -n "def _setup_main_window" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`

### `enforce_forward_only_dac_lifecycle`

Replace recursive spawn/push/inherited-context behavior with explicit Discover,
Act, Capture steps.

Search anchors:

- `rg -n "A recursive, multi-window Tkinter workspace" "_PARTS-FOR-PLANS/_theCELL/README.md"`
- `rg -n "Spawn child cells" "_PARTS-FOR-PLANS/_theCELL/README.md"`
- `rg -n "Route/push content to another live cell" "_PARTS-FOR-PLANS/_theCELL/README.md"`
- `rg -n "SIGNAL_SPAWN_REQUESTED" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SignalBusMS.py"`
- `rg -n "SIGNAL_PUSH_DATA" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SignalBusMS.py"`
- `rg -n "def spawn_window" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_TkinterAppShellMS.py"`

### `manage_cell_identity_and_state`

Preserve useful identity/session concepts without creating parent/child cell
trees.

Search anchors:

- `rg -n "class CellIdentity" "_PARTS-FOR-PLANS/_theCELL/src/cell_identity.py"`
- `rg -n "class SessionManagerMS" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SessionManagerMS.py"`

### `persist_personas_prompts_and_templates`

Provide local repositories for roles, system prompts, task prompts, personas,
and DAC workflow templates.

Search anchors:

- `rg -n "CREATE TABLE IF NOT EXISTS personas" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "\"tasks\"" "_PARTS-FOR-PLANS/_theCELL/_workflows/feature_developer.json"`
- `rg -n "def _on_load_workflow" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`

### `run_streamed_agent_step`

Run one bounded DAC Act step with streaming output and structured artifact
metadata.

Search anchors:

- `rg -n "def process_submission" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "class SignalBusMS" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SignalBusMS.py"`

### `execute_declared_task_queue`

Load, edit, validate, and run ordered workflow steps.

Search anchors:

- `rg -n "def run_queue" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "def _start_task" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "def _on_task_done" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "self.btn_load_workflow" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`

### `ingest_context_for_retrieval`

Optionally ingest selected files/folders into a retrieval store.

Search anchors:

- `rg -n "def ingest_file" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "def ingest_directory" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "faiss-cpu" "_PARTS-FOR-PLANS/_theCELL/requirements.txt"`
- `rg -n "chromadb" "_PARTS-FOR-PLANS/_theCELL/requirements.txt"`

### `surface_signal_bus_events`

Expose workflow progress, logs, errors, and UI-safe updates through local event
contracts.

Search anchor:

- `rg -n "class SignalBusMS" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SignalBusMS.py"`

### `capture_outputs_feedback_and_exports`

Capture generated artifacts, HITL decisions, export routing, and evidence
records.

Search anchors:

- `rg -n "def export_artifact" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "def record_feedback" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`
- `rg -n "class SessionManagerMS" "_PARTS-FOR-PLANS/_theCELL/src/microservices/_SessionManagerMS.py"`

### `replace_ontological_steps_with_captured_evidence`

Convert prompt-stacked ontological steps into explicit captured evidence objects.

Search anchors:

- `rg -n "def add_onto_step" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`
- `rg -n "def _serialize_onto_steps" "_PARTS-FOR-PLANS/_theCELL/src/ui.py"`
- `rg -n "inherited_context" "_PARTS-FOR-PLANS/_theCELL/src/backend.py"`

## Reference Frailties

- Recursive multi-window lifecycle must be replaced with forward-only DAC.
- Cross-cell push routing and loop guards are not accepted final architecture.
- Prior task output must become explicit captured evidence, not silent inherited
  prompt context.
- Checked-in `_sessions/` state is provenance only.
- `chromadb`, `faiss-cpu`, and `numpy` must remain optional until a later
  tranche accepts vector/RAG support.
- The dense Tk prompt/queue/RAG/HITL/export surface needs Useful Helpers-native
  layout design before implementation acceptance.

## Parked State

TheCELL is scaffolded as a reviewed semantic contract. Implementation is
pending, and the lifecycle is explicitly blocked from final acceptance until it
is redesigned as forward-only DAC.
