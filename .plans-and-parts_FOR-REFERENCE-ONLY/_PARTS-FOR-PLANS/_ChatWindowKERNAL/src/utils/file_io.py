"""
Owns: low-level file and directory helpers that are domain-neutral.
Does not own: JSON schema validation, logging setup, or application state semantics.
Collaborates with: persistence and bootstrap modules that need safe filesystem access.
"""

from __future__ import annotations

from pathlib import Path


def ensure_directory(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path
