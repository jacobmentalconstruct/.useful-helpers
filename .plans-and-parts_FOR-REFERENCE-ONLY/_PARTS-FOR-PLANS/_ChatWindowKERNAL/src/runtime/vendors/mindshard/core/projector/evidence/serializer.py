"""
manifold_kernel.evidence.serializer — JSON serialisation for evidence bags.

Outputs are machine-usable, human-inspectable, and deterministic enough
for regression testing.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict

from .bag import EvidenceBag


def evidence_to_dict(bag: EvidenceBag) -> Dict[str, Any]:
    """Convert an EvidenceBag to a plain dict suitable for JSON serialisation."""
    return {
        "query": bag.query,
        "lens_profile": bag.lens_profile,
        "seed_ids": bag.seed_ids,
        "items": [
            {
                "artifact_id": item.artifact_id,
                "score": item.score,
                "score_components": item.score_components,
                "text_snippet": item.text_snippet,
                "artifact_type": item.artifact_type,
                "depth": item.depth,
                "source": item.source,
            }
            for item in bag.items
        ],
        "relations": [
            {
                "from_id": rel.from_id,
                "to_id": rel.to_id,
                "relation_type": rel.relation_type,
                "weight": rel.weight,
            }
            for rel in bag.relations
        ],
        "stats": asdict(bag.stats) if bag.stats else None,
        "metadata": bag.metadata,
    }


def evidence_to_json(bag: EvidenceBag, indent: int = 2) -> str:
    """Serialise an EvidenceBag to a JSON string."""
    return json.dumps(evidence_to_dict(bag), indent=indent, sort_keys=False)


def evidence_to_summary(bag: EvidenceBag) -> str:
    """Produce a human-readable text summary of the evidence bag."""
    lines = []
    lines.append(f"Evidence Bag for: \"{bag.query}\"")
    lines.append(f"Lens Profile: {bag.lens_profile}")
    lines.append(f"Seeds: {len(bag.seed_ids)}")

    if bag.stats:
        lines.append(f"Projection: {bag.stats.total_nodes_in_projection} nodes, {bag.stats.total_edges_in_projection} edges")
        lines.append(f"Included: {bag.stats.items_included} items (excluded {bag.stats.items_excluded})")
        lines.append(f"Score range: {bag.stats.min_score:.4f} — {bag.stats.max_score:.4f} (mean {bag.stats.mean_score:.4f})")

    lines.append("")
    lines.append("─" * 60)

    for i, item in enumerate(bag.items[:20], 1):
        lines.append(f"\n[{i}] {item.artifact_id}  (score={item.score:.4f}, depth={item.depth}, via={item.source})")
        if item.text_snippet:
            snippet = item.text_snippet.replace("\n", " ")[:120]
            lines.append(f"    {snippet}")

    if len(bag.items) > 20:
        lines.append(f"\n... and {len(bag.items) - 20} more items")

    return "\n".join(lines)
