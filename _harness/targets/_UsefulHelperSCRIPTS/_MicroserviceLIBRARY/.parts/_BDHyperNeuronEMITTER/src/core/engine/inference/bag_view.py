"""bag_view.py — user-facing Bag of Evidence shaping.

Ownership: core/engine/inference/bag_view.py
    Converts the internal retrieval output into a richer, external-agent-friendly
    Bag of Evidence payload. The bag stays faithful to the current deterministic
    retrieval path while adding:
        - item metadata enrichment from SQLite
        - item / group / whole-bag summary lenses
        - pullback-ready full text for selected evidence items

Boundary rule: READS from the Cold Artifact and retrieval pipeline only.
It never writes to disk.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .provider import query as run_query


def _normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def _sentence_summary(text: str, limit: int = 220) -> str:
    compact = _normalize_whitespace(text)
    if not compact:
        return ""

    for marker in (". ", "! ", "? "):
        idx = compact.find(marker)
        if 0 <= idx < limit:
            return compact[: idx + 1].strip()

    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def _load_item_rows(conn: sqlite3.Connection, occurrence_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    ids = list(dict.fromkeys(occurrence_ids))
    if not ids:
        return {}

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT o.occurrence_id, o.origin_id, o.structural_path,
               c.hunk_id, c.node_kind, c.content, c.attention_weight, c.static_mass
        FROM occurrence_nodes o
        JOIN content_nodes c ON c.hunk_id = o.hunk_id
        WHERE o.occurrence_id IN ({placeholders})
        """,
        ids,
    ).fetchall()

    payload: dict[str, dict[str, Any]] = {}
    for row in rows:
        content = row[5] or ""
        payload[str(row[0])] = {
            "occurrence_id": str(row[0]),
            "origin_id": str(row[1]),
            "structural_path": str(row[2] or ""),
            "hunk_id": str(row[3]),
            "node_kind": str(row[4]),
            "content": content,
            "content_snippet": _sentence_summary(content, limit=180),
            "item_summary": _sentence_summary(content, limit=220),
            "attention_weight": float(row[6]),
            "static_mass": int(row[7]),
        }
    return payload


def _load_relation_hints(
    conn: sqlite3.Connection,
    occurrence_ids: Iterable[str],
    *,
    per_item_limit: int = 3,
) -> dict[str, list[dict[str, Any]]]:
    ids = list(dict.fromkeys(occurrence_ids))
    if not ids:
        return {}

    placeholders = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""
        SELECT source_occ_id, target_occ_id, op, weight, routing_profile, interaction_mode
        FROM relations
        WHERE source_occ_id IN ({placeholders}) OR target_occ_id IN ({placeholders})
        ORDER BY weight DESC
        """,
        ids + ids,
    ).fetchall()

    hints: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        source_occ_id = str(row[0])
        target_occ_id = str(row[1])
        op = str(row[2])
        weight = float(row[3])
        interaction_mode = str(row[5] or "")
        try:
            routing_profile = json.loads(row[4] or "{}")
        except json.JSONDecodeError:
            routing_profile = {}

        for occ_id, direction, other_occ_id in (
            (source_occ_id, "outgoing", target_occ_id),
            (target_occ_id, "incoming", source_occ_id),
        ):
            if occ_id not in ids:
                continue
            bucket = hints[occ_id]
            if len(bucket) >= per_item_limit:
                continue
            bucket.append(
                {
                    "direction": direction,
                    "op": op,
                    "other_occurrence_id": other_occ_id,
                    "weight": round(weight, 4),
                    "interaction_mode": interaction_mode,
                    "routing_profile": routing_profile,
                }
            )

    return hints


def _make_group_key(item: dict[str, Any], group_by: str) -> str:
    if group_by == "node_kind":
        return item["node_kind"]
    if group_by == "structural_root":
        path = item["structural_path"]
        return path.split("/", 1)[0] if path else "(no-structural-path)"
    return item["origin_id"]


def _group_summary(label: str, items: list[dict[str, Any]]) -> str:
    top = max(items, key=lambda x: x["activation"])
    kinds = Counter(item["node_kind"] for item in items)
    top_kind = kinds.most_common(1)[0][0] if kinds else "unknown"
    return (
        f"{len(items)} items in {label}. "
        f"Strongest activation {top['activation']:.3f}. "
        f"Most common kind: {top_kind}. "
        f"Representative item: {top['item_summary']}"
    )


def _bag_summary(query_text: str, items: list[dict[str, Any]], groups: list[dict[str, Any]]) -> str:
    if not items:
        return f'No evidence items were surfaced for query "{query_text}".'

    origins = Counter(item["origin_id"] for item in items).most_common(3)
    node_kinds = Counter(item["node_kind"] for item in items).most_common(3)
    origins_text = ", ".join(f"{name} ({count})" for name, count in origins) or "none"
    kinds_text = ", ".join(f"{name} ({count})" for name, count in node_kinds) or "none"
    return (
        f'{len(items)} evidence items surfaced for "{query_text}" across {len(groups)} groups. '
        f"Top sources: {origins_text}. "
        f"Top node kinds: {kinds_text}."
    )


def build_bag(
    *,
    query_text: str,
    db_path: str | Path,
    top_k: int = 12,
    hop_limit: int = 2,
    decay: float = 0.9,
    group_by: str = "origin_id",
    include_full_text: bool = False,
    pull_occurrence_ids: list[str] | None = None,
    embedder_override: str | None = None,
    sentence_model: str | None = None,
) -> dict[str, Any]:
    db_path = Path(db_path)
    results = run_query(
        query_text,
        db_path=db_path,
        top_k=top_k,
        hop_limit=hop_limit,
        decay=decay,
        embedder_override=embedder_override,
        sentence_model=sentence_model,
    )

    occurrence_ids = [result.occurrence_id for result in results]
    conn = sqlite3.connect(str(db_path))
    try:
        item_rows = _load_item_rows(conn, occurrence_ids)
        relation_hints = _load_relation_hints(conn, occurrence_ids)
    finally:
        conn.close()

    items: list[dict[str, Any]] = []
    for result in results:
        row = item_rows.get(result.occurrence_id, {})
        item = {
            "occurrence_id": result.occurrence_id,
            "activation": round(float(result.activation), 4),
            "hunk_id": result.hunk_id,
            "node_kind": row.get("node_kind", result.node_kind),
            "origin_id": row.get("origin_id", ""),
            "structural_path": row.get("structural_path", ""),
            "content_snippet": row.get("content_snippet", ""),
            "item_summary": row.get("item_summary", ""),
            "attention_weight": float(row.get("attention_weight", result.attention_weight)),
            "static_mass": int(row.get("static_mass", result.static_mass)),
            "why": relation_hints.get(result.occurrence_id, []),
        }
        if include_full_text:
            item["content"] = row.get("content", "")
        items.append(item)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        grouped[_make_group_key(item, group_by)].append(item)

    groups: list[dict[str, Any]] = []
    for label, group_items in grouped.items():
        groups.append(
            {
                "group_key": label,
                "item_count": len(group_items),
                "max_activation": round(max(item["activation"] for item in group_items), 4),
                "summary": _group_summary(label, group_items),
                "occurrence_ids": [item["occurrence_id"] for item in group_items],
            }
        )
    groups.sort(key=lambda group: (-group["max_activation"], -group["item_count"], group["group_key"]))

    pull_targets = set(pull_occurrence_ids or [])
    pullback_items: list[dict[str, Any]] = []
    if pull_targets:
        for item in items:
            if item["occurrence_id"] not in pull_targets:
                continue
            row = item_rows.get(item["occurrence_id"], {})
            pullback_items.append(
                {
                    "occurrence_id": item["occurrence_id"],
                    "origin_id": item["origin_id"],
                    "structural_path": item["structural_path"],
                    "node_kind": item["node_kind"],
                    "pullback_text": row.get("content", ""),
                }
            )

    return {
        "query": query_text,
        "db_path": str(db_path.resolve()),
        "bag_summary": {
            "item_count": len(items),
            "group_count": len(groups),
            "group_by": group_by,
            "summary": _bag_summary(query_text, items, groups),
        },
        "groups": groups,
        "items": items,
        "pullback": {
            "selected_occurrence_ids": [item["occurrence_id"] for item in pullback_items],
            "items": pullback_items,
        },
    }
