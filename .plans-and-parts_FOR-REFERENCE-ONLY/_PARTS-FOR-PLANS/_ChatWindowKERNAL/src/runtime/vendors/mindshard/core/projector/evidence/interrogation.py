"""
Grounded Bag Interrogation Layer.

Sits between Evidence Bag retrieval and prompt assembly. Transforms
flat bag items into dimension-aware structured context so the model
receives typed records instead of an undifferentiated text dump.

Design doc: grounded_bag_interrogation_model.md

Key concepts:
  - 5 dimensions: identity, structure, verbatim, semantic, relations
  - Intent classification maps (query, mode, scope) → primary/support dims
  - Typed records are built per bag item using existing metadata (no extra
    model calls)
  - Response anchor constrains the model's answer shape
  - Formatted output replaces to_prompt_block() when interrogation is enabled

NOT responsible for: scoring, packing, transport, model invocation, UI.
"""

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

# ── Standalone mode/scope enums (decoupled from CodeMONKEY) ──────────
# These replicate the subset of TaskMode/TaskScope values that the
# interrogation layer actually references for intent classification.
# Agents using this kernel should map their own task modes to these.

class TaskMode(Enum):
    """Agent task modes relevant to intent classification."""
    CHAT = "chat"
    CLASSIFY = "classify"
    LABEL = "label"
    PATCH = "patch"
    COMMIT_DRAFT = "commit_draft"
    QUERY_REWRITE = "query_rewrite"
    EXPLAIN = "explain"
    GENERIC = "generic"


class TaskScope(Enum):
    """Agent task scopes."""
    LOCAL = "local"
    PROJECT = "project"
    GLOBAL = "global"

logger = logging.getLogger(__name__)

__all__ = [
    "Dimension", "IntentClass", "AnswerType", "IntentProfile",
    "TypedRecord", "ResponseAnchor",
    "classify_intent", "build_typed_records", "build_response_anchor",
    "format_interrogated_context", "interrogate_evidence",
]


# ── Dimensions ────────────────────────────────────────────────────────

class Dimension(Enum):
    """The five evidence dimensions."""
    IDENTITY = "identity"
    STRUCTURE = "structure"
    VERBATIM = "verbatim"
    SEMANTIC = "semantic"
    RELATIONS = "relations"


# ── Intent classification ─────────────────────────────────────────────

class IntentClass(Enum):
    """High-level intent categories derived from query analysis."""
    IDENTITY_QUESTION = "identity_question"
    STRUCTURE_QUESTION = "structure_question"
    VERBATIM_EXPLANATION = "verbatim_explanation"
    RELEVANCE_QUESTION = "relevance_question"
    DEPENDENCY_QUESTION = "dependency_question"
    DESIGN_QUESTION = "design_question"
    GENERAL = "general"


class AnswerType(Enum):
    """Expected shape of the answer."""
    OBJECT_IDENTIFICATION = "object_identification"
    STRUCTURAL_MAP = "structural_map"
    CODE_EXPLANATION = "code_explanation"
    RELEVANCE_JUSTIFICATION = "relevance_justification"
    DEPENDENCY_TRACE = "dependency_trace"
    DESIGN_PROPOSAL = "design_proposal"
    FREE_FORM = "free_form"


@dataclass(frozen=True)
class IntentProfile:
    """Result of intent classification."""
    intent_class: IntentClass
    primary_dimension: Dimension
    support_dimensions: Tuple[Dimension, ...]
    answer_type: AnswerType


# Dimension priority orders per intent class (from the design doc)
_INTENT_DIMENSIONS: Dict[IntentClass, List[Dimension]] = {
    IntentClass.IDENTITY_QUESTION: [
        Dimension.IDENTITY, Dimension.STRUCTURE, Dimension.VERBATIM,
        Dimension.RELATIONS, Dimension.SEMANTIC,
    ],
    IntentClass.STRUCTURE_QUESTION: [
        Dimension.STRUCTURE, Dimension.IDENTITY, Dimension.RELATIONS,
        Dimension.VERBATIM, Dimension.SEMANTIC,
    ],
    IntentClass.VERBATIM_EXPLANATION: [
        Dimension.VERBATIM, Dimension.IDENTITY, Dimension.STRUCTURE,
        Dimension.SEMANTIC, Dimension.RELATIONS,
    ],
    IntentClass.RELEVANCE_QUESTION: [
        Dimension.SEMANTIC, Dimension.VERBATIM, Dimension.RELATIONS,
        Dimension.IDENTITY, Dimension.STRUCTURE,
    ],
    IntentClass.DEPENDENCY_QUESTION: [
        Dimension.RELATIONS, Dimension.STRUCTURE, Dimension.IDENTITY,
        Dimension.VERBATIM, Dimension.SEMANTIC,
    ],
    IntentClass.DESIGN_QUESTION: [
        Dimension.RELATIONS, Dimension.SEMANTIC, Dimension.STRUCTURE,
        Dimension.VERBATIM, Dimension.IDENTITY,
    ],
    IntentClass.GENERAL: [
        Dimension.SEMANTIC, Dimension.VERBATIM, Dimension.IDENTITY,
        Dimension.STRUCTURE, Dimension.RELATIONS,
    ],
}

_INTENT_ANSWER_TYPES: Dict[IntentClass, AnswerType] = {
    IntentClass.IDENTITY_QUESTION: AnswerType.OBJECT_IDENTIFICATION,
    IntentClass.STRUCTURE_QUESTION: AnswerType.STRUCTURAL_MAP,
    IntentClass.VERBATIM_EXPLANATION: AnswerType.CODE_EXPLANATION,
    IntentClass.RELEVANCE_QUESTION: AnswerType.RELEVANCE_JUSTIFICATION,
    IntentClass.DEPENDENCY_QUESTION: AnswerType.DEPENDENCY_TRACE,
    IntentClass.DESIGN_QUESTION: AnswerType.DESIGN_PROPOSAL,
    IntentClass.GENERAL: AnswerType.FREE_FORM,
}

# Keywords for rule-based intent classification
_IDENTITY_KEYWORDS = {
    "what file", "which file", "what module", "which module",
    "what class", "which class", "what function", "which function",
    "what is this", "identify", "what object", "file name",
    "filename", "module name",
}
_STRUCTURE_KEYWORDS = {
    "where does", "where is", "how is.*organized", "parent",
    "child", "directory", "folder", "package", "tree",
    "structure", "layout", "hierarchy",
}
_RELEVANCE_KEYWORDS = {
    "why was", "why is.*related", "why.*retrieved", "relevance",
    "how is.*related", "connection to query",
}
_DEPENDENCY_KEYWORDS = {
    "depends on", "dependency", "import", "imports",
    "calls", "caller", "references", "connects",
    "bridge", "linked", "relationship",
}
_DESIGN_KEYWORDS = {
    "how would", "extend", "refactor", "architecture",
    "design", "improve", "redesign", "proposal",
}


def classify_intent(
    query: str,
    mode: TaskMode,
    scope: TaskScope,
) -> IntentProfile:
    """Classify the user's intent to determine dimension priorities.

    Uses rule-based keyword matching plus mode/scope hints.
    No model inference required.

    Args:
        query: The user's raw query text.
        mode: The selected task mode.
        scope: The selected task scope.

    Returns:
        An IntentProfile with primary dimension, support dimensions,
        and expected answer type.
    """
    query = query or ""
    q_lower = query.lower()

    # Mode-based shortcuts
    if mode == TaskMode.CLASSIFY or mode == TaskMode.LABEL:
        intent = IntentClass.IDENTITY_QUESTION
    elif mode == TaskMode.PATCH:
        intent = IntentClass.VERBATIM_EXPLANATION
    elif mode == TaskMode.COMMIT_DRAFT:
        intent = IntentClass.VERBATIM_EXPLANATION
    elif mode == TaskMode.QUERY_REWRITE:
        intent = IntentClass.RELEVANCE_QUESTION
    else:
        # Keyword-based classification
        intent = _classify_by_keywords(q_lower)

    dims = _INTENT_DIMENSIONS[intent]
    answer_type = _INTENT_ANSWER_TYPES[intent]

    return IntentProfile(
        intent_class=intent,
        primary_dimension=dims[0],
        support_dimensions=tuple(dims[1:3]),  # top 2 support dims
        answer_type=answer_type,
    )


def _classify_by_keywords(q_lower: str) -> IntentClass:
    """Score query against keyword sets and pick the best intent class."""
    scores: Dict[IntentClass, int] = {
        IntentClass.IDENTITY_QUESTION: 0,
        IntentClass.STRUCTURE_QUESTION: 0,
        IntentClass.RELEVANCE_QUESTION: 0,
        IntentClass.DEPENDENCY_QUESTION: 0,
        IntentClass.DESIGN_QUESTION: 0,
    }

    for intent_class, keyword_set in (
        (IntentClass.IDENTITY_QUESTION, _IDENTITY_KEYWORDS),
        (IntentClass.STRUCTURE_QUESTION, _STRUCTURE_KEYWORDS),
        (IntentClass.RELEVANCE_QUESTION, _RELEVANCE_KEYWORDS),
        (IntentClass.DEPENDENCY_QUESTION, _DEPENDENCY_KEYWORDS),
        (IntentClass.DESIGN_QUESTION, _DESIGN_KEYWORDS),
    ):
        for kw in keyword_set:
            try:
                if re.search(kw, q_lower):
                    scores[intent_class] += 1
            except re.error:
                # Malformed pattern — fall back to plain substring match
                if kw in q_lower:
                    scores[intent_class] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        # No keyword hits — check for explain/what patterns
        if re.search(r"what does|explain|how does|tell me about", q_lower):
            return IntentClass.VERBATIM_EXPLANATION
        return IntentClass.GENERAL

    return best


# ── Typed records ─────────────────────────────────────────────────────

@dataclass
class IdentityRecord:
    """Who/what is this evidence item."""
    node_id: Optional[int]
    object_name: str
    object_type: str        # "file", "function", "class", "chunk", etc.
    canonical_path: str     # source_ref or parsed path
    file_extension: str


@dataclass
class StructureRecord:
    """Where this item lives in the project."""
    parent_package: str     # directory or module parent
    hierarchy_depth: int    # path component count
    container_hint: str     # "src/core/", "tests/", "evidence_bag/", etc.


@dataclass
class VerbatimRecord:
    """What this item literally contains."""
    content: str
    header_line: str        # first meaningful line
    line_count: int
    is_truncated: bool


@dataclass
class SemanticRecord:
    """Why this item matched the query."""
    score: float
    density: float
    is_neighbor: bool
    match_reason: str       # brief explanation of why it scored


@dataclass
class RelationRecord:
    """How this item connects to other evidence."""
    is_neighbor: bool
    neighbor_source: str    # if neighbor, which seed spawned it
    connection_count: int   # number of explicit connections


@dataclass
class TypedRecord:
    """A bag item transformed into dimension-aware typed records."""
    item_index: int
    identity: Optional[IdentityRecord] = None
    structure: Optional[StructureRecord] = None
    verbatim: Optional[VerbatimRecord] = None
    semantic: Optional[SemanticRecord] = None
    relations: Optional[RelationRecord] = None


def build_typed_records(
    bag_items: list,
    intent: IntentProfile,
) -> List[TypedRecord]:
    """Build typed records for each bag item, filtered by intent dimensions.

    Only populates records for the primary dimension and support dimensions,
    leaving others as None to keep the prompt focused.

    Args:
        bag_items: List of BagItem objects from the evidence bag.
        intent: The classified intent profile.

    Returns:
        A list of TypedRecord, one per bag item.
    """
    active_dims: Set[Dimension] = {intent.primary_dimension}
    active_dims.update(intent.support_dimensions)

    records: List[TypedRecord] = []
    for i, item in enumerate(bag_items):
        record = TypedRecord(item_index=i + 1)

        if Dimension.IDENTITY in active_dims:
            record.identity = _extract_identity(item)

        if Dimension.STRUCTURE in active_dims:
            record.structure = _extract_structure(item)

        if Dimension.VERBATIM in active_dims:
            record.verbatim = _extract_verbatim(item)

        if Dimension.SEMANTIC in active_dims:
            record.semantic = _extract_semantic(item)

        if Dimension.RELATIONS in active_dims:
            record.relations = _extract_relations(item)

        records.append(record)

    return records


def _extract_identity(item) -> IdentityRecord:
    """Extract identity record from a BagItem."""
    source = getattr(item, "source_ref", "") or ""
    kind = getattr(item, "kind", "unknown")

    # Parse object name from source_ref
    name = os.path.basename(source) if source else "unknown"
    ext = os.path.splitext(name)[1] if name else ""

    # Infer object type from kind and extension
    obj_type = kind
    if ext in (".py",):
        obj_type = "python_file"
    elif ext in (".js", ".ts", ".tsx"):
        obj_type = "script_file"
    elif ext in (".md", ".txt", ".rst"):
        obj_type = "document"
    elif ext in (".json", ".yaml", ".yml", ".toml"):
        obj_type = "config_file"

    return IdentityRecord(
        node_id=getattr(item, "node_id", None),
        object_name=name,
        object_type=obj_type,
        canonical_path=source,
        file_extension=ext,
    )


def _extract_structure(item) -> StructureRecord:
    """Extract structure record from a BagItem."""
    source = getattr(item, "source_ref", "") or ""

    # Parse parent package from source path
    parts = source.replace("\\", "/").split("/") if source else []
    parent = "/".join(parts[:-1]) if len(parts) > 1 else ""
    depth = len(parts)

    # Determine container hint
    container = ""
    for known in ("src/core/", "src/panels/", "tests/", "evidence_bag/", "_docs/"):
        if known in source.replace("\\", "/"):
            container = known
            break

    return StructureRecord(
        parent_package=parent,
        hierarchy_depth=depth,
        container_hint=container,
    )


def _extract_verbatim(item) -> VerbatimRecord:
    """Extract verbatim record from a BagItem."""
    content = getattr(item, "content", "") or ""
    lines = content.split("\n")

    # Find first non-empty line as header
    header = ""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            header = stripped[:120]
            break
    if not header and lines:
        header = lines[0].strip()[:120]

    return VerbatimRecord(
        content=content,
        header_line=header,
        line_count=len(lines),
        is_truncated=getattr(item, "is_truncated", False),
    )


def _extract_semantic(item) -> SemanticRecord:
    """Extract semantic record from a BagItem."""
    score = getattr(item, "score", 0.0) or 0.0
    density = getattr(item, "density", 0.0) or 0.0
    is_neighbor = getattr(item, "is_neighbor", False)

    # Build match reason
    if is_neighbor:
        reason = "neighbor expansion from high-scoring seed"
    elif score > 0.5:
        reason = "strong semantic + lexical match"
    elif score > 0.2:
        reason = "moderate semantic match"
    else:
        reason = "weak match, included for coverage"

    return SemanticRecord(
        score=score,
        density=density,
        is_neighbor=is_neighbor,
        match_reason=reason,
    )


def _extract_relations(item) -> RelationRecord:
    """Extract relations record from a BagItem."""
    is_neighbor = getattr(item, "is_neighbor", False)
    source = getattr(item, "source_ref", "") or ""

    return RelationRecord(
        is_neighbor=is_neighbor,
        neighbor_source=source if is_neighbor else "",
        connection_count=0,  # BagItem doesn't carry connection data
    )


# ── Response anchor ───────────────────────────────────────────────────

@dataclass
class ResponseAnchor:
    """Constrains the shape and grounding of the model's response."""
    center_type: str          # "identity", "structure", "semantic", "relational"
    expected_answer_type: str  # from AnswerType
    grounding_rules: List[str]  # injected into system prompt


# Center type mapping
_CENTER_TYPES: Dict[IntentClass, str] = {
    IntentClass.IDENTITY_QUESTION: "identity",
    IntentClass.STRUCTURE_QUESTION: "structure",
    IntentClass.VERBATIM_EXPLANATION: "identity",
    IntentClass.RELEVANCE_QUESTION: "semantic",
    IntentClass.DEPENDENCY_QUESTION: "relational",
    IntentClass.DESIGN_QUESTION: "relational",
    IntentClass.GENERAL: "semantic",
}

# Grounding rules per intent class
_GROUNDING_RULES: Dict[IntentClass, List[str]] = {
    IntentClass.IDENTITY_QUESTION: [
        "Answer must reference specific file paths or object names from the evidence.",
        "Do not infer file structure from summaries when direct identity evidence exists.",
        "If the evidence does not contain the named object, say so explicitly.",
    ],
    IntentClass.STRUCTURE_QUESTION: [
        "Answer must describe the structural position using evidence paths.",
        "Parent/child relationships must come from observed paths, not assumptions.",
        "Do not invent modules or packages not present in the evidence.",
    ],
    IntentClass.VERBATIM_EXPLANATION: [
        "Ground your explanation in the actual code or text provided.",
        "Reference specific lines, functions, or constructs from the evidence.",
        "Do not substitute README summaries for actual code when code is available.",
    ],
    IntentClass.RELEVANCE_QUESTION: [
        "Explain why each cited piece of evidence is relevant to the query.",
        "Distinguish between semantic similarity and structural relevance.",
        "If relevance is weak, acknowledge that clearly.",
    ],
    IntentClass.DEPENDENCY_QUESTION: [
        "Trace actual import/call/reference relationships from the evidence.",
        "Do not invent dependencies not visible in the provided code.",
        "Distinguish observed dependencies from inferred ones.",
    ],
    IntentClass.DESIGN_QUESTION: [
        "Ground design proposals in the observed architecture from evidence.",
        "Clearly separate observed patterns from proposed changes.",
        "Mark each claim as [observed], [inferred], or [proposed].",
    ],
    IntentClass.GENERAL: [
        "Ground your answer in the provided evidence where possible.",
        "If the evidence is insufficient, say so rather than speculating.",
        "Distinguish between what the evidence shows and what you are inferring.",
    ],
}


def build_response_anchor(
    intent: IntentProfile,
    records: List[TypedRecord],
) -> ResponseAnchor:
    """Build a response anchor that constrains the model's answer.

    Args:
        intent: The classified intent profile.
        records: The typed records built from bag items.

    Returns:
        A ResponseAnchor with center type, answer type, and grounding rules.
    """
    center = _CENTER_TYPES.get(intent.intent_class, "semantic")
    rules = list(_GROUNDING_RULES.get(intent.intent_class, []))

    # Add claim classification rule for all non-trivial intents
    if intent.intent_class != IntentClass.GENERAL:
        rules.append(
            "For each substantive claim, indicate whether it is "
            "[observed] (directly in evidence), [inferred] (reasonably "
            "derived), or [proposed] (your suggestion)."
        )

    return ResponseAnchor(
        center_type=center,
        expected_answer_type=intent.answer_type.value,
        grounding_rules=rules,
    )


# ── Structured prompt formatting ─────────────────────────────────────

def format_interrogated_context(
    records: List[TypedRecord],
    anchor: ResponseAnchor,
    intent: IntentProfile,
) -> str:
    """Format typed records + anchor into a structured context block.

    Replaces the flat to_prompt_block() output when interrogation
    is enabled. Groups records by dimension priority and appends
    grounding rules.

    Args:
        records: Typed records from build_typed_records().
        anchor: Response anchor from build_response_anchor().
        intent: The intent profile for ordering.

    Returns:
        Formatted markdown context string for prompt injection.
    """
    sections: List[str] = []

    # Header
    sections.append(
        f"## Evidence ({intent.intent_class.value} — "
        f"primary: {intent.primary_dimension.value})"
    )

    # Build evidence items grouped by primary dimension first
    for i, rec in enumerate(records):
        item_lines = [f"\n### Evidence {rec.item_index}."]

        # Identity block
        if rec.identity:
            ident = rec.identity
            item_lines.append(
                f"**Identity:** `{ident.canonical_path}` "
                f"({ident.object_type})"
            )

        # Structure block
        if rec.structure:
            struct = rec.structure
            if struct.container_hint:
                item_lines.append(
                    f"**Location:** `{struct.parent_package}` "
                    f"(in `{struct.container_hint}`)"
                )
            else:
                item_lines.append(
                    f"**Location:** `{struct.parent_package}` "
                    f"(depth {struct.hierarchy_depth})"
                )

        # Semantic block
        if rec.semantic:
            sem = rec.semantic
            item_lines.append(
                f"**Relevance:** score={sem.score:.3f}, "
                f"density={sem.density:.3f} — {sem.match_reason}"
            )

        # Relations block
        if rec.relations and rec.relations.is_neighbor:
            item_lines.append(
                f"**Relation:** neighbor node "
                f"(expanded from `{rec.relations.neighbor_source}`)"
            )

        # Verbatim block (last — it's the longest)
        if rec.verbatim:
            verb = rec.verbatim
            trunc_note = " [truncated]" if verb.is_truncated else ""
            item_lines.append(
                f"**Content** ({verb.line_count} lines{trunc_note}):"
            )
            item_lines.append(f"```\n{verb.content}\n```")

        sections.append("\n".join(item_lines))

    # Grounding rules section
    if anchor.grounding_rules:
        rules_block = "\n## Grounding Rules\n"
        for rule in anchor.grounding_rules:
            rules_block += f"- {rule}\n"
        rules_block += (
            f"\nExpected answer type: **{anchor.expected_answer_type}** "
            f"(center: {anchor.center_type})"
        )
        sections.append(rules_block)

    return "\n".join(sections)


# ── Top-level convenience ─────────────────────────────────────────────

def interrogate_evidence(
    bag_items: list,
    query: str,
    mode: TaskMode,
    scope: TaskScope,
) -> str:
    """Full interrogation pipeline: classify → records → anchor → format.

    This is the main entry point. Call this instead of bag.to_prompt_block()
    when interrogation is enabled.

    Args:
        bag_items: List of BagItem from EvidenceBag.items.
        query: The user's raw query text.
        mode: The active TaskMode.
        scope: The active TaskScope.

    Returns:
        Formatted, dimension-aware context string for prompt injection.
    """
    intent = classify_intent(query, mode, scope)
    records = build_typed_records(bag_items, intent)
    anchor = build_response_anchor(intent, records)
    formatted = format_interrogated_context(records, anchor, intent)

    logger.info(
        "Interrogated %d evidence items: intent=%s, primary=%s, anchor=%s",
        len(records), intent.intent_class.value,
        intent.primary_dimension.value, anchor.center_type,
    )

    return formatted
