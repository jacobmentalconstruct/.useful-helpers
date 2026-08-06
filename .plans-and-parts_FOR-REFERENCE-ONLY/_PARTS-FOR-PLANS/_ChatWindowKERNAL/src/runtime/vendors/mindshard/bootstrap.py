"""
Owns: vendored MindSHARD module alias registration for legacy import paths.
Does not own: host runtime policy, UI state, or agent orchestration behavior.
Collaborates with: the vendored runtime copy and the Mindshard adapter.
"""

from __future__ import annotations

from pathlib import Path
import sys
import types


_PACKAGE_ALIASES = {
    "core": "core",
    "bridge": "bridge",
    "memory": "memory",
    "agent": "agent",
    "evidence_bag": "core/evidence_bag",
    "mechanical_tokenizer_bundle": "core/embedder",
    "manifold_kernel": "core/projector",
}


def ensure_bootstrap() -> None:
    """Register stable top-level aliases for the vendored runtime copy."""
    package_root = Path(__file__).resolve().parent

    for alias, relative_path in _PACKAGE_ALIASES.items():
        if alias not in sys.modules:
            module = types.ModuleType(alias)
            module.__package__ = alias
            module.__path__ = [str(package_root / relative_path)]
            sys.modules[alias] = module
