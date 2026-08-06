"""Domain layer (parse-only fixture)."""
from services import core  # DELIBERATE back-edge domain -> services (illegal + a cycle)

__all__ = ["PublicThing"]

_UNUSED = core  # keep the import "used" so it isn't optimized away by a reader


def PublicThing():
    """Exported via __all__ (public API surface) but with no static caller ->
    dead_code must mark this LOW confidence, not a deletion target."""
    return 1


def genuinely_dead():
    """No references, no decorator, top-level -> dead_code SHOULD flag this HIGH."""
    return 2
