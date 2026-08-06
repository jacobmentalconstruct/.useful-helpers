# 0021 - WASM Inference Wrapper Contract Scaffold

Date: 2026-08-04

## Tranche

Root Tranche 14D: WASM Inference Wrapper Contract Scaffold.

Goal: scaffold a Useful Helpers tool contract that fulfills the intended purpose of packaging a local agent in a WASM-shaped deployment wrapper, using `_WasmInferenceWRAPPER` only as reference evidence.

Expected completion point:

- reference folder is inspected,
- target intent is recorded separately from reference implementation shape,
- contract adapter is created,
- registry exposes the tool as pending,
- tests pin capabilities, safety gates, and frailties,
- docs record the scaffold and non-goals.

Non-goals held:

- no runtime implementation,
- no model download,
- no dependency install,
- no venv creation,
- no process start/stop/kill,
- no runtime dependency on the parts-bin installer.

## Initial Inspection

`_WasmInferenceWRAPPER` contains only `wrapper_installer.py`. It writes generated Python payloads for a FastAPI `llama-cpp-python` GGUF model server, run scripts, a Tk chat UI, a registry file, a kill-port helper, a venv, dependencies, and a model download.

Key finding: the reference name says WASM, but the implementation is not a WASM wrapper. It is still useful as a bootstrap-flow reference for local model-node packaging.

## Implementation

Added:

- `src/useful_helpers/tools/wasm_inference_wrapper/__init__.py`,
- `src/useful_helpers/tools/wasm_inference_wrapper/adapter.py`,
- `_docs/WASM_INFERENCE_WRAPPER_TOOL_CONTRACT.md`,
- `tests/test_wasm_inference_wrapper_adapter_contract.py`.

Updated registry and docs so the new tool appears as `WASM Inference Wrapper` with status `contract scaffolded; implementation pending; reference is not true WASM`.

The contract defines capabilities for manifest definition, runtime-boundary repair, install planning, artifact generation, model download gates, registry management, endpoint contract, safe process controls, and local test harness.

## Review Findings And Repairs

- Initial registry insertion did not land because of newline shape. Rewrote the registry tuple directly and reran focused tests.
- The reference has a likely llama.cpp response parsing bug and a dangerous generated force-kill helper; both are recorded as frailties.

## Verification

```bat
python -m pytest tests\test_wasm_inference_wrapper_adapter_contract.py -q -p no:cacheprovider
```

Result: `5 passed`.

Full verification is recorded in current state after final run.

## Residual Risks

- True WASM runtime strategy still needs architecture work.
- The reference is a Python fallback/bootstrapper, not an accepted final runtime.
- Future implementation will need explicit user confirmation for network, dependency, file-write, and process actions.

## Park Point

WASM Inference Wrapper Contract Scaffold is complete. The next recommended tranche remains Root Tranche 15: Tool Command Surface Framework unless another new reference-app scaffold is prioritized.