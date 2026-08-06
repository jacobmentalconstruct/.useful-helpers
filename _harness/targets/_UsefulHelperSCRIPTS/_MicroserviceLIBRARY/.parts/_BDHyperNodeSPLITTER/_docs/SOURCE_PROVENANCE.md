# Source Provenance — _BDHyperNodeSPLITTER

_Per Builder Constraint Contract §6.9 — provenance shall be recorded when logic is extracted, transplanted, or materially informed by reference sources._

---

## Provenance Table

| Destination | Source | Relationship | Reason | Treatment |
|---|---|---|---|---|
| `src/core/engines/treesitter_eng.py` | `_BDHyperNodeSPLITTER/src/engines/treesitter_eng.py` | Rewrite with v1 as reference | Two-pass emission pattern, recursive `_walk()`, sibling threading — correct structure hard to derive without reference; v1 had 5 known bugs that required careful v2 fixes | Full rewrite; v1 bugs fixed (_PARSER_CACHE, decorators, docstrings, base_classes, import_context); surface model added; v2 docstrings |
| `src/core/engines/peg_eng.py` | `_BDHyperNodeSPLITTER/src/engines/peg_eng.py` | Rewrite with v1 as reference | 4-layer pipeline (ledger→containers→leaf parsers→emit) — correct layer sequencing required reference; v1 discarded heading text | Full rewrite; heading_trail TEXT fix; cross_refs extraction added; nested structural path; surface model added |
| `src/core/engines/fallback_eng.py` | `_BDHyperNodeSPLITTER/src/engines/fallback_eng.py` | Rewrite informed by v1 | Blank-line paragraph splitter pattern — reference used to preserve v1 split semantics; sub_split() responsibility moved to Negotiator | Rewritten; sub_split removed (Negotiator owns it); v2 surface fields added (document_position, sibling_count, split_reason) |
| `src/core/negotiator.py` | `_BDHyperNodeSPLITTER/src/contract/negotiator.py` | Rewrite informed by v1 | Token budget enforcement pattern — algorithm informed by v1; v2 changes slicing from character-count to token-budget and adds context_window | Rewritten; character→token budget; context_window populated; DAG lineage on sub-split fragments; v2 field inheritance |
| `src/core/contract/hyperhunk.py` | `final/contract/hyperhunk.py` | Local owned copy derived from shared contract | Shared wire format is still designed in `final/contract/`, but the Splitter now carries its own runtime copy | Inlined locally during `/final` cleanup; no runtime dependency on `final/contract/` |
| `src/core/contract/token_budget.py` | `final/contract/token_budget.py` | Local owned copy derived from shared contract | Same ownership pattern as hyperhunk.py | Inlined locally during `/final` cleanup |

---

## What Was Original (no v1 reference)

| File | Notes |
|---|---|
| `src/core/splitter.py` | Completely original — parallel dispatch architecture did not exist in v1. v1 used a cascade (first-match-wins). v2 coordinator dispatches all capable engines and merges surfaces. |
| `src/app.py` | Original CLI implementation (stream + info commands). |
| `src/__main__.py` | Original entry point. |

---

## Why Rewriting From Reference Was Necessary (§1 and §6.7 borrowing conditions)

**TreeSitter engine:**
- The two-pass emission strategy (preamble flush + definition walk) and the recursive `_walk()` with structural_path threading are non-trivial to derive without reference. V1 had 5 documented bugs: missing parser cache (performance), lost decorators, lost scope names, lost docstrings, lost base classes. Fixing these while preserving the core traversal structure required the v1 reference as the base to correct from.

**PEG engine:**
- The 4-layer pipeline (Line Ledger → Block Resolution → Leaf Parsers → Emission) is a specific architectural choice. The correct state machine for fenced code, blockquotes, tables, and lists interacting with blank-line rules required the v1 reference as the starting point. The heading_trail TEXT bug was a v1 regression being fixed.

**Fallback + Negotiator:**
- These are informed rewrites, not transplants. The v1 reference established the behavioral contract (what counts as a paragraph boundary, what the token budget enforcement looks like). The algorithms were rewritten with new domain boundaries.

---

## Compliance Adjustments Applied to All Rewrites

- All modules placed in `src/core/` under correct ownership per scaffold
- Internal imports use `core.contract.*` (not `final.contract.*`) — runnable and vendorable
- All v2 surface fields added (structural, grammatical, statistical surfaces)
- Module docstrings include `V1 reference:` line and bug-fix notes
- No `@HITL_PERMS` markers apply (no mathematical invariants in Splitter — that domain belongs to the Emitter)
- `print()` not present (these are new writes, logging used throughout)

---

## Contract Ownership Note

`src/core/contract/hyperhunk.py` and `token_budget.py` are now locally owned runtime copies derived from `final/contract/`. The shared `final/contract/` folder remains the design surface while the strangler build is still evolving:

> When vendoring, each component inlines its own copy of the contract into `src/core/contract/`. No runtime imports across component boundaries.
> — `final/` README and plan (`async-inventing-deer.md`)

The Splitter now satisfies that runtime boundary already. Future contract changes still need to be synchronized deliberately between the shared design surface and the component-local copy.
