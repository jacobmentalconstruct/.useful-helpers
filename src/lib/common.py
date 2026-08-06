"""
FILE:       src/lib/common.py
ROLE:       Small shared helpers with a real, narrow domain (serialization + path hygiene).
DOMAIN:     lib
DOES:       Provide safe_json_dumps and relativize_paths (the ONE path scrubber shared by the
            event log and logging, so machine paths never leak into shareable state).
DEPENDS ON: (stdlib) json, os
WIRES TO:   used by core.*, interfaces.*, lib.logging_setup
NOTES:      NOT a junk drawer. Kept minimal; anything that grows its own domain
            graduates to its own module.
"""
from __future__ import annotations

import json
import os
from typing import Any, Iterable


def safe_json_dumps(value: Any, indent: int | None = None) -> str:
    """JSON-serialize with a stable fallback for non-serializable objects (repr via str)."""
    try:
        return json.dumps(value, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps(value, indent=indent, ensure_ascii=False, default=str)


def relativize_paths(text: str | None,
                     roots: "Iterable[tuple[str | None, str]] | None" = None) -> str | None:
    """THE central path scrubber (roots contract, field report A5/D5): replace absolute
    machine paths in `text` with scoped tokens so shareable state (event log errors, log
    lines, journal prose) never leaks a local hard-drive layout.

    `roots` is (base_path, token) pairs  -  pass them explicitly where a Paths object is in
    hand (e.g. (str(paths.project_root), "<project>"), (str(paths.root), "<toolkit>")).
    Falls back to the SUITE_PROJECT_ROOT / SUITE_HOME env vars (set by the invoke seam for
    tool subprocesses). Both slash forms of each base are stripped."""
    if not text:
        return text
    pairs = list(roots) if roots is not None else [
        (os.environ.get("SUITE_PROJECT_ROOT"), "<project>"),
        (os.environ.get("SUITE_HOME"), "<toolkit>"),
    ]
    for base, token in pairs:
        if not base:
            continue
        for form in {base, base.replace("/", "\\"), base.replace("\\", "/")}:
            text = text.replace(form, token)
    return text
