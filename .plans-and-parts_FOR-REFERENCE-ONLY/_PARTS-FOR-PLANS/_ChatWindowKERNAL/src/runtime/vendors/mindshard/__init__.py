"""
Owns: the vendored MindSHARD runtime package copy and bootstrap entrypoint.
Does not own: host UI behavior, shell orchestration, or adapter policy.
Collaborates with: src.runtime.adapters.mindshard_adapter and vendored subpackages.
"""

from src.runtime.vendors.mindshard.bootstrap import ensure_bootstrap

__version__ = "0.1.0"

__all__ = ["ensure_bootstrap", "__version__"]
