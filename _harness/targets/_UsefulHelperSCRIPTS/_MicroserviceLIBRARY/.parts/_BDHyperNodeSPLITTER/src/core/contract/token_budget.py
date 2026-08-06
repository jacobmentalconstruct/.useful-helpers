"""token_budget.py — Splitter-local Phase 1 token budget helper."""

from __future__ import annotations

from typing import List


class TokenBudget:
    """Token-aware budget calculator and slicer using a char-estimate proxy."""

    def __init__(
        self,
        max_tokens: int = 256,
        overlap_ratio: float = 0.25,
        chars_per_token: float = 4.0,
    ) -> None:
        if max_tokens < 1:
            raise ValueError(f"max_tokens must be >= 1, got {max_tokens!r}")
        if not 0.0 <= overlap_ratio < 1.0:
            raise ValueError(
                f"overlap_ratio must be in [0.0, 1.0), got {overlap_ratio!r}"
            )
        self.max_tokens = max_tokens
        self.overlap_ratio = overlap_ratio
        self._chars_per_token = chars_per_token
        self._max_chars = max(1, round(max_tokens * chars_per_token))
        self._overlap_chars = max(
            0, round(max_tokens * overlap_ratio * chars_per_token)
        )

    def count(self, text: str) -> int:
        if not text:
            return 0
        return max(1, round(len(text) / self._chars_per_token))

    def fits(self, text: str) -> bool:
        return self.count(text) <= self.max_tokens

    def headroom(self, text: str) -> int:
        return self.max_tokens - self.count(text)

    def split_to_slices(self, text: str) -> List[str]:
        if not text:
            return [""]
        slices = [
            text[i:i + self._max_chars]
            for i in range(0, len(text), self._max_chars)
        ]
        return slices if slices else [text]

    def context_window_tokens(self, prev_content: str) -> str:
        if not prev_content or self._overlap_chars <= 0:
            return ""
        return prev_content[-self._overlap_chars:]
