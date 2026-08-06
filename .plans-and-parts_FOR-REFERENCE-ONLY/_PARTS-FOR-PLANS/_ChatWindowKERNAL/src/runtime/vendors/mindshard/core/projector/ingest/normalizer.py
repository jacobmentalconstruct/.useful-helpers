"""
manifold_kernel.ingest.normalizer — Text normalisation.

Transforms raw text into a canonical form suitable for hashing and
comparison.  Normalisation is deterministic: same input + same config
always yields the same output.
"""

from __future__ import annotations

import re
import unicodedata

from ..config import IngestConfig


def normalize_text(raw: str, config: IngestConfig) -> str:
    """
    Apply configured normalisation rules.

    Steps (in order):
    1. Unicode NFC normalisation
    2. Optional whitespace collapse
    3. Optional case folding
    4. Strip leading/trailing whitespace
    """
    text = unicodedata.normalize("NFC", raw)

    if config.normalize_whitespace:
        # Collapse runs of whitespace to single spaces, preserve newlines
        text = re.sub(r"[^\S\n]+", " ", text)
        # Collapse 3+ consecutive newlines to 2
        text = re.sub(r"\n{3,}", "\n\n", text)

    if config.normalize_case:
        text = text.lower()

    return text.strip()
