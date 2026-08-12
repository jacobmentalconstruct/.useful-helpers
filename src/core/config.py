"""
FILE:       src/core/config.py
ROLE:       Resolve project paths and load suite configuration.
DOMAIN:     core
DOES:       Locate the project root; expose canonical paths (config/, tools/, apps/, _docs/,
            logs/, the shared .venv python).
DEPENDS ON: (stdlib) os, pathlib, dataclasses
WIRES TO:   consumed by app.py, core.registry, core.invoke
NOTES:      Central configuration - one owned settings model, no scattered constants.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from src.core import instance


@dataclass(frozen=True)
class Paths:
    """Canonical project paths. Populated by resolve_paths().

    `root` is the TOOLKIT HOME  -  where the code, config, and registry live.
    `project_root` is the WORK TARGET  -  the project the toolkit operates on. They are the same
    in standalone/dev use; when the toolkit is installed as a sidecar (e.g. `.useful-helpers/`
    inside a host project), `project_root` is the host project (the sidecar's parent), so tools
    default their analysis to the whole project rather than the sidecar itself.
    `state` is the STATE ROOT  -  durable memory (journal/evidence/event-log/workbench). Distinct
    from generated artifacts: state survives an update-in-place, artifacts are disposable.
    Mirrors tools._toolkit.state_root()  -  keep the two in step.
    """
    root: Path
    project_root: Path | None
    config: Path
    tools: Path
    apps: Path
    docs: Path
    logs: Path
    state: Path
    venv_python: Path


class NoTargetBound(RuntimeError):
    """Raised when no work target can be established. Never guessed at."""


def _resolve_project_root(sidecar_root: Path) -> Path | None:
    """The work target, resolved by evidence only. Four cases, no fallthrough:

    1. An explicit `SUITE_PROJECT_ROOT` naming a real directory  -> that directory.
    2. An explicit `SUITE_PROJECT_ROOT` naming anything else     -> HARD ERROR.
       Previously this fell through silently and resolved to the parent while
       reporting success, so a typo in the target root was indistinguishable
       from a correct run.
    3. A canonical installed instance, proven by its identity manifest -> the
       target that manifest records, structurally. A malformed manifest RAISES;
       it never degrades into case 4.
    4. Otherwise (a sidecar in development)                      -> None.
       No target. Callers must refuse rather than guess.

    The folder NAME is deliberately not evidence. A dot-prefixed home used to
    infer a target, which made this repository bind to its own parent staging
    folder purely because of how it is named.
    """
    env = os.environ.get("SUITE_PROJECT_ROOT")
    if env is not None and env.strip() != "":
        p = Path(env).expanduser().resolve()
        if not p.is_dir():
            raise NoTargetBound(
                f"SUITE_PROJECT_ROOT does not name an existing directory: {p}. "
                "Refusing to fall back to an inferred target."
            )
        return p
    # Case 3, structurally. The `.suite_sidecar` marker is retired: it was written
    # only by development paths, never by the product installer, and zero markers were
    # ever tracked - so no supported installation can depend on it (journal 0026).
    #
    # `resolve()` RAISES on a malformed manifest rather than returning None. That
    # propagates on purpose: an instance whose identity is broken must not fall
    # through to case 4 and report "no target" as though it were merely uninstalled.
    ctx = instance.resolve(sidecar_root)
    if ctx is not None:
        return ctx.target_root
    return None


def resolve_paths(root: Path | None = None) -> Paths:
    """Resolve the toolkit home (default: two levels above this file), the work target
    (project_root), and derive canonical paths."""
    if root is None:
        root = Path(__file__).resolve().parents[2]
    root = Path(root).resolve()
    project_root = _resolve_project_root(root)
    # venv python differs by OS; invoke() falls back to sys.executable if this is absent.
    if os.name == "nt":
        venv_python = root / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = root / ".venv" / "bin" / "python"
    state_override = os.environ.get("SUITE_STATE_ROOT")
    return Paths(
        root=root,
        project_root=project_root,
        config=root / "config",
        tools=root / "tools",
        apps=root / "apps",
        # Product-facing documentation. This moved from `_docs/` to `docs/` when the
        # sidecar was collapsed to the repository root: `_docs/` is now the sidecar's
        # own record (its journal), and `docs/` is what ships. This line was missed in
        # that move, so paths.docs pointed at the journal directory.
        docs=root / "docs",
        logs=root / "logs",
        state=Path(state_override).resolve() if state_override else root / "_state",
        venv_python=venv_python,
    )
