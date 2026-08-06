# Journal 001 — Bootstrap

Date: 2026-03-26

## What happened

Scaffolded the v2 _BDHyperNodeSPLITTER inside the `final/` staging area.

This is Tranche 1: scaffold only. No implementation code yet.

## Why this exists

The v1 Splitter has three problems:

1. **Information loss** — The engines (TreeSitter, PEG, Fallback) collect rich
   structural context during parsing (scope names, heading breadcrumbs,
   decorators, docstrings, cross-references) but discard nearly all of it.
   Only `structural_path` survives as a type-path string. The actual names,
   docstrings, decorators, and heading text are gone by the time the Negotiator
   sees the hunk.

2. **Character-count budget** — The Negotiator uses `len(content) > max_size`
   (character count). The Emitter's embedding window is measured in BPE tokens.
   A 1000-char dense Python function and a 1000-char verbose English paragraph
   cost wildly different amounts. Splits happen at the wrong places.

3. **Hard cut edges** — There is zero overlap between hunks. Adjacent hunks
   have hard boundaries in the embedding space. The hot engine's topology
   state is noisier than it needs to be because context is cut exactly at
   hunk boundaries.

## What the v2 contract adds

See `final/contract/hyperhunk.py` for the full v2 schema.

Key new fields:
- `scope_stack` — full enclosing name chain (TreeSitter)
- `scope_docstrings` — docstrings of enclosing scopes (TreeSitter)
- `base_classes` — inherited class names (TreeSitter)
- `decorators` — decorator strings (TreeSitter)
- `import_context` — relevant import lines (TreeSitter)
- `heading_trail` — markdown heading breadcrumb (PEG)
- `cross_refs` — markdown link targets (PEG)
- `context_window` — last N BPE tokens of preceding hunk (Negotiator)
- `token_count` — BPE token count of content (Negotiator)
- `split_reason` — why this split happened (all engines + Negotiator)
- `document_position` — 0.0–1.0 position in source (all engines)
- `sibling_count` — total siblings at scope level (all engines)

## What was decided

- Suite model: kept. Components remain independently vendorable.
- `/final` staging area: created at suite root.
- Contract module: lives at `final/contract/` during development; re-homed into
  each component's `src/core/contract/` when vendored out.
- Builder constraint contract: copied into `_docs/` and governs all build decisions.
- Hash stability: v2 hash inputs are IDENTICAL to v1. New fields are additive context.
  v1 and v2 producers can coexist in the same cold_anatomy.db.

## Current state

Scaffold complete. Contract designed. No engine code yet.
Active tranche: Tranche 1 (scaffold). Complete when `app.py` runs without import errors.

## Next step

Tranche 2: Negotiator upgrade (token-aware, context_window population).
This should precede engine upgrades because it affects ALL hunks regardless of engine.
