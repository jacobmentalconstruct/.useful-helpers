"""peg_eng.py — Regex/PEG-based engine for Markdown and structured documents.

Surface populator for the STRUCTURAL + GRAMMATICAL surfaces.

Structural surface fields populated:
    structural_path, heading_trail, sibling_index, sibling_count,
    document_position, parent_occurrence_id, prev_sibling_occurrence_id

Grammatical surface fields populated:
    node_kind, layer_type ("CST"), cross_refs

Statistical surface fields populated (partial):
    extraction_engine = "PEGEngine"
    extraction_confidence = 0.9
    split_reason = "heading_boundary" | "paragraph_boundary"

V1 reference: _BDHyperNodeSPLITTER/src/engines/peg_eng.py (4-layer pipeline)
V1 bugs fixed:
    - Heading TEXT discarded after slug creation. V2 tracks heading_trail:
      list of heading TEXT strings (not slugs) from root to current scope.
    - cross_refs not extracted. V2 extracts all [text](url) link targets.
    - sibling_count not stored. V2 pre-counts siblings per heading scope.
    - document_position not tracked. V2 computes char_offset / total_bytes.
    - split_reason not set. V2 sets "heading_boundary" or "paragraph_boundary".
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from core.contract.hyperhunk import HyperHunk
from core.signal_profile import (
    ListRepresentationProfile,
    ReferenceExtractionProfile,
    SplitterSignalProfile,
    StructuredTextProfile,
)

# ── Constants ─────────────────────────────────────────────────────────────

_HANDLED_EXTENSIONS = frozenset({".md", ".markdown", ".rst"})

_NODE_KIND_MAP: Dict[str, str] = {
    "heading":     "md_heading",
    "fenced_code": "md_code_block",
    "literal_block": "md_code_block",
    "paragraph":   "md_paragraph",
    "blockquote":  "md_blockquote",
    "list":        "md_list",
    "list_item":   "md_list_item",
    "table":       "md_table",
    "hr":          "md_hr",
}

_CROSS_REF_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
_RST_ROLE_REF_RE = re.compile(r':(?P<role>[a-zA-Z_][\w-]*):`(?P<body>[^`]+)`')
_RST_INLINE_LINK_RE = re.compile(r'`(?P<label>[^`<]+?)\s*<(?P<target>[^>]+)>`_')
_GRAMMAR_SYMBOL_RE = re.compile(r'``(?P<symbol>[A-Za-z_][A-Za-z0-9_-]{1,63})``')

# ── Layer B: Line Ledger ──────────────────────────────────────────────────

_LINE_PATTERNS = {
    "blank":           re.compile(r'^\s*$'),
    "fence_open":      re.compile(r'^[ ]{0,3}(```+|~~~+)(.*)$'),
    "heading":         re.compile(r'^[ ]{0,3}(#{1,6})\s+(.+)$'),
    "setext_underline": re.compile(r'^[ ]{0,3}([=\-~^"#*])\1{2,}\s*$'),
    "blockquote":      re.compile(r'^[ ]{0,3}>\s?(.*)'),
    "hr":              re.compile(r'^[ ]{0,3}([-*_])(\s*\1){2,}\s*$'),
    "list_bullet":     re.compile(r'^[ ]{0,3}[-*+]\s+(.*)'),
    "list_ordered":    re.compile(r'^[ ]{0,3}\d{1,9}[.)]\s+(.*)'),
    "table_separator": re.compile(r'^[ ]{0,3}\|?[-:|][-| :]+\|?\s*$'),
    "table_row":       re.compile(r'^[ ]{0,3}\|(.+)\|\s*$'),
}


@dataclass
class LineRecord:
    index:    int
    offset:   int
    indent:   int
    raw:      str
    tag:      str
    is_blank: bool


@dataclass
class ReferenceRecord:
    raw: str
    normalized: str
    kind: str
    confidence: float


def _classify_line(line: str) -> str:
    for tag, pattern in _LINE_PATTERNS.items():
        if pattern.match(line):
            return tag
    return "text"


def _measure_indent(line: str) -> int:
    count = 0
    for ch in line:
        if ch == ' ':
            count += 1
        elif ch == '\t':
            count += 4
        else:
            break
    return count


def _build_ledger(text: str) -> List[LineRecord]:
    records: List[LineRecord] = []
    offset = 0
    for i, raw in enumerate(text.split('\n')):
        tag = _classify_line(raw)
        records.append(LineRecord(
            index=i,
            offset=offset,
            indent=_measure_indent(raw),
            raw=raw,
            tag=tag,
            is_blank=(tag == "blank"),
        ))
        offset += len(raw.encode('utf-8')) + 1
    return records


# ── Layer C: Block Resolution ─────────────────────────────────────────────


@dataclass
class Block:
    kind:  str
    lines: List[LineRecord] = field(default_factory=list)
    meta:  Dict[str, Any]   = field(default_factory=dict)

    @property
    def text(self) -> str:
        return '\n'.join(lr.raw for lr in self.lines)

    @property
    def content_text(self) -> str:
        if self.kind == 'blockquote':
            return '\n'.join(
                re.sub(r'^[ ]{0,3}>\s?', '', lr.raw)
                for lr in self.lines
            )
        if self.kind == 'literal_block':
            nonblank = [lr.raw for lr in self.lines if lr.raw.strip()]
            if not nonblank:
                return self.text
            min_indent = min(_measure_indent(raw) for raw in nonblank)
            return '\n'.join(
                raw[min_indent:] if len(raw) >= min_indent else raw
                for raw in (lr.raw for lr in self.lines)
            )
        if self.kind == 'list':
            cleaned = []
            for j, lr in enumerate(self.lines):
                if j == 0:
                    cleaned.append(re.sub(
                        r'^[ ]{0,3}[-*+]\s+|^[ ]{0,3}\d+[.)]\s+', '', lr.raw
                    ))
                else:
                    cleaned.append(lr.raw.lstrip())
            return '\n'.join(cleaned)
        return self.text


def _resolve_containers(ledger: List[LineRecord]) -> List[Block]:
    blocks: List[Block] = []
    i = 0
    n = len(ledger)

    while i < n:
        lr = ledger[i]

        # Indented literal / code block in structured prose
        if lr.indent >= 3 and lr.tag in ("text", "heading"):
            block = Block(kind="literal_block", lines=[lr])
            i += 1
            while i < n and (ledger[i].indent >= 3 or ledger[i].is_blank):
                block.lines.append(ledger[i])
                i += 1
            blocks.append(block)
            continue

        # Fenced code
        if lr.tag == "fence_open":
            m = _LINE_PATTERNS["fence_open"].match(lr.raw)
            fc = m.group(1)[0]
            fl = len(m.group(1))
            lang = m.group(2).strip()
            block = Block(
                kind="fenced_code",
                lines=[lr],
                meta={"lang": lang, "fence_char": fc, "fence_len": fl},
            )
            i += 1
            while i < n:
                lr2 = ledger[i]
                block.lines.append(lr2)
                if re.match(rf'^[ ]{{0,3}}{re.escape(fc)}{{{fl},}}\s*$', lr2.raw):
                    i += 1
                    break
                i += 1
            blocks.append(block)
            continue

        # ATX heading
        if lr.tag == "heading":
            m = _LINE_PATTERNS["heading"].match(lr.raw)
            blocks.append(Block(
                kind="heading",
                lines=[lr],
                meta={"level": len(m.group(1)), "title": m.group(2).strip()},
            ))
            i += 1
            continue

        # Setext / reStructuredText-style heading
        if (
            lr.tag in ("text", "list_ordered")
            and i + 1 < n
            and ledger[i + 1].tag == "setext_underline"
            and lr.raw.strip()
        ):
            underline = ledger[i + 1].raw.strip()
            level = _setext_level(underline[0])
            blocks.append(Block(
                kind="heading",
                lines=[lr, ledger[i + 1]],
                meta={"level": level, "title": lr.raw.strip()},
            ))
            i += 2
            continue

        # Horizontal rule
        if lr.tag == "hr":
            blocks.append(Block(kind="hr", lines=[lr]))
            i += 1
            continue

        # Blockquote
        if lr.tag == "blockquote":
            block = Block(kind="blockquote", lines=[lr])
            i += 1
            while i < n and (
                ledger[i].tag == "blockquote"
                or (ledger[i].tag == "text" and not ledger[i].is_blank)
            ):
                block.lines.append(ledger[i])
                i += 1
            blocks.append(block)
            continue

        # Table
        if lr.tag in ("table_row", "table_separator"):
            block = Block(kind="table", lines=[lr])
            i += 1
            while i < n and ledger[i].tag in ("table_row", "table_separator"):
                block.lines.append(ledger[i])
                i += 1
            blocks.append(block)
            continue

        # List
        if lr.tag in ("list_bullet", "list_ordered"):
            block = Block(
                kind="list",
                lines=[lr],
                meta={"ordered": lr.tag == "list_ordered"},
            )
            i += 1
            while i < n:
                lr2 = ledger[i]
                if lr2.tag in ("list_bullet", "list_ordered"):
                    block.lines.append(lr2)
                    i += 1
                elif lr2.tag == "text" and lr2.indent >= 2:
                    block.lines.append(lr2)
                    i += 1
                elif lr2.is_blank:
                    if i + 1 < n and ledger[i + 1].tag in ("list_bullet", "list_ordered"):
                        block.lines.append(lr2)
                        i += 1
                    else:
                        break
                else:
                    break
            blocks.append(block)
            continue

        # Blank
        if lr.is_blank:
            i += 1
            continue

        # Paragraph (default)
        block = Block(kind="paragraph", lines=[lr])
        i += 1
        while i < n and ledger[i].tag == "text" and not ledger[i].is_blank:
            block.lines.append(ledger[i])
            i += 1
        blocks.append(block)

    return blocks


# ── Layer D: Leaf parsers ─────────────────────────────────────────────────


def _parse_leaf_code(text: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    lines = text.split('\n')
    if len(lines) >= 2:
        fc = meta.get("fence_char", "`")
        content_lines = (
            lines[1:-1]
            if lines[-1].strip() and lines[-1].strip()[0] == fc
            else lines[1:]
        )
    else:
        content_lines = lines
    return {"code": '\n'.join(content_lines), "lang": meta.get("lang", "")}


def _slugify(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')


def _normalize_reference(raw: str, mode: str) -> str:
    text = raw.strip().strip("`'\"")
    if mode == "none":
        return text.lower()

    text = text.lower().replace("\\", "/")
    if "<" in text and ">" in text:
        inner = re.search(r"<([^>]+)>", text)
        if inner:
            text = inner.group(1)
    text = text.split("#", 1)[0].strip()
    text = text.lstrip("./")
    if text.endswith((".txt", ".rst", ".md")):
        text = text.rsplit(".", 1)[0]
    if "/" in text:
        parts = [_slugify(part) for part in text.split("/") if part.strip()]
        text = "/".join(part for part in parts if part)
    else:
        text = _slugify(text)
    return text


def _collect_reference_records(
    content: str,
    profile: ReferenceExtractionProfile,
) -> List[ReferenceRecord]:
    if not profile.enabled:
        return []

    records: List[ReferenceRecord] = []
    seen: set[tuple[str, str, str]] = set()

    def _add(raw: str, kind: str, confidence: float) -> None:
        normalized = _normalize_reference(raw, profile.normalization_mode)
        if not normalized and profile.normalization_mode != "none":
            return
        if confidence < profile.minimum_reference_quality:
            return
        key = (raw.strip(), normalized, kind)
        if key in seen:
            return
        seen.add(key)
        records.append(
            ReferenceRecord(
                raw=raw.strip(),
                normalized=normalized,
                kind=kind,
                confidence=round(confidence, 3),
            )
        )

    for match in _CROSS_REF_RE.finditer(content):
        _add(match.group(2), "markdown_link", 0.95)

    for match in _RST_INLINE_LINK_RE.finditer(content):
        _add(match.group("target"), "rst_inline_link", 0.9)

    for match in _RST_ROLE_REF_RE.finditer(content):
        role = match.group("role").lower()
        body = match.group("body").strip()
        target = body.split("<", 1)[-1].rstrip(">").strip() if "<" in body and ">" in body else body
        confidence = 0.8
        if role in {"doc", "ref"}:
            confidence = 0.95
        elif role in {"term", "token"}:
            confidence = 0.7
        _add(target, f"rst_{role}", confidence)

    for match in _GRAMMAR_SYMBOL_RE.finditer(content):
        symbol = match.group("symbol")
        if "_" in symbol or symbol.islower():
            _add(symbol, "grammar_symbol", 0.45)

    return records


def _infer_list_section_reference(
    content: str,
    profile: ReferenceExtractionProfile,
    *,
    list_role: str,
) -> List[ReferenceRecord]:
    if not profile.enabled or not list_role.endswith("_item"):
        return []

    first_line = content.splitlines()[0].strip()
    first_line = re.sub(r'^(?:[-*+]|(?:\d+[.)]))\s+', '', first_line)
    if len(first_line) > 120:
        return []

    match = re.match(r'^(?P<number>\d+(?:\.\d+){0,3})\.?\s+(?P<title>.+)$', first_line)
    if not match:
        return []

    title = match.group("title").strip(" .")
    if len(title) < 3:
        return []
    normalized = _normalize_reference(title, profile.normalization_mode)
    if not normalized:
        return []
    confidence = 0.62 if "." in match.group("number") else 0.7
    if confidence < profile.minimum_reference_quality:
        return []
    return [
        ReferenceRecord(
            raw=title,
            normalized=normalized,
            kind="list_section_title",
            confidence=round(confidence, 3),
        )
    ]


def _summarize_references(
    content: str,
    profile: ReferenceExtractionProfile,
    *,
    list_role: str = "",
) -> Dict[str, Any]:
    records = _collect_reference_records(content, profile)
    records.extend(_infer_list_section_reference(content, profile, list_role=list_role))
    deduped: List[ReferenceRecord] = []
    seen: set[tuple[str, str, str]] = set()
    for record in records:
        key = (record.raw, record.normalized, record.kind)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(record)
    records = deduped
    raw_refs = [r.raw for r in records] if profile.keep_raw_refs else []
    normalized_refs = []
    for record in records:
        if record.normalized and record.normalized not in normalized_refs:
            normalized_refs.append(record.normalized)
    kinds = sorted({record.kind for record in records})
    confidence = max((record.confidence for record in records), default=0.0)
    return {
        "cross_refs": raw_refs,
        "normalized_cross_refs": normalized_refs,
        "reference_kinds": kinds,
        "reference_confidence": confidence,
        "reference_records": [
            {
                "raw": record.raw,
                "normalized": record.normalized,
                "kind": record.kind,
                "confidence": record.confidence,
            }
            for record in records
        ],
    }


def _setext_level(ch: str) -> int:
    return {
        "=": 1,
        "-": 2,
        "~": 3,
        "^": 4,
        '"': 5,
        "#": 6,
        "*": 1,
    }.get(ch, 2)


def _effective_count(threshold: int, sensitivity: float) -> int:
    return max(1, round(threshold / max(sensitivity, 0.1)))


def _looks_like_structured_text(text: str, profile: StructuredTextProfile) -> bool:
    """Heuristic gate for `.txt` structured prose like reST docs.

    We keep plain text on the fallback path and only promote `.txt` into PEG
    when there is strong evidence of heading-based structure.
    """
    lines = text.splitlines()
    heading_pairs = 0
    directives = 0
    list_like_lines = 0
    indented_lines = 0

    for i, line in enumerate(lines[:250]):
        stripped = line.strip()
        if stripped.startswith(".. "):
            directives += 1
        if re.match(r'^[ ]{0,3}[*+-]\s+\S', line):
            list_like_lines += 1
        if re.match(r'^[ ]{3,}\S', line):
            indented_lines += 1
        if not stripped:
            continue
        if i + 1 >= len(lines):
            continue
        underline = lines[i + 1].strip()
        if (
            len(stripped) <= 120
            and _LINE_PATTERNS["setext_underline"].match(underline)
        ):
            heading_pairs += 1
            if heading_pairs >= _effective_count(profile.heading_pair_threshold, profile.txt_promotion_sensitivity):
                return True

    heading_gate = _effective_count(profile.heading_pair_threshold, profile.txt_promotion_sensitivity)
    list_gate = _effective_count(profile.list_heavy_threshold, profile.txt_promotion_sensitivity)
    indent_gate = _effective_count(profile.indented_block_threshold, profile.txt_promotion_sensitivity)

    if heading_pairs >= 1 and directives >= 1:
        return True
    if heading_pairs >= heading_gate - 1 and list_like_lines >= list_gate:
        return True
    if heading_pairs >= heading_gate - 1 and indented_lines >= indent_gate:
        return True
    return False


# ── Pre-count siblings per scope ──────────────────────────────────────────


def _precount_siblings(blocks: List[Block]) -> List[int]:
    """Pre-count non-heading blocks per heading scope (parallel to blocks list)."""
    scope_ids: List[int] = []
    scope_id = 0
    for block in blocks:
        if block.kind == "heading":
            scope_id += 1
        scope_ids.append(scope_id)

    counts: Counter = Counter()
    for block, sid in zip(blocks, scope_ids):
        if block.kind != "heading":
            counts[sid] += 1

    result: List[int] = []
    for block, sid in zip(blocks, scope_ids):
        if block.kind == "heading":
            result.append(counts.get(sid + 1, 0))
        else:
            result.append(counts.get(sid, 0))
    return result


# ── Layer E/F: Emission ───────────────────────────────────────────────────


def _soft_chunk_text(text: str, max_chars: int) -> List[str]:
    if len(text) <= max_chars:
        return [text]

    parts: List[str] = []
    remaining = text.strip()
    while len(remaining) > max_chars:
        split_at = remaining.rfind(" ", 0, max_chars)
        if split_at < max_chars // 2:
            split_at = max_chars
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    if remaining:
        parts.append(remaining)
    return [part for part in parts if part]


def _build_list_items(block: Block, profile: ListRepresentationProfile) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    current_lines: List[LineRecord] = []
    current_marker = ""
    current_depth = 0
    current_ordered = bool(block.meta.get("ordered", False))

    def _flush() -> None:
        nonlocal current_lines, current_marker, current_depth, current_ordered
        if not current_lines:
            return
        raw_lines = [lr.raw for lr in current_lines]
        first = raw_lines[0]
        marker_match = re.match(r'^([ ]{0,3}(?:[-*+]|\d+[.)]))\s+(.*)$', first)
        body_lines: List[str] = []
        if marker_match:
            current_marker = marker_match.group(1).strip()
            first_body = marker_match.group(2)
            body_lines.append(first if profile.preserve_markers else first_body)
            current_ordered = bool(re.match(r'^\d+[.)]$', current_marker))
            current_depth = max(0, current_lines[0].indent // 2)
        else:
            body_lines.append(first.lstrip())
        body_lines.extend(line.lstrip() for line in raw_lines[1:])
        text = "\n".join(body_lines).strip()
        if not text:
            current_lines = []
            return
        parts = _soft_chunk_text(text, profile.max_list_item_length)
        for idx, part in enumerate(parts):
            items.append({
                "content": part,
                "lines": list(current_lines),
                "marker": current_marker,
                "depth": current_depth,
                "ordered": current_ordered,
                "fragment_index": idx,
                "fragment_count": len(parts),
            })
        current_lines = []
        current_marker = ""
        current_depth = 0
        current_ordered = bool(block.meta.get("ordered", False))

    for lr in block.lines:
        if lr.tag in ("list_bullet", "list_ordered"):
            _flush()
            current_lines = [lr]
        else:
            current_lines.append(lr)
    _flush()
    return items


def _emit_blocks(
    blocks: List[Block],
    origin_id: str,
    metadata: Dict[str, Any],
    total_bytes: int,
    signal_profile: SplitterSignalProfile,
) -> Iterator[HyperHunk]:
    """Emit HyperHunks from resolved blocks with full v2 surface population."""
    scope_sibling_counts = _precount_siblings(blocks)

    # V2: heading trail — stack of (level, text) tuples
    heading_stack: List[Tuple[int, str]] = []

    current_path = "doc"
    prev_occ: Optional[str] = None
    sibling_idx = 0
    scope_sibling_count = scope_sibling_counts[0] if scope_sibling_counts else 0

    for block_i, block in enumerate(blocks):
        node_kind = _NODE_KIND_MAP.get(block.kind, "md_paragraph")

        if block.kind == "heading":
            level = block.meta.get("level", 1)
            title = block.meta.get("title", "")

            # V2: maintain TEXT trail — pop levels >= current, push new
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))

            # Build nested structural path from heading stack
            path_parts = ["doc"] + [
                "h{}_{}".format(
                    lvl,
                    re.sub(r'[^a-z0-9]+', '_', txt.lower()).strip('_')[:30]
                )
                for lvl, txt in heading_stack
            ]
            current_path = "/".join(path_parts)

            # Reset scope state
            sibling_idx = 0
            prev_occ = None
            scope_sibling_count = scope_sibling_counts[block_i]
            split_reason = "heading_boundary"
        else:
            split_reason = "paragraph_boundary"

        # Content
        if block.kind == "heading":
            content = block.meta.get("title", "").strip()
            block_meta = {**metadata, **block.meta}
        elif block.kind == "fenced_code":
            parsed = _parse_leaf_code(block.text, block.meta)
            content = parsed["code"].strip()
            block_meta = {**metadata, **block.meta}
        else:
            content = block.content_text.strip()
            block_meta = {**metadata, **block.meta}

        if not content:
            continue

        if block.lines:
            block_meta["start_line"] = block.lines[0].index + 1
            block_meta["end_line"] = block.lines[-1].index + 1

        byte_offset = block.lines[0].offset if block.lines else 0
        doc_pos = round(byte_offset / total_bytes, 4) if total_bytes > 0 else 0.0
        heading_trail = [txt for _, txt in heading_stack]

        emission_units: List[Dict[str, Any]] = [{
            "content": content,
            "node_kind": node_kind,
            "structural_path": current_path,
            "metadata": block_meta,
            "cross_refs_payload": _summarize_references(
                content,
                signal_profile.reference_extraction_profile,
                list_role="list_block" if block.kind == "list" else "",
            ),
            "document_position": doc_pos,
            "list_role": "list_block" if block.kind == "list" else "",
            "list_depth": max(0, block.lines[0].indent // 2) if block.lines else 0,
            "split_reason": split_reason,
        }]

        if (
            block.kind == "list"
            and signal_profile.list_representation_profile.emit_list_items
        ):
            emission_units = []
            items = _build_list_items(block, signal_profile.list_representation_profile)
            for item_idx, item in enumerate(items):
                item_path = current_path
                if signal_profile.list_representation_profile.inherit_heading_ancestry:
                    item_path = f"{current_path}/li_{item_idx + 1}"
                item_meta = {
                    **block_meta,
                    "list_marker": item["marker"],
                    "list_ordered": item["ordered"],
                    "list_depth": item["depth"],
                    "list_item_fragment_index": item["fragment_index"],
                    "list_item_fragment_count": item["fragment_count"],
                    "start_line": item["lines"][0].index + 1,
                    "end_line": item["lines"][-1].index + 1,
                }
                item_offset = item["lines"][0].offset if item["lines"] else byte_offset
                item_doc_pos = round(item_offset / total_bytes, 4) if total_bytes > 0 else 0.0
                emission_units.append({
                    "content": item["content"],
                    "node_kind": "md_list_item",
                    "structural_path": item_path,
                    "metadata": item_meta,
                    "cross_refs_payload": _summarize_references(
                        item["content"],
                        signal_profile.reference_extraction_profile,
                        list_role="ordered_item" if item["ordered"] else "unordered_item",
                    ),
                    "document_position": item_doc_pos,
                    "list_role": "ordered_item" if item["ordered"] else "unordered_item",
                    "list_depth": item["depth"],
                    "split_reason": split_reason,
                })

        for unit in emission_units:
            refs = unit["cross_refs_payload"]
            unit_meta = dict(unit["metadata"])
            if refs["reference_records"]:
                unit_meta["reference_records"] = refs["reference_records"]

            hunk = HyperHunk(
                content=unit["content"],
                origin_id=origin_id,
                layer_type="CST",
                node_kind=unit["node_kind"],
                structural_path=unit["structural_path"],
                sibling_index=sibling_idx,
                metadata=unit_meta,
                parent_occurrence_id=None,
                prev_sibling_occurrence_id=prev_occ,
                heading_trail=heading_trail,
                sibling_count=scope_sibling_count,
                document_position=unit["document_position"],
                cross_refs=refs["cross_refs"],
                normalized_cross_refs=refs["normalized_cross_refs"],
                reference_kinds=refs["reference_kinds"],
                reference_confidence=refs["reference_confidence"],
                list_role=unit["list_role"],
                list_depth=unit["list_depth"],
                extraction_engine="PEGEngine",
                extraction_confidence=0.9,
                split_reason=unit["split_reason"],
            )

            prev_occ = hunk.occurrence_id
            sibling_idx += 1
            yield hunk


# ── Engine class ──────────────────────────────────────────────────────────


class PEGEngine:
    """Regex/PEG-based Markdown parser. Populates structural + grammatical surfaces."""

    def __init__(self, signal_profile: SplitterSignalProfile | None = None) -> None:
        self.signal_profile = signal_profile or SplitterSignalProfile.default()

    def can_handle(self, origin_id: str, text: str | None = None) -> bool:
        suffix = Path(origin_id).suffix.lower()
        if suffix in _HANDLED_EXTENSIONS:
            return True
        if suffix == ".txt" and text:
            return _looks_like_structured_text(
                text,
                self.signal_profile.structured_text_profile,
            )
        return False

    def parse(
        self,
        text: str,
        origin_id: str,
        metadata: dict | None = None,
    ) -> Iterator[HyperHunk]:
        """Parse Markdown into structurally-aware HyperHunks.

        4-layer pipeline:
          B. _build_ledger       — per-line classification
          C. _resolve_containers — block resolution with state machine
          D. leaf parsers        — code fence content extraction
          E/F. _emit_blocks      — HyperHunk emission with v2 surface population
        """
        meta = dict(metadata or {})
        total_bytes = len(text.encode('utf-8'))
        ledger = _build_ledger(text)
        blocks = _resolve_containers(ledger)
        yield from _emit_blocks(
            blocks,
            origin_id,
            meta,
            total_bytes,
            self.signal_profile,
        )
