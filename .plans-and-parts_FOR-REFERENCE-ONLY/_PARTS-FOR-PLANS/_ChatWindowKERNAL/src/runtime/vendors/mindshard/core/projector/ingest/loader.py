"""
manifold_kernel.ingest.loader — Source reading and metadata capture.

Accepts file paths or directory paths and yields (path, raw_text, file_hash)
triples.  Responsible for I/O only — no chunking, no normalisation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Generator, Tuple

from ..config import IngestConfig
from ..errors import SourceNotFoundError


@dataclass
class LoadedSource:
    """Raw material read from a single file."""
    path: str
    raw_text: str
    file_hash: str
    byte_length: int


def file_hash(path: Path) -> str:
    """SHA-256 of file content."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            h.update(block)
    return h.hexdigest()


def load_file(path: Path) -> LoadedSource:
    """Read a single file and return a LoadedSource."""
    if not path.is_file():
        raise SourceNotFoundError(f"File not found: {path}")
    raw = path.read_text(encoding="utf-8", errors="replace")
    return LoadedSource(
        path=str(path),
        raw_text=raw,
        file_hash=file_hash(path),
        byte_length=path.stat().st_size,
    )


def load_sources(
    target: str | Path,
    config: IngestConfig,
) -> Generator[LoadedSource, None, None]:
    """
    Yield LoadedSource objects for the given path.

    If *target* is a file, yield one item.
    If *target* is a directory, walk it recursively and yield every
    file whose extension matches config.file_extensions.
    """
    target = Path(target)
    if not target.exists():
        raise SourceNotFoundError(f"Path does not exist: {target}")

    if target.is_file():
        yield load_file(target)
        return

    for child in sorted(target.rglob("*")):
        if child.is_file() and child.suffix.lower() in config.file_extensions:
            try:
                yield load_file(child)
            except Exception:
                # Skip unreadable files during directory walks
                continue
