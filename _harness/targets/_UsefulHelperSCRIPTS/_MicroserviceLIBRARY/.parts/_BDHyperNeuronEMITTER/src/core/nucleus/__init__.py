"""nucleus — Bootstrap Nucleus for Phase 1 edge scoring.

Phase 1: fixed-weight Nucleus using ontology coupling constants.
Phase 2 (deferred): FFN Nucleus trained on Phase 1 edge decisions.
"""

from .bootstrap import BootstrapNucleus, NucleusResult

__all__ = ["BootstrapNucleus", "NucleusResult"]
