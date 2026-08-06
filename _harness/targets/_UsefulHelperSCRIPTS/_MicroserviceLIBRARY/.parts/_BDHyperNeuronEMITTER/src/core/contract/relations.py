"""relations.py — Emitter-local edge predicate registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class EdgePredicate:
    name: str
    inverse: Optional[str]
    cardinality: str
    transitive: bool
    default_weight: float
    description: str


_PREDICATES: Dict[str, EdgePredicate] = {}


def _register(pred: EdgePredicate) -> None:
    _PREDICATES[pred.name] = pred


_register(EdgePredicate("pull", "pulled_by", "N:1", False, 1.0, "Structural parent edge. Child pulls toward parent."))
_register(EdgePredicate("pulled_by", "pull", "1:N", False, 1.0, "Inverse of pull. Parent is pulled_by children."))
_register(EdgePredicate("precedes", "follows", "1:1", True, 0.8, "Left sibling sequence edge. Right node precedes left."))
_register(EdgePredicate("follows", "precedes", "1:1", True, 0.8, "Inverse of precedes. Left node follows right."))
_register(EdgePredicate("scope_member_of", "scope_contains", "N:1", True, 0.6, "Scope containment. Inner scope is member_of outer scope name."))
_register(EdgePredicate("scope_contains", "scope_member_of", "1:N", True, 0.6, "Inverse of scope_member_of. Outer scope contains inner."))
_register(EdgePredicate("section_of", "section_contains", "N:1", False, 0.5, "Heading containment. Block belongs to a heading section."))
_register(EdgePredicate("section_contains", "section_of", "1:N", False, 0.5, "Inverse of section_of. Heading contains blocks."))
_register(EdgePredicate("references", "referenced_by", "N:N", False, 0.4, "Cross-reference link. Source block references a target."))
_register(EdgePredicate("referenced_by", "references", "N:N", False, 0.4, "Inverse of references. Target is referenced_by source."))


def lookup(name: str) -> Optional[EdgePredicate]:
    pred = _PREDICATES.get(name)
    if pred is None:
        log.warning("Unregistered edge predicate: %r", name)
    return pred


def inverse_of(name: str) -> Optional[str]:
    pred = _PREDICATES.get(name)
    if pred is None:
        return None
    return pred.inverse


def validate_relation(rel: Dict[str, Any]) -> bool:
    if not isinstance(rel, dict):
        return False
    op = rel.get("op")
    if not isinstance(op, str) or op not in _PREDICATES:
        return False
    target = rel.get("target")
    if not isinstance(target, str) or not target:
        return False
    weight = rel.get("weight")
    if not isinstance(weight, (int, float)) or weight < 0:
        return False
    return True


def validate_relations(rels: List[Dict[str, Any]]) -> List[str]:
    warnings: List[str] = []
    for i, rel in enumerate(rels):
        if not isinstance(rel, dict):
            warnings.append(f"relation[{i}]: not a dict")
            continue
        op = rel.get("op", "<missing>")
        if op not in _PREDICATES:
            warnings.append(f"relation[{i}]: unregistered op {op!r}")
        if not rel.get("target"):
            warnings.append(f"relation[{i}]: missing or empty target")
        weight = rel.get("weight")
        if not isinstance(weight, (int, float)):
            warnings.append(f"relation[{i}]: weight is not a number")
        elif weight < 0:
            warnings.append(f"relation[{i}]: negative weight {weight}")
    return warnings


def register(predicate: EdgePredicate) -> None:
    if predicate.name in _PREDICATES:
        log.info("Overwriting existing EdgePredicate: %s", predicate.name)
    _PREDICATES[predicate.name] = predicate


def all_predicates() -> Dict[str, EdgePredicate]:
    return dict(_PREDICATES)
