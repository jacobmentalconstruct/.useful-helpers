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
NOTES:      Ships permissive (Apply) when NO governance is declared, so existing behavior is
            unchanged; the operator or an (untrusted) caller opts into a stricter ceiling.
            This is the guardrail the local-agent capstone stands on  -  e.g. run an agent
            Observe-only, or require approval for Apply. A governance file that is PRESENT
            but unreadable degrades to Observe rather than to the permissive default: see
            _config_ceiling. Absent is not the same as broken.
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
DEGRADED_CEILING = "Observe"  # a governance file that is PRESENT but cannot be read


def _config_ceiling(paths) -> str | None:
    """The operator's declared ceiling, DEGRADED_CEILING if it cannot be read, else None.

    ABSENT IS NOT THE SAME AS BROKEN, and collapsing the two was the defect. Both used to
    return None and land on the permissive default, so an operator who clamps a sensitive
    target to `Observe` and mistypes the file got the MOST permissive ceiling instead of
    the strictest - the one direction a safety control must never fail.

    Two ways that happened:

      1. unreadable or malformed JSON  -> swallowed by `except Exception: pass`
      2. a value outside _RANK ("observe", "apply", a typo) -> `m in _RANK` is False

    An earlier pass made both AUDIBLE but deliberately left the posture alone, on the
    grounds that changing a security posture is the operator's decision and not a
    review's. That was the right call then and the decision has since been made: T8
    requires a governed work loop, and a bench that can rewrite arbitrary target files
    cannot treat an unreadable mutation control as permission to mutate.

    WHY OBSERVE AND NOT SANDBOX. A broken file is a control in an UNKNOWN state, so the
    only defensible degradation is the one that is safe under every value the operator
    might have intended - and Observe is the only such value. Choosing Sandbox would be
    assuming the operator did not mean Observe, which is precisely the assumption there
    is no evidence for. Diagnosis stays available (reads still work, so the operator can
    inspect the target and find the broken file); mutation is withheld until a human
    repairs the declaration.

    THE THREE BENIGN CASES STAY PERMISSIVE, because none of them is a broken control:
    no file at all, a file declaring no ceiling, and a valid clamp. Only "present and
    unreadable" degrades.
    """
    cfg = Path(paths.root) / "config" / "governance.json"
    try:
        if not cfg.is_file():
            return None                   # no governance declared. Not a defect.
        m = json.loads(cfg.read_text(encoding="utf-8")).get("max_authority")
    except (OSError, ValueError) as e:
        log.warning("policy: governance config unreadable (%s: %s) at %s - DEGRADING to "
                    "%r; Apply is withheld until the declaration is repaired",
                    type(e).__name__, e, cfg, DEGRADED_CEILING)
        return DEGRADED_CEILING
    if m is None:
        return None                       # present, declares no ceiling. Not a defect.
    if m not in _RANK:
        log.warning("policy: governance config declares max_authority=%r, which is not "
                    "one of %s - DEGRADING to %r; Apply is withheld until the "
                    "declaration is repaired", m, list(AUTHORITIES), DEGRADED_CEILING)
        return DEGRADED_CEILING
    return m


def effective_ceiling(paths, caller_allow: str | None = None) -> str:
    """Env override -> config -> default; then intersect with caller_allow (stricter wins).

    SUITE_MAX_AUTHORITY still wins over a degraded config, and that is intended rather
    than overlooked: it is an explicit statement by whoever launched the process, and an
    explicit statement outranks an unreadable one. It is also the operator's way out of
    a degraded bench without editing files. What it must never be is the SILENT way out,
    which is why the degradation logs at WARNING before this runs.
    """
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
