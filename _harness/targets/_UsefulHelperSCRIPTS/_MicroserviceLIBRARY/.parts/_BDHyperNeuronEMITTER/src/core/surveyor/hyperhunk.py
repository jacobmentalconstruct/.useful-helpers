"""surveyor/hyperhunk.py — HyperHunk surface richness validation + quality reporting.

Ownership: core/surveyor/hyperhunk.py

Validates incoming HyperHunks, reports surface richness metrics across a stream,
and emits diagnostic alerts.  The Surveyor is the Emitter's quality gate — it
does not transform data, only observes and reports.

Boundary rule: this module NEVER writes to the Cold Artifact or database.
               It only reads from HyperHunks and emits reports.

V1 vs V2 detection heuristic:
    A hunk is "v2-rich" if at least ONE of the following is non-empty:
    scope_stack, heading_trail, context_window, decorators, base_classes
    Otherwise it is "v1-thin" (valid wire format but missing context).

No v1 counterpart — original for the v2 Relational Field Engine.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional

log = logging.getLogger(__name__)


# ── Validation ─────────────────────────────────────────────────────────────

class ValidationError(Exception):
    """Raised when a HyperHunk fails required-field validation."""


def validate(hunk: Any) -> None:
    """Validate a HyperHunk's required fields.

    Raises ValidationError with a descriptive message on failure.
    Checks:
      - content is a non-empty string
      - origin_id is a non-empty string
      - node_kind is a non-empty string
      - layer_type is a non-empty string
      - hunk_id is a 64-char hex string (sha256)
      - occurrence_id is a 64-char hex string (sha256)
      - sibling_index is an int ≥ 0
      - document_position is a float in [0.0, 1.0]
      - extraction_confidence is a float in [0.0, 1.0]
    """
    if not isinstance(getattr(hunk, "content", None), str) or not hunk.content:
        raise ValidationError(f"hunk.content must be a non-empty string (got {hunk.content!r})")
    if not isinstance(getattr(hunk, "origin_id", None), str) or not hunk.origin_id:
        raise ValidationError(f"hunk.origin_id must be a non-empty string (got {hunk.origin_id!r})")
    if not isinstance(getattr(hunk, "node_kind", None), str) or not hunk.node_kind:
        raise ValidationError(f"hunk.node_kind must be a non-empty string (got {hunk.node_kind!r})")
    if not isinstance(getattr(hunk, "layer_type", None), str) or not hunk.layer_type:
        raise ValidationError(f"hunk.layer_type must be a non-empty string (got {hunk.layer_type!r})")

    hunk_id = getattr(hunk, "hunk_id", None)
    if not isinstance(hunk_id, str) or len(hunk_id) != 64:
        raise ValidationError(f"hunk.hunk_id must be a 64-char hex string (got {hunk_id!r})")

    occ_id = getattr(hunk, "occurrence_id", None)
    if not isinstance(occ_id, str) or len(occ_id) != 64:
        raise ValidationError(f"hunk.occurrence_id must be a 64-char hex string (got {occ_id!r})")

    sib = getattr(hunk, "sibling_index", None)
    if not isinstance(sib, int) or sib < 0:
        raise ValidationError(f"hunk.sibling_index must be int ≥ 0 (got {sib!r})")

    pos = getattr(hunk, "document_position", None)
    if not isinstance(pos, float) or not (0.0 <= pos <= 1.0):
        raise ValidationError(f"hunk.document_position must be float in [0,1] (got {pos!r})")

    conf = getattr(hunk, "extraction_confidence", None)
    if not isinstance(conf, float) or not (0.0 <= conf <= 1.0):
        raise ValidationError(f"hunk.extraction_confidence must be float in [0,1] (got {conf!r})")


def is_v2_rich(hunk: Any) -> bool:
    """Return True if the hunk carries any v2 context fields."""
    return bool(
        getattr(hunk, "scope_stack", [])
        or getattr(hunk, "heading_trail", [])
        or getattr(hunk, "context_window", "")
        or getattr(hunk, "decorators", [])
        or getattr(hunk, "base_classes", [])
    )


# ── Richness report ────────────────────────────────────────────────────────

@dataclass
class HunkReport:
    """Richness report for a single HyperHunk."""
    occurrence_id: str
    hunk_id:       str
    origin_id:     str
    node_kind:     str
    is_v2_rich:    bool
    surface_richness: Dict[str, float]  # from hunk.surface_richness()
    has_embedding: bool
    token_count:   int
    warnings:      List[str] = field(default_factory=list)


def report_one(hunk: Any, *, strict: bool = False) -> HunkReport:
    """Build a richness report for a single HyperHunk.

    Parameters
    ----------
    hunk : HyperHunk
    strict : bool
        If True, raises ValidationError on invalid hunks.
        If False, invalid hunks produce a report with warnings instead.
    """
    warnings: List[str] = []

    try:
        validate(hunk)
    except ValidationError as exc:
        if strict:
            raise
        warnings.append(str(exc))

    richness = {}
    try:
        richness = hunk.surface_richness()
    except Exception as exc:
        warnings.append(f"surface_richness() failed: {exc}")

    has_embedding = bool(getattr(hunk, "embedding", None))

    token_count = getattr(hunk, "token_count", 0)
    if token_count == 0:
        warnings.append("token_count=0 (Negotiator may not have run)")

    return HunkReport(
        occurrence_id=getattr(hunk, "occurrence_id", ""),
        hunk_id=getattr(hunk, "hunk_id", ""),
        origin_id=getattr(hunk, "origin_id", ""),
        node_kind=getattr(hunk, "node_kind", ""),
        is_v2_rich=is_v2_rich(hunk),
        surface_richness=richness,
        has_embedding=has_embedding,
        token_count=token_count,
        warnings=warnings,
    )


# ── Stream-level aggregation ───────────────────────────────────────────────

@dataclass
class StreamReport:
    """Aggregated quality report for a stream of HyperHunks.

    Attributes
    ----------
    total_hunks : int
    v2_rich_count : int
    v1_thin_count : int
    embedded_count : int
    mean_surface_richness : Dict[str, float]
        Mean richness fraction per surface (0.0–1.0).
    zero_token_count : int
        Number of hunks with token_count == 0.
    node_kind_distribution : Dict[str, int]
        Counts by node_kind.
    all_warnings : List[str]
        All per-hunk warnings concatenated.
    """
    total_hunks:          int = 0
    v2_rich_count:        int = 0
    v1_thin_count:        int = 0
    embedded_count:       int = 0
    zero_token_count:     int = 0
    mean_surface_richness: Dict[str, float] = field(default_factory=dict)
    node_kind_distribution: Dict[str, int]  = field(default_factory=dict)
    all_warnings:         List[str]         = field(default_factory=list)

    def summary_lines(self) -> List[str]:
        """Return a list of human-readable summary lines."""
        lines = [
            f"Total hunks:     {self.total_hunks}",
            f"V2-rich:         {self.v2_rich_count} ({_pct(self.v2_rich_count, self.total_hunks)}%)",
            f"V1-thin:         {self.v1_thin_count} ({_pct(self.v1_thin_count, self.total_hunks)}%)",
            f"Embedded:        {self.embedded_count} ({_pct(self.embedded_count, self.total_hunks)}%)",
            f"Zero token count:{self.zero_token_count}",
            "Surface richness (mean):",
        ]
        for surface, frac in sorted(self.mean_surface_richness.items()):
            lines.append(f"  {surface:<14} {frac:.2f}")
        if self.all_warnings:
            lines.append(f"Warnings: {len(self.all_warnings)}")
        return lines


def _pct(count: int, total: int) -> str:
    if total == 0:
        return "0"
    return f"{100 * count / total:.1f}"


class HunkSurveyor:
    """Surveys a stream of HyperHunks and accumulates a StreamReport.

    Usage::

        surveyor = HunkSurveyor()
        for hunk in hunk_stream:
            surveyor.observe(hunk)
        report = surveyor.finalize()
        for line in report.summary_lines():
            print(line)
    """

    def __init__(self, strict: bool = False) -> None:
        self._strict = strict
        self._reports: List[HunkReport] = []

    def observe(self, hunk: Any) -> HunkReport:
        """Observe a single hunk and accumulate its report."""
        r = report_one(hunk, strict=self._strict)
        self._reports.append(r)
        if r.warnings:
            for w in r.warnings:
                log.debug("surveyor warning [%s]: %s", r.occurrence_id[:8], w)
        return r

    def observe_stream(self, hunks: Iterable[Any]) -> int:
        """Observe all hunks in an iterable. Returns count observed."""
        count = 0
        for hunk in hunks:
            self.observe(hunk)
            count += 1
        return count

    def finalize(self) -> StreamReport:
        """Compute and return the aggregated StreamReport."""
        if not self._reports:
            return StreamReport()

        report = StreamReport(total_hunks=len(self._reports))

        # Accumulate per-surface richness sums
        surface_sums: Dict[str, float] = {}
        surface_counts: Dict[str, int] = {}

        for r in self._reports:
            if r.is_v2_rich:
                report.v2_rich_count += 1
            else:
                report.v1_thin_count += 1
            if r.has_embedding:
                report.embedded_count += 1
            if r.token_count == 0:
                report.zero_token_count += 1

            report.node_kind_distribution[r.node_kind] = (
                report.node_kind_distribution.get(r.node_kind, 0) + 1
            )

            for surface, frac in r.surface_richness.items():
                surface_sums[surface] = surface_sums.get(surface, 0.0) + frac
                surface_counts[surface] = surface_counts.get(surface, 0) + 1

            report.all_warnings.extend(r.warnings)

        # Mean surface richness
        report.mean_surface_richness = {
            s: round(surface_sums[s] / surface_counts[s], 3)
            for s in surface_sums
            if surface_counts.get(s, 0) > 0
        }

        return report

    def reset(self) -> None:
        """Clear accumulated observations."""
        self._reports.clear()
