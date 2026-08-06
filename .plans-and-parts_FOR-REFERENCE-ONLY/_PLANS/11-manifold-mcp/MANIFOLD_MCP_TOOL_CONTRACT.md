# manifold-mcp Tool Contract

Status: contract reviewed; implementation pending; primary value is agent-transport
prior art, and its envelope conflicts with the existing `tools/` convention

Reference app:
`_PARTS-FOR-PLANS/_manifold-mcp/`

- `CONTRACT.md`: written builder pledge and tool/MCP/data contracts.
- `common.py` (101 lines): shared envelope, CLI parser, `standard_main`.
- `mcp_server.py` (147 lines): stdio MCP server and tool dispatch.
- `tool_manifest.json`: mechanical contract and vendoring declaration.
- `tools/manifold_ingest.py`, `manifold_query.py`, `manifold_extract.py`.
- `lib/manifold_store.py` (380 lines): reversible corpus store.
- `sdk/evidence_package.py` (205 lines): thin in-process adapter.

Runtime contract surface:
`src/useful_helpers/tools/manifold_mcp/adapter.py`

## Intent

This reference serves two distinct purposes, and the contract keeps them
separate.

**Primary purpose: agent-transport prior art.** `_manifold-mcp` is the only
reference in the parts bin that solves the problem Root Tranche 15 exists to
solve. It defines one tool entry point callable identically from a CLI and from
an agent over MCP, and it states the anti-drift rule explicitly. That design is
the reason this app was reviewed before Root Tranche 15.

**Secondary purpose: a reversible text-to-graph capability.** Ingest text into
exact evidence spans, build additive graph structure over those spans, query to
produce an evidence bag, and reconstruct verbatim source text from that bag.
This is genuinely useful for the workbench, but it is not why the review was
prioritized.

## The Rule Worth Adopting

From `CONTRACT.md`:

> MCP is the primary operation path for agents.
> MCP must call the same `run(arguments)` logic as CLI execution.
> Do not fork behavior between MCP and CLI paths.

This is the same requirement the MonacoVIEWER contract states as
`SHARED_SESSION_RULE`, arrived at independently. Two references converging on it
is strong evidence it belongs in the Root Tranche 15 framework rather than in
any single tool.

The mechanism is small and worth copying in shape:

- each tool exports `FILE_METADATA` (including a JSON Schema `input_schema` and
  a stable `mcp_name`) and a single `run(arguments: dict) -> dict`,
- `standard_main` in `common.py` gives every tool the same CLI surface:
  `metadata`, `run --input-json`, `run --input-file`,
- `mcp_server.py` builds `TOOL_REGISTRY` from the same `FILE_METADATA` and
  dispatches `tools/call` straight into the same `run()`,
- `tools/list` is generated from `input_schema`, so the agent-visible schema
  cannot drift from the CLI's accepted input.

There is exactly one implementation per tool. The transport is the only
variable.

## Envelope Conflict

RECORDED, NOT RESOLVED. This is a Root Tranche 15 decision, not a 14G decision.

Useful Helpers already has 91 tools under `tools/` with their own mature
convention, and the two envelope shapes are incompatible:

| Concern | `tools/_toolkit.py` (in repo) | `_manifold-mcp/common.py` |
| --- | --- | --- |
| Success shape | `{"ok": true, ...}` | `{"status": "ok", "tool", "input", "result"}` |
| Error shape | `{"ok": false, "error": ...}` | `{"status": "error", ...}` |
| CLI flag | `--args-json` | `--input-json` / `--input-file` |
| Metadata | `tool.json` sidecar | `FILE_METADATA` in module |
| Agent transport | none | MCP stdio |

Each side has what the other lacks. `tools/_toolkit.py` is stronger on safety:
it has `resolve_within_roots` and `_is_within` path containment, `confirmed()`
and `apply_with()` confirmation gating, scoped `project_root()`,
`output_root()`, and `state_root()`, plus `attach_evidence()`. Its `tool.json`
also carries an `authority` field (`Observe`, `Apply`, `Sandbox`) and an
`operates_on` field (`project`, `toolkit`) that together form a real permission
model.

`_manifold-mcp` has none of that safety layer, but it has the MCP server and
the written anti-drift doctrine that `tools/` lacks entirely.

The synthesis Root Tranche 15 should reach: keep the `tools/` safety and
authority model, adopt the manifold single-`run()`-plus-transport-adapter shape,
and settle on one envelope. Adopting either envelope wholesale without the other
side's strengths would be a regression.

## Required Stop State

The tool is complete when Useful Helpers can:

- ingest inline text and approved local files into a reversible corpus with
  exact evidence spans,
- build additive graph structure that never replaces or mutates evidence text,
- query a corpus and return an evidence bag with traceable provenance,
- reconstruct verbatim source text from an evidence bag,
- enforce path containment on every file read and store write, which the
  reference does not do,
- expose the same operations to the GUI and to an agent through one
  implementation and one authority check,
- scope corpus stores to approved side-car output roots,
- do all of this from local Useful Helpers modules with no runtime dependency on
  the parts bin.

## Capabilities

- `reversible_ingest`
- `evidence_span_integrity`
- `additive_graph_projection`
- `evidence_bag_query`
- `verbatim_reconstruction`
- `contained_path_resolution`
- `single_implementation_dispatch`
- `agent_transport_adapter`
- `corpus_store_scoping`

## Path Containment Rule

No ingest, query, extract, or store operation may read or write outside an
approved root. The path must be resolved, checked for containment against an
explicit approved root, and rejected with a clear reason when outside. Relative
paths must resolve against an explicitly supplied root rather than a path depth
inferred from the module's own location.

This rule exists because the reference violates all of it. See frailties.

## Reference Frailties

Security and containment:

- `lib/manifold_store.py:99` accepts arbitrary entries in `files[]`. Absolute
  paths are used as given with no containment check, so an agent calling
  `manifold_ingest` over MCP can read any file the process can read.
- `tools/manifold_ingest.py:51` derives `repo_root` from
  `Path(__file__).resolve().parents[3]`, a hardcoded path-depth assumption. It
  silently resolves to a different root if the folder is relocated, which the
  project's own `VENDORING.md` actively encourages.
- `store_dir` is caller-supplied and unvalidated, so writes can land anywhere.
- `mcp_server.py:76` returns `traceback.format_exc()` to the client, disclosing
  internal paths and structure to whatever is on the other end of the transport.

Protocol correctness:

- `mcp_server.py:81`-`:103` frames messages with `Content-Length` headers. That
  is LSP framing. MCP stdio transport uses newline-delimited JSON, so this
  server is unlikely to interoperate with a real MCP client without a rewrite of
  the transport layer.
- `protocolVersion` is pinned to `2024-11-05` (`mcp_server.py:120`).
- `_handle_request` implements only `initialize`, `ping`, `tools/list`, and
  `tools/call`. There is no pagination, no resource or prompt capability, and no
  graceful shutdown handling.

Design and scale:

- `CONTRACT.md` acknowledges the first version reads a whole corpus bundle for
  simplicity. There is no index and no partial load, so memory scales with
  corpus size.
- `sdk/evidence_package.py` and the MCP tools are two entry paths over the same
  store with no shared locking. Concurrent use is unguarded.
- No authority or permission model. Every tool is equally callable; there is no
  equivalent of the `tools/` `authority` field.
- No confirmation gate on any mutating operation.

## Non-Goals For This Contract Review

- no runtime implementation,
- no MCP server implementation,
- no transport selection or protocol repair,
- no envelope decision, which belongs to Root Tranche 15,
- no changes to the existing 91 tools under `tools/`,
- no corpus store implementation,
- no import/read dependency on the parts bin.
