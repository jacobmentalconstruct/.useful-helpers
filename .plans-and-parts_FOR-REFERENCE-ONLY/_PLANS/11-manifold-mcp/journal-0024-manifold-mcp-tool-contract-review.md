# 0024 - manifold-mcp Tool Contract Review

Date: 2026-08-04

## Tranche

Root Tranche 14G: manifold-mcp Tool Contract Review.

Goal: review the second of the three previously-unreviewed parts-bin apps, and
extract the agent-transport prior art that should constrain Root Tranche 15.

Expected completion point:

- reference inspected in full,
- the reusable architectural rule identified and recorded,
- capability intent recorded separately from reference implementation shape,
- contract doc written,
- adapter scaffolded,
- registry exposes the tool as pending,
- tests pin capabilities, rules, and frailties.

Non-goals held:

- no runtime implementation,
- no MCP server implementation,
- no transport selection or protocol repair,
- no envelope decision, which belongs to Root Tranche 15,
- no changes to the existing 91 tools under `tools/`,
- no runtime dependency on the parts bin.

## Current State Before Work

`_manifold-mcp` was the second of three parts-bin apps never reviewed. It is
1,245 lines of Python across `common.py`, `mcp_server.py`, three tools, a store
library, an SDK, and a smoke test, plus four written contract/doc files. All of
it was read.

## Key Findings

**The reference already states the rule the project needs.** `CONTRACT.md:29-32`
says: "MCP is the primary operation path for agents. MCP must call the same
`run(arguments)` logic as CLI execution. Do not fork behavior between MCP and
CLI paths." This is the same requirement the MonacoVIEWER contract independently
arrived at as `SHARED_SESSION_RULE`. Two references converging on it is strong
evidence it belongs in the Root Tranche 15 framework rather than in any single
tool.

The mechanism is small and worth copying in shape: each tool exports
`FILE_METADATA` (with a JSON Schema `input_schema` and a stable `mcp_name`) plus
one `run(arguments) -> dict`; `standard_main` in `common.py` gives every tool the
same CLI; `mcp_server.py` builds its registry from the same `FILE_METADATA` and
dispatches `tools/call` straight into the same `run()`. The agent-visible schema
is generated from the metadata the CLI validates against, so the two cannot
drift. There is one implementation per tool and the transport is the only
variable.

**Useful Helpers already has a competing convention, and it is the stronger
one on safety.** The project's own `tools/` folder holds 91 tools with
`tool.json` manifests and a shared `_toolkit.py`. That toolkit has
`resolve_within_roots` and `_is_within` path containment, `confirmed()` and
`apply_with()` confirmation gating, scoped `project_root()`, `output_root()`,
and `state_root()`, and `attach_evidence()`. Its `tool.json` carries an
`authority` field (`Observe`, `Apply`, `Sandbox`) and an `operates_on` field
(`project`, `toolkit`) that together form a real permission model.

`_manifold-mcp` has none of that safety layer. But it has the MCP server and the
written anti-drift doctrine that `tools/` lacks entirely.

**The envelopes are incompatible.** `tools/_toolkit.py` uses `{"ok": bool, ...}`
with `--args-json` and a `tool.json` sidecar. `_manifold-mcp/common.py` uses
`{"status", "tool", "input", "result"}` with `--input-json` / `--input-file` and
in-module metadata. Each side has what the other lacks. This is recorded as an
open Root Tranche 15 decision, not resolved here.

**The reference is unsafe for agent use as written.** `lib/manifold_store.py:99`
accepts arbitrary `files[]` entries, uses absolute paths as given with no
containment check, and resolves relative paths against a `repo_root` derived
from `Path(__file__).resolve().parents[3]` — a hardcoded path-depth assumption
that silently resolves elsewhere if the folder is relocated, which its own
`VENDORING.md` actively encourages. An agent calling `manifold_ingest` over MCP
can read any file the process can read. `store_dir` is likewise unvalidated.

**The MCP transport is probably not MCP.** `mcp_server.py:81-103` frames
messages with `Content-Length` headers. That is LSP framing; MCP stdio uses
newline-delimited JSON. The server is unlikely to interoperate with a real MCP
client without a transport rewrite. `mcp_server.py:76` also returns
`traceback.format_exc()` to the client.

The architectural doctrine is the valuable part. The transport implementation is
not.

## Decisions

None required from the user in this tranche. The one decision this review
surfaced — which envelope Useful Helpers standardizes on — is explicitly
deferred to Root Tranche 15 and recorded as `ENVELOPE_CONFLICT_RULE` so it
cannot be settled by accident.

Recorded recommendation for that decision: keep the `tools/` safety and
authority model, adopt the manifold single-`run()`-plus-transport-adapter shape,
and settle on one envelope. Adopting either envelope wholesale without the other
side's strengths would be a regression.

## Implementation

Added:

- `_docs/MANIFOLD_MCP_TOOL_CONTRACT.md`,
- `src/useful_helpers/tools/manifold_mcp/__init__.py`,
- `src/useful_helpers/tools/manifold_mcp/adapter.py`,
- `tests/test_manifold_mcp_adapter_contract.py`.

Updated `src/useful_helpers/tools/registry.py` so the tool appears as
`Manifold MCP` with status `contract reviewed; implementation pending;
agent-transport prior art; envelope conflict open`.

The adapter defines nine capabilities: `reversible_ingest`,
`evidence_span_integrity`, `additive_graph_projection`, `evidence_bag_query`,
`verbatim_reconstruction`, `contained_path_resolution`,
`single_implementation_dispatch`, `agent_transport_adapter`, and
`corpus_store_scoping`. It carries 24 reference locators across `CONTRACT.md`,
`common.py`, `mcp_server.py`, `tools/manifold_ingest.py`,
`lib/manifold_store.py`, and `sdk/evidence_package.py`.

Two capabilities are deliberately owned by Root Tranche 15 rather than by this
tool: `single_implementation_dispatch` and `agent_transport_adapter`. They are
framework concerns that this reference happens to demonstrate, not manifold
features.

Four rules are stated as named constants and tested directly:
`SINGLE_IMPLEMENTATION_RULE`, `PATH_CONTAINMENT_RULE`, `ENVELOPE_CONFLICT_RULE`,
and `REVERSIBILITY_RULE`.

## Review Findings And Repairs

No repairs required. The tranche is additive; the only edit to existing runtime
code was the single registry tuple entry.

## Verification

Cross-platform partial run (Linux sandbox; no `tkinter`, so the three
Tk-importing modules were excluded):

```bash
python -m pytest -q -p no:cacheprovider \
  --ignore=tests/test_project_mapper_adapter_contract.py \
  --ignore=tests/test_project_mapper_backend.py \
  --ignore=tests/test_ui_theme_contract.py
```

Result: `2 failed, 93 passed`. The two failures are the known Windows-only
assertions recorded in journal 0022, unchanged by this tranche.

Focused run:

```bash
python -m pytest -q -p no:cacheprovider tests/test_manifold_mcp_adapter_contract.py
```

Result: `9 passed`.

Test function count is now 103 (94 after Tranche 14F, plus 9). Debris check
after the run: `_state/` contained only `evidence.sqlite3`.

Authoritative Windows verification: PENDING. Expected `103 passed`. Note that
neither 14F nor 14G has been confirmed on Windows yet; one run covers both.

## Residual Risks

- The envelope conflict is open and now blocks a clean Root Tranche 15 start.
  Two incompatible tool conventions exist in the project's orbit.
- The 91 tools under `tools/` have never been reviewed as a system. They were
  treated as project-local tooling, but they carry a mature contract that
  materially affects the Root Tranche 15 design. This is a coverage gap of the
  same kind as the parts-bin gap found in journal 0022, and it deserves its own
  review before or during Root Tranche 15.
- The reference MCP transport is probably non-conformant, so no code from
  `mcp_server.py` should be adopted without protocol verification against a
  real MCP client.
- Reversible corpus storage will produce artifacts that need a home under the
  unified output layer planned in Root Tranche 25.
- One parts-bin app remains unreviewed: `_TheDISMANTLER`.

## Park Point

Root Tranche 14G is complete pending the Windows verification run.

Next recommended action: Root Tranche 14H, TheDISMANTLER Tool Contract Review.
It supplies the third input to Root Tranche 15 — GUI-side tool dispatch via
`BaseTool` registration and `BackendEngine.execute_task()` — and it is the last
unreviewed parts-bin app. After that, Root Tranche 15 can be designed against
three real prior designs plus the existing `tools/` convention rather than
invented.
