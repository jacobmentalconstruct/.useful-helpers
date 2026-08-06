"""hyperhunk.py — Emitter-local v2 HyperHunk + Relational DSL extension.

Extends the v2 base HyperHunk with:
  - embedding field (optional SVD embedding vector — populated by Emitter)
  - attention_weight property (v2: decorators boost, heading_trail depth reduction,
    token_count floor)
  - relations property (v2: scope_member_of, section_of, references fully active)
  - semantic_surface override (exposes embedding vector)

This module now owns its local base contract directly through
``core.contract.base_hyperhunk`` so the Emitter can run standalone from its
own project root.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .base_hyperhunk import HyperHunk as _BaseHyperHunk

# ── Attention weight table (node_kind → base semantic gravity) ────────────
# These MUST mirror ontology.py default_coupling values exactly.
# Source of truth is ontology.py — this table is a fast-path cache.
_ATTENTION_WEIGHTS: Dict[str, float] = {
    "function_definition":   2.0,
    "class_definition":      2.0,
    "decorated_definition":  1.8,
    "method_definition":     1.8,
    "class_declaration":     1.8,
    "function_declaration":  1.8,
    "export_statement":      1.5,
    "md_heading":            1.5,
    "md_code_block":         1.4,
    "module_preamble":       1.2,
    "paragraph":             1.0,
    "md_paragraph":          1.0,
    "md_list":               1.0,
    "md_list_item":          1.0,
    "md_table":              1.0,
    "md_blockquote":         0.9,
    "md_hr":                 0.3,
}

_DEFAULT_ATTENTION: float = 1.0
_FRAGMENT_ATTENTION: float = 0.7

# V2 Relational DSL ops
_SCOPE_OP     = "scope_member_of"
_SECTION_OP   = "section_of"
_REFERENCE_OP = "references"


@dataclass
class HyperHunk(_BaseHyperHunk):
    """V2 HyperHunk with Emitter-side Relational DSL extension.

    Adds:
        embedding : List[float] or None
            SVD/BPE embedding vector. Populated by the Emitter's
            DeterministicEmbedProvider after the hunk is ingested.
            None until the embedding pass has run.
    """

    # Emitter-side fields (not in the wire format — local to the Emitter)
    embedding: Optional[List[float]] = field(default=None, compare=False, repr=False)

    # ── attention_weight ──────────────────────────────────────────────────

    @property
    def attention_weight(self) -> float:
        """Semantic gravity of this node_kind, adjusted for v2 context.

        V2 adjustments applied in order:
          1. Fragment nodes: fixed 0.7 (sub-split fragments carry less mass)
          2. Base weight from _ATTENTION_WEIGHTS (mirrors ontology coupling)
          3. +0.1 per decorator present (capped at +0.3 total)
          4. -0.05 per heading_trail depth level (floor at 0.5)
          5. Floor reduction to 0.6 for very short hunks (token_count < 20 and > 0)
        """
        if self.node_kind.startswith("fragment_of_"):
            return _FRAGMENT_ATTENTION

        w = _ATTENTION_WEIGHTS.get(self.node_kind, _DEFAULT_ATTENTION)

        # Decorator boost: each decorator adds a small bump (max +0.3)
        if self.decorators:
            w += min(len(self.decorators) * 0.1, 0.3)

        # Heading depth reduction: deeper sections are less gravitational
        if self.heading_trail:
            w = max(0.5, w - len(self.heading_trail) * 0.05)

        # Token count floor: very short hunks get reduced attention
        if 0 < self.token_count < 20:
            w = min(w, 0.6)

        return round(w, 4)

    # ── relations ─────────────────────────────────────────────────────────

    @property
    def relations(self) -> List[Dict[str, Any]]:
        """Relational DSL — all DAG and structural relations for this hunk.

        V1 relations (structural pointers, occurrence_id targets):
          pull     — parent structural edge (target = parent_occurrence_id)
          precedes — left sibling edge (target = prev_sibling_occurrence_id)

        V2 relations (v2 context fields, non-occurrence-id targets):
          scope_member_of — one per scope_stack entry (inner → outer, weight 1.5)
          section_of      — one per heading_trail entry (root → leaf, weight 1.2)
          references      — one per cross_refs entry (weight 0.9)

        Note: scope_member_of, section_of, and references targets are
        scope names / heading texts / URLs — NOT occurrence_ids.
        The Assembler handles them separately from structural edges.
        """
        rels: List[Dict[str, Any]] = []

        # V1: structural parent edge
        if self.parent_occurrence_id:
            rels.append({
                "op":     "pull",
                "target": self.parent_occurrence_id,
                "weight": 1.0,
            })

        # V1: left sibling sequence edge
        if self.prev_sibling_occurrence_id:
            rels.append({
                "op":     "precedes",
                "target": self.prev_sibling_occurrence_id,
                "weight": 0.8,
            })

        # V2: scope containment (outer → inner, but expressed as inner member_of outer)
        for scope_name in self.scope_stack:
            rels.append({
                "op":     _SCOPE_OP,
                "target": scope_name,
                "weight": 1.5,
            })

        # V2: heading section containment
        for heading_text in self.heading_trail:
            rels.append({
                "op":     _SECTION_OP,
                "target": heading_text,
                "weight": 1.2,
            })

        # V2: cross-reference links
        for ref in self.cross_refs:
            rels.append({
                "op":     _REFERENCE_OP,
                "target": ref,
                "weight": 0.9,
            })

        return rels

    # ── semantic_surface override ─────────────────────────────────────────

    @property
    def semantic_surface(self) -> Dict[str, Any]:
        """Embedding-space data — populated once the Emitter embeds the hunk."""
        return {
            "embedding":      self.embedding,
            "attention_weight": self.attention_weight,
        }
