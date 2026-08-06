"""Service layer (parse-only fixture)."""
from domain import model


def used_service():
    # References the domain module (services -> domain, an allowed edge) but not PublicThing,
    # so PublicThing stays caller-less (to exercise the __all__ path in dead_code).
    return model
