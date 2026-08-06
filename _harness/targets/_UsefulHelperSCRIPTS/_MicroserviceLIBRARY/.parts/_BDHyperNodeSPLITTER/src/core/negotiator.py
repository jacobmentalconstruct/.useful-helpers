"""negotiator.py — token-aware size negotiator.

The ONLY component in the pipeline that knows about the token budget.

Boundary rule
-------------
The Negotiator enforces the budget contract. It does not parse grammar
and it does not write regex. Its job is to receive raw HyperHunks from
the engines and decide: approve or sub-split.

V2 algorithm
------------
For each incoming HyperHunk:

  1. Compute context_window = tail of prev_content (sliding window overlap).
  2. IF hunk fits the token budget:
       → set token_count, context_window on the hunk
       → yield as-is (engine's split_reason is preserved)
  3. ELSE:
       → sub-split into token-budget-sized fragments
       → each fragment gets: token_count, context_window, split_reason="token_budget"
       → DAG lineage is preserved: fragment.parent_occurrence_id = oversized.occurrence_id
       → each fragment inherits all v2 scope/structure fields from the oversized hunk

V2 sub-split differs from v1
------------------------------
v1 delegated sub_split to FallbackEngine and sliced by character count.
v2 owns the sub-split logic here (cleaner ownership) and slices by token budget.
v2 populates context_window on each fragment so cross-fragment signal is smooth.
v2 inherits v2 scope/structure fields (scope_stack, heading_trail, etc.) into
each fragment so lineage context is not lost even on split fragments.

process_stream state
---------------------
process_stream() maintains prev_content state across the full document stream.
This means context_window carries forward across ALL hunk boundaries —
including boundaries between different AST nodes, not just fragment boundaries.
"""

from __future__ import annotations

import logging
from typing import Iterator, List

from core.contract.hyperhunk import HyperHunk
from core.contract.token_budget import TokenBudget
from core.signal_profile import SplitterSignalProfile

log = logging.getLogger(__name__)


class Negotiator:
    """Token-aware HyperHunk stream negotiator.

    Parameters
    ----------
    max_tokens : int
        Maximum BPE tokens allowed per hunk.
    overlap_ratio : float
        Fraction of max_tokens to carry forward as context_window overlap.
    chars_per_token : float
        Calibration for the char-estimate proxy (until real BPE is wired in).
    """

    def __init__(
        self,
        max_tokens: int = 256,
        overlap_ratio: float = 0.25,
        chars_per_token: float = 4.0,
        signal_profile: SplitterSignalProfile | None = None,
    ) -> None:
        self.budget = TokenBudget(
            max_tokens=max_tokens,
            overlap_ratio=overlap_ratio,
            chars_per_token=chars_per_token,
        )
        self.signal_profile = signal_profile or SplitterSignalProfile.default()

    # ── Public API ────────────────────────────────────────────────────

    def negotiate(
        self,
        hunk: HyperHunk,
        prev_content: str = "",
    ) -> Iterator[HyperHunk]:
        """Approve or sub-split a single HyperHunk.

        Sets token_count and context_window on every yielded hunk.
        Sets split_reason="token_budget" only on sub-split fragments
        (engine-set split_reason is preserved on whole hunks).

        Parameters
        ----------
        hunk : HyperHunk
            The raw hunk from an engine (may be oversized).
        prev_content : str
            Content of the previously yielded hunk, for context_window.

        Yields
        ------
        HyperHunk
            One or more budget-compliant hunks.
        """
        context = self.budget.context_window_tokens(prev_content)
        context = self._retain_context(context)

        if self.budget.fits(hunk.content):
            # Whole hunk approved — stamp v2 budget fields in-place
            hunk.token_count = self.budget.count(hunk.content)
            hunk.context_window = context
            yield hunk
        else:
            log.debug(
                "Sub-splitting oversized hunk %s (%d tokens) from %s",
                hunk.occurrence_id[:8],
                self.budget.count(hunk.content),
                hunk.origin_id,
            )
            yield from self._sub_split(hunk, context)

    def process_stream(
        self,
        hunks: Iterator[HyperHunk],
    ) -> Iterator[HyperHunk]:
        """Apply negotiate() lazily across an entire HyperHunk stream.

        Maintains prev_content state so context_window flows across
        ALL hunk boundaries in the document, not just fragment boundaries.

        This is a generator — it never accumulates the full stream in memory.
        """
        prev_content: str = ""
        for hunk in hunks:
            for result in self.negotiate(hunk, prev_content):
                prev_content = result.content
                yield result

    # ── Private ───────────────────────────────────────────────────────

    def _sub_split(
        self,
        oversized: HyperHunk,
        initial_context: str,
    ) -> Iterator[HyperHunk]:
        """Slice an oversized hunk into token-budget-sized fragments.

        DAG preservation:
            fragment.parent_occurrence_id = oversized.occurrence_id
            This means the original AST/CST/REGEX node stays in the DAG
            as the structural parent of all its fragments.

        Context window:
            fragment[0]   gets initial_context (from before the oversized hunk)
            fragment[i+1] gets context_window_tokens(fragment[i].content)

        V2 scope/structure inheritance:
            All v2 context fields (scope_stack, heading_trail, decorators, etc.)
            are inherited from the oversized hunk into every fragment.
            This preserves lineage even when content is split mid-token.
        """
        slices: List[str] = self.budget.split_to_slices(oversized.content)
        total = len(slices)
        parent_occ = oversized.occurrence_id
        prev_occ: str | None = oversized.prev_sibling_occurrence_id
        prev_content: str = ""

        for seq, fragment_text in enumerate(slices):
            context = (
                self.budget.context_window_tokens(prev_content)
                if prev_content
                else initial_context
            )
            context = self._retain_context(context)

            fragment_metadata = {
                **oversized.metadata,
                "fragment_of_occurrence_id": parent_occ,
                "fragment_index": seq,
                "fragment_count": total,
                "source_layer_type": oversized.layer_type,
                "source_node_kind": oversized.node_kind,
                "source_extraction_engine": oversized.extraction_engine,
            }
            if self.signal_profile.fragment_inheritance_profile.keep_parent_node_kind_family:
                fragment_metadata["source_node_kind_family"] = oversized.node_kind

            fragment = HyperHunk(
                content=fragment_text,
                origin_id=oversized.origin_id,
                layer_type="CHAR",
                node_kind=f"fragment_of_{oversized.node_kind}",
                structural_path=f"{oversized.structural_path}/fragment",
                sibling_index=seq,
                metadata=fragment_metadata,
                parent_occurrence_id=parent_occ,
                prev_sibling_occurrence_id=prev_occ,
                # V2 budget fields
                token_count=self.budget.count(fragment_text),
                split_reason="token_budget",
                context_window=context,
                # V2 scope/structure: inherit from oversized hunk
                scope_stack=list(oversized.scope_stack),
                scope_docstrings=dict(oversized.scope_docstrings),
                base_classes=list(oversized.base_classes),
                decorators=list(oversized.decorators),
                import_context=(
                    list(oversized.import_context)
                    if self.signal_profile.fragment_inheritance_profile.inherit_full_reference_context
                    else []
                ),
                heading_trail=list(oversized.heading_trail),
                cross_refs=(
                    list(oversized.cross_refs)
                    if self.signal_profile.fragment_inheritance_profile.inherit_full_reference_context
                    else []
                ),
                normalized_cross_refs=(
                    list(oversized.normalized_cross_refs)
                    if self.signal_profile.fragment_inheritance_profile.inherit_full_reference_context
                    else []
                ),
                reference_kinds=(
                    list(oversized.reference_kinds)
                    if self.signal_profile.fragment_inheritance_profile.inherit_full_reference_context
                    else []
                ),
                list_role=oversized.list_role,
                list_depth=oversized.list_depth,
                reference_confidence=(
                    oversized.reference_confidence
                    if self.signal_profile.fragment_inheritance_profile.inherit_full_reference_context
                    else 0.0
                ),
                # Position context: inherit from oversized
                document_position=oversized.document_position,
                sibling_count=oversized.sibling_count,
                extraction_engine=oversized.extraction_engine,
                extraction_confidence=oversized.extraction_confidence,
            )
            prev_occ = fragment.occurrence_id
            prev_content = fragment_text
            yield fragment

    def _retain_context(self, context: str) -> str:
        ratio = self.signal_profile.fragment_inheritance_profile.context_window_retain_ratio
        if ratio >= 1.0 or not context:
            return context
        if ratio <= 0.0:
            return ""
        keep_chars = max(1, int(len(context) * ratio))
        return context[-keep_chars:]
