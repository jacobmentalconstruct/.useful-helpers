# Journal 002 — Tranche 2: Negotiator Upgrade

Date: 2026-03-26

## Status: COMPLETE

## What was built

### TokenBudget (`final/contract/token_budget.py`)
- Phase 1 implementation: character-estimate proxy (len / chars_per_token)
- API: count(), fits(), headroom(), split_to_slices(), context_window_tokens()
- Phase 2 upgrade path documented: swap count() for real BPE call when vocab is trained
- Default calibration: 4.0 chars/token (conservative midpoint)

### FallbackEngine v2 (`src/core/engines/fallback_eng.py`)
- Re-implemented from scratch (not copied from v1)
- Adds: document_position, sibling_count, split_reason="paragraph_boundary"
- Removed: sub_split() — ownership moved to Negotiator where it belongs
- char_offset tracking for accurate document_position per paragraph

### Negotiator v2 (`src/core/negotiator.py`)
- Token-aware: budget.fits() replaces len(content) > max_size
- Stamps token_count on EVERY hunk passing through
- Stamps context_window on every hunk (empty for first, sliding tail thereafter)
- split_reason="token_budget" on sub-split fragments; engine reasons preserved on whole hunks
- Sub-split inherits ALL v2 scope/structure fields from oversized hunk
  (scope_stack, heading_trail, decorators, etc. carry into fragments)
- Owns sub-split logic directly (no longer delegates to FallbackEngine)

### Splitter coordinator (`src/core/splitter.py`)
- Re-implemented from scratch (not copied from v1)
- API: process(), process_file(), which_engine(), estimate_hunk_count()
- Passes max_tokens/overlap_ratio/chars_per_token through to Negotiator
- __pycache__, .git, .venv, node_modules excluded from directory walks
- FallbackEngine is the live path; TreeSitter + PEG are live shells (yield nothing)

### app.py (`src/app.py`)
- stream and info commands fully wired to splitter
- All diagnostic output to stderr; NDJSON to stdout

## Verified behavior (inline test)

Input: 4 paragraphs, max_tokens=30, overlap_ratio=0.25

Results:
  hunk[0] para 1: tokens=28, reason='paragraph_boundary', context_window="" ✓
  frag[0] para 2: tokens=30, reason='token_budget', context_window=<tail of para1> ✓
  frag[1] para 2: tokens=4,  reason='token_budget', context_window=<tail of frag0> ✓
  hunk[2] para 3: tokens=14, reason='paragraph_boundary', context_window=<tail of frag1> ✓
  hunk[3] para 4: tokens=4,  reason='paragraph_boundary', context_window=<tail of para3> ✓
  sibling_count=4 on all hunks ✓

Key design confirmation:
  context_window flows across ALL hunk boundaries — not just fragment-to-fragment.
  This means the sliding window creates smooth signal across the entire document stream.

## What is NOT in Tranche 2

- TreeSitter engine (Tranche 3): .py/.js/etc. files produce no output yet
- PEG engine (Tranche 4): .md files produce no output yet
- scope_stack, decorators, heading_trail, cross_refs — all empty (engine work)
- document_position — 0.0 for FallbackEngine paragraphs (char offsets are tracked but
  not exposed in document_position yet due to post-split position ambiguity; fix in Tranche 3/4)
- Real BPE token counting — char-estimate proxy in use (fix in Tranche 5/6)

## Next: Tranche 3 — TreeSitter engine v2

Priority fields to implement:
  scope_stack, scope_docstrings, base_classes, decorators, import_context,
  structural_path (name-path), sibling_count, document_position, split_reason="ast_boundary"

Reference: v1 treesitter_eng.py (reference only, do not copy verbatim)
