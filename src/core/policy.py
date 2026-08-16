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

from src.lib.logging_setup import get_logger

log = get_logger("core.policy")

AUTHORITIES = ("Observe", "Sandbox", "Apply")
_RANK = {"Observe": 0, "Sandbox": 1, "Apply": 2}
DEFAULT_CEILING = "Apply"  # permissive: everything allowed unless the operator/caller clamps


def _config_ceiling(paths) -> str | None:
    """The operator's declared ceiling, or None.

    STILL BEST-EFFORT, BUT NO LONGER SILENT. A broken config must not block the seam -
    that part is deliberate and unchanged. What was wrong is that it failed **open and
    invisibly**: an operator who clamps a sensitive target to `Observe` and mistypes the
    file gets the *most permissive* ceiling and no indication whatever.

    Two distinct ways that happened, both returning None and both indistinguishable
    from "the operator set no ceiling":

      1. unreadable or malformed JSON  -> swallowed by `except Exception: pass`
      2. a value outside _RANK ("observe", "apply", a typo) -> `m in _RANK` is False

    Each now says so at WARNING. The fail-open DEFAULT is unchanged, because changing a
    security posture is the operator's decision and not a review's - it is recorded in
    the backlog as a question, not answered here. But a governance control that
    degrades has to be audible, or it is not a control.
    """
    cfg = Path(paths.root) / "config" / "governance.json"
    try:
        if not cfg.is_file():
            return None
        m = json.loads(cfg.read_text(encoding="utf-8")).get("max_authority")
    except (OSError, ValueError) as e:
        log.warning("policy: governance config unreadable (%s: %s) at %s - falling back "
                    "to the permissive default %r; NO CEILING IS IN FORCE",
                    type(e).__name__, e, cfg, DEFAULT_CEILING)
        return None
    if m is None:
        return None                       # present, declares no ceiling. Not a defect.
    if m not in _RANK:
        log.warning("policy: governance config declares max_authority=%r, which is not "
                    "one of %s - falling back to the permissive default %r; NO CEILING "
                    "IS IN FORCE", m, list(AUTHORITIES), DEFAULT_CEILING)
        return None
    return m


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
