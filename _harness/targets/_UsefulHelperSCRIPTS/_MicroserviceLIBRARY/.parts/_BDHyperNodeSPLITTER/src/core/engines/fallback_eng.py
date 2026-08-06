"""fallback_eng.py — blank-line paragraph splitter. Engine of last resort.

Handles any file type the higher-priority engines decline.
Pure stdlib — no external dependencies.

V2 additions over v1
---------------------
- document_position  — 0.0–1.0 char-offset position in source
- sibling_count      — total paragraph count (all siblings know the total)
- split_reason       — "paragraph_boundary" on every emitted hunk

V1 sub_split() responsibility moved to the Negotiator.
This engine only does parse(). The Negotiator owns token-budget slicing.

Boundary rule
-------------
parse() is size-blind. It splits on blank lines and yields paragraphs.
It does NOT enforce any token or character budget — that is the Negotiator's job.
"""

from __future__ import annotations

import re
from typing import Iterator, List

from core.contract.hyperhunk import HyperHunk

_PARA_RE = re.compile(r'\n[ \t]*\n+')


class FallbackEngine:
    """Paragraph splitter. No external dependencies."""

    def can_handle(self, origin_id: str, text: str | None = None) -> bool:  # noqa: ARG002
        """Always handles — engine of last resort."""
        return True

    def parse(
        self,
        text: str,
        origin_id: str,
        metadata: dict | None = None,
    ) -> Iterator[HyperHunk]:
        """Split text into paragraphs. Yields at least one hunk.

        Populates v2 fields:
            document_position  — char offset of paragraph start / total chars
            sibling_count      — total number of paragraphs in the document
            split_reason       — "paragraph_boundary"
        """
        text = text.strip()
        if not text:
            return

        total_chars = len(text)
        paragraphs: List[str] = [p.strip() for p in _PARA_RE.split(text) if p.strip()]
        if not paragraphs:
            paragraphs = [text]

        total = len(paragraphs)

        # Pre-compute char offsets for document_position
        char_offsets = _build_char_offsets(text, paragraphs)

        prev_occ: str | None = None
        for idx, para in enumerate(paragraphs):
            char_offset = char_offsets[idx]
            doc_pos = char_offset / total_chars if total_chars > 0 else 0.0

            hunk = HyperHunk(
                content=para,
                origin_id=origin_id,
                layer_type="REGEX",
                node_kind="paragraph",
                structural_path="doc",
                sibling_index=idx,
                metadata=dict(metadata or {}),
                parent_occurrence_id=None,
                prev_sibling_occurrence_id=prev_occ,
                # V2 fields
                sibling_count=total,
                document_position=round(doc_pos, 4),
                split_reason="paragraph_boundary",
                extraction_engine="FallbackEngine",
                extraction_confidence=0.6,
            )
            prev_occ = hunk.occurrence_id
            yield hunk


# ── Private helpers ───────────────────────────────────────────────────────


def _build_char_offsets(full_text: str, paragraphs: List[str]) -> List[int]:
    """Find the start char offset of each paragraph within full_text.

    Scans forward through full_text matching each paragraph in order.
    Falls back to 0 for any paragraph not found (shouldn't happen in practice).
    """
    offsets: List[int] = []
    cursor = 0
    for para in paragraphs:
        idx = full_text.find(para, cursor)
        if idx == -1:
            offsets.append(cursor)
        else:
            offsets.append(idx)
            cursor = idx + len(para)
    return offsets
