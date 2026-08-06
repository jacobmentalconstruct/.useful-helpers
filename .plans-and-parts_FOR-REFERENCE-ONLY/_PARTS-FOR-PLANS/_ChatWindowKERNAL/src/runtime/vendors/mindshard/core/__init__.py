"""
Owns: vendored core package alias registration for legacy MindSHARD imports.
Does not own: host import policy outside the vendored runtime boundary.
Collaborates with: vendored projector, evidence-bag, and embedder packages.
"""

from __future__ import annotations

import importlib
import sys


_ALIASES = {
    "evidence_bag": f"{__name__}.evidence_bag",
    "mechanical_tokenizer_bundle": f"{__name__}.embedder",
    "manifold_kernel": f"{__name__}.projector",
}

for alias, target in _ALIASES.items():
    if alias not in sys.modules:
        sys.modules[alias] = importlib.import_module(target)
