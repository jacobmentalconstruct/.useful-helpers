"""
FILE:       src/core/policy.py
ROLE:       Authority policy  -  decides whether a tool's authority is permitted at the seam.
DOMAIN:     core
DOES:       Resolves an effective authority ceiling (Observe < Sandbox < Apply) from, in order:
            the SUITE_MAX_AUTHORITY env var, config/governance.json, else a permissive default
            (Apply  -  nothing blocked). A per-call `allow` can only tighten it. decide() returns
            whether a given authority passes.
DEPENDS ON: src.core.config (Paths), (stdlib) json, os, pathlib
WIRES TO:   consulted by src.core.invoke before dispatch
NOTES:      Ships permissive (Apply) so existing behavior is unchanged; the operator or an
            (untrusted) caller opts into a stricter ceiling. This is the guardrail the
            local-agent capstone will stand on  -  e.g. run an agent Observe-only, or require
            approval for Apply. Reads are cheap + best-effort; a broken config never blocks.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

AUTHORITIES = ("Observe", "Sandbox", "Apply")
_RANK = {"Observe": 0, "Sandbox": 1, "Apply": 2}
DEFAULT_CEILING = "Apply"  # permissive: everything allowed unless the operator/caller clamps


def _config_ceiling(paths) -> str | None:
    try:
        cfg = Path(paths.root) / "config" / "governance.json"
        if cfg.is_file():
            m = json.loads(cfg.read_text(encoding="utf-8")).get("max_authority")
            if m in _RANK:
                return m
    except Exception:
        pass
    return None


def effective_ceiling(paths, caller_allow: str | None = None) -> str:
    """Env override -> config -> default; then intersect with caller_allow (stricter wins)."""
    env = os.environ.get("SUITE_MAX_AUTHORITY")
    ceiling = env if env in _RANK else (_config_ceiling(paths) or DEFAULT_CEILING)
    if caller_allow in _RANK and _RANK[caller_allow] < _RANK[ceiling]:
        ceiling = caller_allow
    return ceiling


def decide(paths, authority: str | None, caller_allow: str | None = None) -> tuple[bool, str]:
    """Return (allowed, ceiling). Unknown/None authority passes  -  dispatch handles unknown tools."""
    ceiling = effective_ceiling(paths, caller_allow)
    if authority not in _RANK:
        return True, ceiling
    return _RANK[authority] <= _RANK[ceiling], ceiling
