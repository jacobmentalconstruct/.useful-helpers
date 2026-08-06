"""
FILE:       src/lib/logging_setup.py
ROLE:       Central logging configuration for the suite.
DOMAIN:     lib
DOES:       Configure logging to logs/suite.log (+ stderr) and return named loggers. Both
            handlers carry the shared path scrubber so machine paths never land in suite.log.
DEPENDS ON: src.lib.common (relativize_paths), (stdlib) logging, pathlib
WIRES TO:   used by app.py, core.invoke, interfaces.*
NOTES:      Logging over printing. Handlers write to stderr so stdout stays clean
            for CLI/MCP JSON payloads.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from src.lib.common import relativize_paths

_CONFIGURED = False


class _ScrubFilter(logging.Filter):
    """Handler-level filter: relativize machine paths in every record (roots contract, A5).
    Handler filters apply to propagated child-logger records, unlike logger filters."""

    def __init__(self, roots):
        super().__init__()
        self._roots = tuple(roots) if roots else None

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        scrubbed = relativize_paths(msg, self._roots)
        if scrubbed != msg:
            record.msg = scrubbed
            record.args = ()
        return True


def configure(logs_dir, scrub_roots=None) -> None:
    """Configure suite logging once. Idempotent. `scrub_roots` is (base, token) pairs for the
    path scrubber (pass the resolved Paths roots; env fallback otherwise)."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logs_dir = Path(logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    scrub = _ScrubFilter(scrub_roots)

    file_handler = logging.FileHandler(logs_dir / "suite.log", encoding="utf-8")
    file_handler.setFormatter(fmt)
    file_handler.addFilter(scrub)
    # stderr, never stdout  -  stdout carries CLI/MCP JSON.
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(fmt)
    stream_handler.addFilter(scrub)

    root = logging.getLogger("suite")
    root.setLevel(logging.INFO)
    root.handlers[:] = [file_handler, stream_handler]
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the 'suite' root."""
    return logging.getLogger(f"suite.{name}")
