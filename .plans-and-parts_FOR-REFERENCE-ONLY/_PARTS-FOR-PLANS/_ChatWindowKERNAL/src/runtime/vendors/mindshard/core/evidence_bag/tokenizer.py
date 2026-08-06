"""
Lexical tokenizer for the Evidence Bag system.

Provides lightweight token extraction and overlap counting used by the
gravity scorer for tag_matches, content_matches, and scope_matches.

Token rule: lowercase alphanumeric or underscore, minimum length 3.
"""

from __future__ import annotations

import re
from typing import FrozenSet, Set, Union

_TOKEN_RE = re.compile(r"[a-z0-9_]{3,}")


def tokenize(text: str) -> FrozenSet[str]:
    """
    Extract unique tokens from text.

    Tokens are lowercase sequences of [a-z0-9_] with length >= 3.

    Args:
        text: Input string (any casing).

    Returns:
        Frozen set of unique token strings.
    """
    return frozenset(_TOKEN_RE.findall(text.lower()))


def token_overlap(a: Union[Set[str], FrozenSet[str]],
                  b: Union[Set[str], FrozenSet[str]]) -> int:
    """
    Count the number of shared tokens between two sets.

    Args:
        a: First token set.
        b: Second token set.

    Returns:
        Integer count of common tokens.
    """
    return len(a & b)
