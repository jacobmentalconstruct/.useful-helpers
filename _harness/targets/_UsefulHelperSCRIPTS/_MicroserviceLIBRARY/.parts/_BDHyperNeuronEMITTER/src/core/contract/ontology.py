"""ontology.py — Emitter-local node type registry."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class NodeType:
    name: str
    parent: Optional[str]
    layer_type: str
    dynamical_role: str
    default_coupling: float
    description: str


_REGISTRY: Dict[str, NodeType] = {}


def _register(nt: NodeType) -> None:
    _REGISTRY[nt.name] = nt


_register(NodeType("code_node", None, "AST", "attractor", 1.0, "Abstract root for all code-derived node types."))
_register(NodeType("prose_node", None, "CST", "carrier", 1.0, "Abstract root for all prose/document-derived node types."))
_register(NodeType("fragment_node", None, "CHAR", "resonator", 0.7, "Abstract root for sub-split fragment types."))

_register(NodeType("function_definition", "code_node", "AST", "attractor", 2.0, "Top-level or nested function."))
_register(NodeType("class_definition", "code_node", "AST", "attractor", 2.0, "Class definition."))
_register(NodeType("method_definition", "code_node", "AST", "conductor", 1.8, "Method inside a class body."))
_register(NodeType("decorated_definition", "code_node", "AST", "conductor", 1.8, "Function or class with decorators."))
_register(NodeType("class_declaration", "code_node", "AST", "conductor", 1.8, "Class declaration (JS/TS)."))
_register(NodeType("function_declaration", "code_node", "AST", "conductor", 1.8, "Function declaration (JS/TS)."))
_register(NodeType("export_statement", "code_node", "AST", "conductor", 1.5, "Module export (JS/TS)."))
_register(NodeType("module_preamble", "code_node", "AST", "conductor", 1.2, "Accumulated imports and module-level constants."))

_register(NodeType("md_heading", "prose_node", "CST", "guide", 1.5, "Markdown heading (any level)."))
_register(NodeType("md_code_block", "prose_node", "CST", "resonator", 1.4, "Fenced or indented code block in Markdown."))
_register(NodeType("md_paragraph", "prose_node", "CST", "carrier", 1.0, "Markdown paragraph."))
_register(NodeType("md_list", "prose_node", "CST", "carrier", 1.0, "Markdown list block."))
_register(NodeType("md_list_item", "prose_node", "CST", "carrier", 1.0, "Markdown list item."))
_register(NodeType("md_table", "prose_node", "CST", "resonator", 1.0, "Markdown table."))
_register(NodeType("md_blockquote", "prose_node", "CST", "carrier", 0.9, "Markdown blockquote."))
_register(NodeType("md_hr", "prose_node", "CST", "guide", 0.3, "Markdown horizontal rule (thematic break)."))

_register(NodeType("paragraph", "prose_node", "REGEX", "carrier", 1.0, "Blank-line-delimited paragraph (fallback engine)."))
_register(NodeType("fragment_of_", "fragment_node", "CHAR", "resonator", 0.7, "Sub-split fragment of an oversized hunk (base pattern)."))

_UNKNOWN = NodeType("_unknown", None, "REGEX", "carrier", 1.0, "Fallback for unregistered node_kind values.")


def lookup(name: str) -> NodeType:
    if name in _REGISTRY:
        return _REGISTRY[name]
    if name.startswith("fragment_of_"):
        return _REGISTRY.get("fragment_of_", _UNKNOWN)
    log.warning("Unregistered node_kind: %r — using default", name)
    return _UNKNOWN


def validate(name: str) -> bool:
    return name in _REGISTRY or name.startswith("fragment_of_")


def get_coupling(name: str) -> float:
    return lookup(name).default_coupling


def get_dynamical_role(name: str) -> str:
    return lookup(name).dynamical_role


def is_subtype(name: str, ancestor: str) -> bool:
    if name == ancestor:
        return True
    current = lookup(name)
    visited = {current.name}
    while current.parent is not None:
        if current.parent == ancestor:
            return True
        if current.parent in visited:
            break
        visited.add(current.parent)
        current = lookup(current.parent)
    return False


def register(node_type: NodeType) -> None:
    if node_type.name in _REGISTRY:
        log.info("Overwriting existing NodeType: %s", node_type.name)
    _REGISTRY[node_type.name] = node_type


def all_types() -> Dict[str, NodeType]:
    return dict(_REGISTRY)
