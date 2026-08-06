# WASM Inference Wrapper Tool Contract

Status: contract scaffolded; implementation pending; reference is not true WASM

Reference app:
`_PARTS-FOR-PLANS/_WasmInferenceWRAPPER/wrapper_installer.py`

Runtime contract surface:
`src/useful_helpers/tools/wasm_inference_wrapper/adapter.py`

## Intent

The intended tool is a deployable local-agent wrapper with a WASM-shaped runtime
boundary. It should let Useful Helpers package or scaffold a local agent runtime,
show its manifest, model/runtime inputs, permissions, resource limits,
request/response contract, generated artifacts, install/build plan, local test
harness, and deployment handoff.

The parts-bin reference is useful only as bootstrap evidence. It currently
creates a Python FastAPI llama.cpp GGUF model node plus a Tk chat UI; it does not
produce a WASM module or a real WebAssembly deployment package.

## Required Stop State

The tool is complete when Useful Helpers can:

- define a local agent wrapper manifest,
- distinguish true WASM runtime work from Python fallback mode,
- preview all generated files, downloads, dependency installs, and process actions,
- scaffold wrapper/runtime artifacts into an approved side-car output folder,
- gate model downloads and dependency installation behind explicit confirmation,
- manage registry metadata without hidden stale state,
- expose a tested prompt generation request/response contract,
- provide safe local start/stop/test harness behavior,
- avoid any runtime dependency on the parts-bin reference installer.

## Capabilities

- `define_wasm_agent_manifest`
- `repair_runtime_boundary`
- `plan_local_agent_install`
- `generate_runtime_artifacts`
- `model_source_and_download_gate`
- `node_registry_management`
- `inference_endpoint_contract`
- `safe_process_controls`
- `local_test_harness`

## Reference Frailties

- The reference name says WASM, but the code generates a Python FastAPI `llama-cpp-python` server.
- The installer performs network model downloads and pip installs without a reusable dry-run plan.
- The generated process-kill helper can force-kill processes by port and must not be adopted blindly.
- The generated wrapper likely parses llama.cpp chat responses incorrectly and needs repair.
- Registry cleanup is ad hoc and can retain stale nodes.
- The default model URL is remote and requires explicit network consent.

## Non-Goals For Scaffold

- no runtime implementation,
- no model download,
- no dependency install,
- no venv creation,
- no process start/stop/kill,
- no import/read dependency on the parts bin.