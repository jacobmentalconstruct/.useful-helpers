"""splitter.py — top-level Splitter coordinator.

Orchestration domain: dispatch + merge.
Does NOT own parsing logic (engines), budget enforcement (Negotiator),
or ontological classification (contract/ontology.py).

PARALLEL SURFACE POPULATION (Relational Field Engine)
------------------------------------------------------
Instead of a cascade (pick ONE engine), the coordinator runs ALL engines
that can_handle() the file type. Each engine populates its designated
surfaces on the HyperHunk. Results are merged:

  1. Primary engine produces the base hunk stream (TreeSitter for code,
     PEG for markdown, Fallback for everything else).
  2. Secondary engines that can_handle() overlay additional surface data
     onto each base hunk via _merge_surfaces().
  3. Fallback ALWAYS provides the verbatim + structural baseline when it
     is not the primary engine.
  4. Negotiator runs AFTER merge — still the only budget enforcer.

Merge rule: non-default overlay fields overwrite base defaults.
            Non-default base fields are NEVER overwritten.

Public API
----------
  process(text, origin_id, ...)          → Iterator[HyperHunk]
  process_file(path, ...)                → Iterator[HyperHunk]
  which_engines(origin_id)               → List[str]
  estimate_hunk_count(path, max_tokens)  → int

This module does NOT handle CLI or I/O. That belongs to app.py.
"""

from __future__ import annotations

import logging
import re
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Iterator, List

from core.contract.hyperhunk import HyperHunk
from core.contract.token_budget import TokenBudget
from core.engines.fallback_eng import FallbackEngine
from core.engines.peg_eng import PEGEngine
from core.engines.treesitter_eng import TreeSitterEngine
from core.negotiator import Negotiator
from core.signal_profile import SplitterSignalProfile

log = logging.getLogger(__name__)

# File extensions the splitter will attempt to process
_TEXT_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".md", ".markdown",
    ".txt", ".rst", ".csv", ".json", ".yaml", ".yml",
    ".html", ".htm", ".xml",
    ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rb", ".rs",
})

# ── Public API ────────────────────────────────────────────────────────────


def process(
    text: str,
    origin_id: str,
    max_tokens: int = 256,
    overlap_ratio: float = 0.25,
    chars_per_token: float = 4.0,
    metadata: dict | None = None,
    signal_profile: SplitterSignalProfile | None = None,
) -> Iterator[HyperHunk]:
    """Run the parallel surface-population pipeline on a single document.

    1. Identify primary engine (highest confidence that can_handle).
    2. Primary engine yields base HyperHunks (its designated surfaces).
    3. Secondary engines overlay additional surface data via merge.
    4. Negotiator enforces budget, stamps token_count and context_window.

    Parameters
    ----------
    text : str
        Raw document text.
    origin_id : str
        Used for engine routing (file extension) and DAG provenance.
    max_tokens : int
        Maximum BPE tokens per output hunk.
    overlap_ratio : float
        Context window overlap ratio for the sliding window.
    chars_per_token : float
        Char-estimate calibration (until real BPE is wired in).
    metadata : dict, optional
        Extra metadata merged into every hunk.

    Yields
    ------
    HyperHunk
        Budget-compliant, surface-enriched hunks ready for the Emitter.
    """
    resolved_signal_profile = signal_profile or SplitterSignalProfile.default()
    primary, secondaries = _select_engines(origin_id, text, resolved_signal_profile)
    meta = dict(metadata or {})
    meta.setdefault("file", origin_id)

    log.debug(
        "Dispatching %s — primary=%s, secondaries=%s",
        origin_id,
        type(primary).__name__,
        [type(s).__name__ for s in secondaries],
    )

    # Primary engine produces the base hunk stream
    base_hunks = primary.parse(text, origin_id, metadata=meta)

    # If there are secondary engines, overlay their surface data
    if secondaries:
        # Collect secondary hunks for surface merging.
        # Each secondary engine runs independently on the same text.
        secondary_hunk_lists = []
        for eng in secondaries:
            try:
                secondary_hunk_lists.append(list(eng.parse(text, origin_id, metadata=meta)))
            except Exception as exc:
                log.warning(
                    "Secondary engine %s failed on %s: %s",
                    type(eng).__name__, origin_id, exc,
                )

        merged = _merge_hunk_stream(base_hunks, secondary_hunk_lists)
    else:
        merged = base_hunks

    # Negotiator is the ONLY budget enforcer — runs after all surface merging
    negotiator = Negotiator(
        max_tokens=max_tokens,
        overlap_ratio=overlap_ratio,
        chars_per_token=chars_per_token,
        signal_profile=resolved_signal_profile,
    )
    yield from negotiator.process_stream(merged)


def process_file(
    path: str,
    max_tokens: int = 256,
    overlap_ratio: float = 0.25,
    chars_per_token: float = 4.0,
    signal_profile: SplitterSignalProfile | None = None,
) -> Iterator[HyperHunk]:
    """Auto-detect file type and stream HyperHunks.

    Handles:
      - Single file → read and pipe through process()
      - Directory   → walk all known text extensions recursively

    Yields
    ------
    HyperHunk
    """
    p = Path(path)
    if p.is_dir():
        yield from _process_directory(
            str(p), max_tokens, overlap_ratio, chars_per_token, signal_profile
        )
    else:
        yield from _process_single_file(
            str(p), max_tokens, overlap_ratio, chars_per_token, signal_profile
        )


def which_engines(
    origin_id: str,
    text: str | None = None,
    signal_profile: SplitterSignalProfile | None = None,
) -> List[str]:
    """Return class names of all engines that would handle origin_id.

    First element is the primary engine; rest are secondaries.
    """
    primary, secondaries = _select_engines(
        origin_id,
        text,
        signal_profile or SplitterSignalProfile.default(),
    )
    return [type(primary).__name__] + [type(s).__name__ for s in secondaries]


def estimate_hunk_count(path: str, max_tokens: int = 256) -> int:
    """Rough hunk count estimate — does not fully stream the pipeline.

    Uses paragraph count + token-budget sub-split estimate as a heuristic.
    Suitable for progress display only; not guaranteed accurate.
    """
    p = Path(path)
    if not p.is_file():
        return 0
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        paragraphs = len(re.split(r'\n\s*\n+', text.strip()))
        budget = TokenBudget(max_tokens=max_tokens)
        total_tokens = budget.count(text)
        sub_splits = max(0, total_tokens // max_tokens - paragraphs)
        return max(1, paragraphs + sub_splits)
    except Exception:
        return max(1, p.stat().st_size // (max_tokens * 4))


# ── Private: Engine Selection ─────────────────────────────────────────────


def _build_engines(signal_profile: SplitterSignalProfile) -> list:
    return [TreeSitterEngine(), PEGEngine(signal_profile=signal_profile), FallbackEngine()]


def _select_engines(
    origin_id: str,
    text: str | None = None,
    signal_profile: SplitterSignalProfile | None = None,
):
    """Select primary and secondary engines for this origin_id.

    Returns (primary_engine, [secondary_engines]).

    Primary = first engine in _ALL_ENGINES that can_handle().
    Secondaries = all OTHER engines that can_handle().

    Fallback always can_handle(), so it always participates
    (as primary for unknown types, as secondary for known types).
    """
    resolved_signal_profile = signal_profile or SplitterSignalProfile.default()
    capable = [
        eng for eng in _build_engines(resolved_signal_profile)
        if eng.can_handle(origin_id, text)
    ]
    if not capable:
        # Should never happen — Fallback.can_handle() returns True
        fallback = FallbackEngine()
        return fallback, []
    primary = capable[0]
    secondaries = capable[1:]
    return primary, secondaries


# ── Private: Surface Merging ──────────────────────────────────────────────


# Fields that define hunk identity / structure — never overwritten by merge.
_IDENTITY_FIELDS = frozenset({
    "content", "origin_id", "hunk_id", "occurrence_id",
    "structural_path", "sibling_index",
    "parent_occurrence_id", "prev_sibling_occurrence_id",
})

# Fields that engines should not compete over — Negotiator owns these.
_NEGOTIATOR_FIELDS = frozenset({
    "token_count", "context_window", "split_reason",
})


def _merge_surfaces(base: HyperHunk, overlay: HyperHunk) -> HyperHunk:
    """Merge overlay surface data into a base hunk.

    Merge rule:
      - Identity fields are NEVER overwritten (content, origin_id, DAG edges).
      - Negotiator fields are NEVER overwritten (budget domain).
      - For all other fields: overlay value replaces base value ONLY if
        the base value is at its default AND the overlay value is not.

    This respects domain boundaries:
      - The primary engine's structure decisions are authoritative.
      - Secondary engines contribute supplementary surface data only.
      - The Negotiator's domain is untouched.

    Returns a new HyperHunk with merged fields.
    """
    merged_kwargs = {}
    for f in dataclass_fields(HyperHunk):
        if not f.init:
            continue  # skip auto-computed fields

        name = f.name
        base_val = getattr(base, name)
        overlay_val = getattr(overlay, name)

        if name in _IDENTITY_FIELDS or name in _NEGOTIATOR_FIELDS:
            # Never overwrite — use base
            merged_kwargs[name] = base_val
            continue

        # Check if base is at default and overlay is not
        default_val = _get_field_default(f)
        base_is_default = (base_val == default_val)
        overlay_is_default = (overlay_val == default_val)

        if base_is_default and not overlay_is_default:
            merged_kwargs[name] = overlay_val
        else:
            merged_kwargs[name] = base_val

    return HyperHunk(**merged_kwargs)


def _get_field_default(f):
    """Extract the default value for a dataclass field."""
    from dataclasses import MISSING
    if f.default is not MISSING:
        return f.default
    if f.default_factory is not MISSING:
        return f.default_factory()
    return None  # required field — no default


def _merge_hunk_stream(
    base_hunks: Iterator[HyperHunk],
    secondary_hunk_lists: List[List[HyperHunk]],
) -> Iterator[HyperHunk]:
    """Merge secondary engine surfaces into the primary hunk stream.

    Strategy: for each base hunk, find the best-matching secondary hunk
    by content overlap (same origin_id + overlapping document_position).
    This is a simple nearest-position match — NOT a full alignment algorithm.

    If no secondary hunks match, the base hunk passes through unchanged.
    """
    if not secondary_hunk_lists:
        yield from base_hunks
        return

    # Flatten all secondary hunks
    all_secondaries = []
    for hunk_list in secondary_hunk_lists:
        all_secondaries.extend(hunk_list)

    if not all_secondaries:
        yield from base_hunks
        return

    for base in base_hunks:
        merged = base
        for overlay in all_secondaries:
            # Only merge hunks from the same document
            if overlay.origin_id != base.origin_id:
                continue
            # Position-based matching: overlay if positions are close
            if abs(overlay.document_position - base.document_position) < 0.05:
                merged = _merge_surfaces(merged, overlay)
        yield merged


# ── Private: File Processing ──────────────────────────────────────────────


def _process_single_file(
    path: str,
    max_tokens: int,
    overlap_ratio: float,
    chars_per_token: float,
    signal_profile: SplitterSignalProfile | None,
) -> Iterator[HyperHunk]:
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise OSError(f"Cannot read file: {path}") from exc
    yield from process(
        text,
        origin_id=path,
        max_tokens=max_tokens,
        overlap_ratio=overlap_ratio,
        chars_per_token=chars_per_token,
        signal_profile=signal_profile,
    )


_SKIP_DIRS = frozenset({"__pycache__", ".git", ".venv", "venv", "node_modules"})


def _process_directory(
    directory: str,
    max_tokens: int,
    overlap_ratio: float,
    chars_per_token: float,
    signal_profile: SplitterSignalProfile | None,
) -> Iterator[HyperHunk]:
    root = Path(directory)
    for file_path in sorted(root.rglob("*")):
        if any(part in _SKIP_DIRS for part in file_path.parts):
            continue
        if file_path.is_file() and file_path.suffix.lower() in _TEXT_EXTENSIONS:
            try:
                yield from _process_single_file(
                    str(file_path),
                    max_tokens,
                    overlap_ratio,
                    chars_per_token,
                    signal_profile,
                )
            except OSError as exc:
                log.warning("Skipping unreadable file %s: %s", file_path, exc)
