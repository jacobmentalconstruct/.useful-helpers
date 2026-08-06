"""
manifold_kernel.ingest.chunker — Configurable text segmentation.

Splits normalised text into artifact-sized chunks with configurable
size and overlap.  Each chunk records its character offsets for
provenance tracing back to the source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from ..config import IngestConfig


@dataclass
class ChunkSpan:
    """A single chunk with its position metadata."""
    text: str
    char_start: int
    char_end: int
    ordinal: int


def chunk_text(
    text: str,
    config: IngestConfig,
) -> List[ChunkSpan]:
    """
    Segment *text* into overlapping chunks.

    The chunker first tries to split on paragraph boundaries (double
    newlines).  If a paragraph exceeds chunk_size, it is split further
    at sentence boundaries or, as a last resort, at word boundaries.
    """
    if not text.strip():
        return []

    chunk_size = max(64, config.chunk_size)
    overlap = max(0, min(config.chunk_overlap, chunk_size // 2))

    # Simple sliding-window with overlap, splitting at whitespace boundaries
    chunks: List[ChunkSpan] = []
    start = 0
    ordinal = 0

    while start < len(text):
        end = start + chunk_size

        if end < len(text):
            # Try to break at a paragraph boundary
            break_at = text.rfind("\n\n", start, end)
            if break_at == -1 or break_at <= start:
                # Try sentence boundary
                break_at = text.rfind(". ", start, end)
                if break_at != -1:
                    break_at += 2  # include the period and space
            if break_at == -1 or break_at <= start:
                # Try word boundary
                break_at = text.rfind(" ", start, end)
            if break_at != -1 and break_at > start:
                end = break_at
        else:
            end = len(text)

        chunk_text_str = text[start:end].strip()
        if chunk_text_str:
            chunks.append(ChunkSpan(
                text=chunk_text_str,
                char_start=start,
                char_end=end,
                ordinal=ordinal,
            ))
            ordinal += 1

        # Advance with overlap
        if end >= len(text):
            break
        start = max(start + 1, end - overlap)

    return chunks
