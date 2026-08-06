# _BDHyperNodeSPLITTER v2 — Architecture

## Domain

Split source documents into richly-contextual HyperHunks.
Stream HyperHunks as NDJSON to stdout.

## Non-domain

- No embedding math
- No SQLite writes
- No graph projection
- No inference

## Builder Contract

See `builder_constraint_contract.md` in this folder.

---

## Current State

Phase 1 baseline is runnable.

- `FallbackEngine` is live for plain text and unknown files.
- `PEGEngine` is live for Markdown and structured prose.
- `TreeSitterEngine` is live for supported code files when the grammar packages from `requirements.txt` are installed.
- `Negotiator` is live and now preserves source-engine provenance on token-budget fragments.

Remaining work is about broader language coverage and richer surface population, not basic pipeline bring-up.

---

## Project Structure (Builder Contract §2.1 compliant)

```
_BDHyperNodeSPLITTER/
  src/
    app.py                      <- composition root + CLI entry
    core/
      __init__.py
      splitter.py               <- top-level coordinator: file → HyperHunk stream
      negotiator.py             <- token-aware size negotiator (v2: uses TokenBudget)
      engines/
        __init__.py
        treesitter_eng.py       <- AST-based splitting (code files)
        peg_eng.py              <- PEG-based splitting (markdown, structured docs)
        fallback_eng.py         <- blank-line fallback (unknown file types)
      contract/
        __init__.py
        hyperhunk.py            <- local copy of v2 HyperHunk (vendored in)
        token_budget.py         <- local copy of TokenBudget (vendored in)
  _docs/
    ARCHITECTURE.md             <- this file
    builder_constraint_contract.md
    _AppJOURNAL/                <- builder memory surface
  requirements.txt
  setup_env.bat
  run.bat
  README.md
  LICENSE.md
```

This is a HEADLESS STREAMING TOOL. No `src/ui/` layer. The builder contract's `src/ui/`
requirement applies to full applications; this component is a pipeline stage.

---

## Composition Root (`src/app.py`)

`app.py` is the single CLI entry point and composition root.

Responsibilities:
- Parse CLI arguments
- Instantiate the Splitter core with the token budget
- Iterate over input files or stdin
- Emit HyperHunk NDJSON to stdout
- Handle graceful failure (log, skip, continue)

It does NOT contain splitting logic. All splitting logic lives in `src/core/`.

---

## Splitter Coordinator (`src/core/splitter.py`)

**Parallel surface population** (Relational Field Engine — NOT a cascade):

1. ALL engines that `can_handle()` the file type run in parallel.
2. Each engine populates its designated surfaces on the HyperHunk.
3. Fallback ALWAYS runs (provides verbatim + structural baseline).
4. TreeSitter overlays the grammatical surface (if it can handle the file).
5. PEG overlays the structural surface with heading_trail (if it can handle the file).
6. `_merge_surfaces(base_hunk, overlay_hunks)` merges results — non-default overlay
   fields overwrite base defaults; non-default base fields are NEVER overwritten.
7. Negotiator runs AFTER merge (still the only budget enforcer).

The cascade model (TreeSitter OR PEG OR Fallback) was the v1 design.
The v2 model runs all applicable engines simultaneously.

---

## Engines

### TreeSitter Engine (`src/core/engines/treesitter_eng.py`)

Input: source code files (Python, JS, TS, Rust, Go, etc.)

V2 obligations — must populate:
- `scope_stack`        — full name chain from module root to this node
- `scope_docstrings`   — docstrings of enclosing named scopes
- `base_classes`       — for class_definition nodes
- `decorators`         — decorator list for decorated nodes
- `import_context`     — filtered import lines (names present in content)
- `structural_path`    — type path from root (existing v1 behavior)
- `sibling_count`      — count siblings at this scope level
- `document_position`  — char_offset / total_chars
- `split_reason`       — "ast_boundary" (or "token_budget" if Negotiator cut it)

### PEG Engine (`src/core/engines/peg_eng.py`)

Input: Markdown files, structured plain text

V2 obligations — must populate:
- `heading_trail`      — list of heading TEXT from root to this block
- `cross_refs`         — [text](target) links found in the block
- `structural_path`    — heading hierarchy path (existing v1 behavior)
- `sibling_count`      — count siblings under the same heading
- `document_position`  — char_offset / total_chars
- `split_reason`       — "heading_boundary" | "paragraph_boundary"

### Fallback Engine (`src/core/engines/fallback_eng.py`)

Input: anything else — plain text, unknown file types

V2 obligations — must populate:
- `document_position`  — char_offset / total_chars
- `split_reason`       — "paragraph_boundary" | "char_limit"

---

## Negotiator (`src/core/negotiator.py`)

### V1 (current, broken)
```python
if len(content) > max_size:
    # split by character count
```

### V2 (this build)
```python
budget = TokenBudget(max_tokens=max_tokens)
if not budget.fits(content):
    # split at token boundary
    fragment.token_count = budget.count(fragment_content)
    fragment.split_reason = "token_budget"
    # populate context_window = budget.context_window_tokens(prev_content)
```

The Negotiator is the ONLY component that writes `context_window`. It does this after
sub-splitting, so each fragment carries the tail of its predecessor's content.

### context_window population rule
- For the FIRST hunk in a document: `context_window = ""`
- For subsequent hunks: `context_window = TokenBudget.context_window_tokens(prev_content)`
- For sub-split fragments: `context_window = TokenBudget.context_window_tokens(prev_fragment)`

---

## Wire Format

Output is NDJSON — one JSON object per line, each being `HyperHunk.to_dict()`.

```bash
python src/app.py stream ./docs/  | python ../emitter/src/app.py emit
```

---

## Tranche Plan

### Tranche 1 — Contract integration
- Scaffold the project structure
- Install v2 HyperHunk contract locally
- Install TokenBudget stub locally
- DONE when: app.py runs, produces empty stream, no import errors

### Tranche 2 — Negotiator upgrade
- Replace character-based Negotiator with TokenBudget-based Negotiator
- Populate token_count, split_reason on all hunks
- Populate context_window on all non-first hunks
- DONE when: negotiator tests pass, context_window appears in output

### Tranche 3 — TreeSitter engine v2
- Add scope_stack, scope_docstrings, base_classes, decorators, import_context
- DONE when: Python test corpus produces fully-populated hunks

### Tranche 4 — PEG engine v2
- Add heading_trail, cross_refs, sibling_count, document_position
- DONE when: Markdown test corpus produces fully-populated hunks

### Tranche 5 — Fallback engine v2
- Add document_position, split_reason
- DONE when: plain text produces at minimum position + reason fields

### Tranche 6 — Integration test
- End-to-end: split → emit → inspect HyperNodes in cold_anatomy.db
- Verify richer fields appear in the DB
- Verify sliding window reduces hard embedding edges
