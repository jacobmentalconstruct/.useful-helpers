"""
manifold_kernel.ltm.memory — Long-Term Memory adapter for agents.

Wraps the ManifoldKernel to present a memory-oriented API:

    remember(text, kind, tags, links_to)  → MemoryEntry
    recall(query, strategy, budget, ...)  → RecallResult
    reinforce(memory_id)                  → bump relevance weight
    forget(memory_id)                     → soft-delete from recall
    reflect(query)                        → interrogated, dimension-aware context
    session_dump(session_id)              → all memories from a session
    consolidate()                         → merge near-duplicate memories

This is a TOOL API — no agent logic lives here.  An agent orchestrator
calls these methods; the memory layer never decides what to remember
or when to recall on its own.

Design rationale
────────────────
The kernel already stores artifacts across 4 representational dimensions
(verbatim, structural, semantic, relational) and scores them through two
independent pipelines (manifold lens + gravity scoring).  LTM just needs:

  1. A thin ingest wrapper that accepts agent-native data (text + metadata)
     instead of file paths
  2. Typed memory kinds that map to ArtifactType
  3. Explicit link/reinforce/forget lifecycle verbs
  4. Recall strategies that map to lens profiles + interrogation intents
  5. Session/goal scoping via relation edges

Everything else — chunking, ID generation, deduplication, scoring,
projection, evidence distillation — is delegated to the kernel as-is.
"""

from __future__ import annotations

import hashlib
import json
import logging
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ..api.kernel import ManifoldKernel
from ..config import KernelConfig
from ..types import (
    ArtifactRecord,
    ArtifactType,
    RelationRecord,
    RelationType,
    SourceRecord,
    VerbatimRecord,
    StructuralRecord,
    SemanticRecord,
    content_hash,
    make_artifact_id,
    make_relation_id,
    make_source_id,
)

logger = logging.getLogger(__name__)


# ── Memory kinds ─────────────────────────────────────────────────────

class MemoryKind(str, Enum):
    """Types of memories an agent can store."""
    CONVERSATION = "conversation"    # dialogue turns
    DECISION = "decision"            # choices and their rationale
    OBSERVATION = "observation"      # facts noticed during work
    INSTRUCTION = "instruction"      # user preferences / standing orders
    ARTIFACT = "artifact"            # code, config, file content
    REFLECTION = "reflection"        # agent's own synthesis / insight
    ERROR = "error"                  # mistakes to avoid repeating
    PLAN = "plan"                    # intentions / upcoming steps

    def to_artifact_type(self) -> ArtifactType:
        return {
            MemoryKind.CONVERSATION: ArtifactType.PARAGRAPH,
            MemoryKind.DECISION: ArtifactType.SECTION,
            MemoryKind.OBSERVATION: ArtifactType.TEXT_CHUNK,
            MemoryKind.INSTRUCTION: ArtifactType.TEXT_CHUNK,
            MemoryKind.ARTIFACT: ArtifactType.CODE_CHUNK,
            MemoryKind.REFLECTION: ArtifactType.TEXT_CHUNK,
            MemoryKind.ERROR: ArtifactType.TEXT_CHUNK,
            MemoryKind.PLAN: ArtifactType.SECTION,
        }.get(self, ArtifactType.TEXT_CHUNK)


# ── Recall strategies ────────────────────────────────────────────────

class RecallStrategy(str, Enum):
    """Maps to lens profiles + interrogation settings."""
    ASSOCIATIVE = "associative"          # semantic_heavy — loose conceptual recall
    PRECISE = "precise"                  # exact_match_heavy — find specific memory
    CONTEXTUAL = "contextual"            # structure_heavy — what's nearby?
    PROVENANCE = "provenance"            # provenance_heavy — who said what when?
    NEIGHBORHOOD = "neighborhood"        # neighborhood_support_heavy — related cluster
    BALANCED = "balanced"                # balanced — general purpose recall

    def to_lens_profile(self) -> str:
        return {
            RecallStrategy.ASSOCIATIVE: "semantic_heavy",
            RecallStrategy.PRECISE: "exact_match_heavy",
            RecallStrategy.CONTEXTUAL: "structure_heavy",
            RecallStrategy.PROVENANCE: "provenance_heavy",
            RecallStrategy.NEIGHBORHOOD: "neighborhood_support_heavy",
            RecallStrategy.BALANCED: "balanced",
        }[self]


# ── Data types ───────────────────────────────────────────────────────

@dataclass
class MemoryEntry:
    """A single memory with its metadata."""
    memory_id: str                          # artifact_id in the kernel
    text: str                               # the remembered content
    kind: MemoryKind
    tags: List[str] = field(default_factory=list)
    session_id: str = ""
    goal_id: str = ""
    created_at: str = ""
    reinforcement_count: int = 0
    forgotten: bool = False
    linked_to: List[str] = field(default_factory=list)


@dataclass
class RecallResult:
    """What comes back from a recall operation."""
    query: str
    strategy: RecallStrategy
    memories: List[MemoryEntry]
    scores: Dict[str, float]               # memory_id → score
    score_components: Dict[str, Dict[str, float]]  # memory_id → {component: value}
    interrogated_context: str = ""          # dimension-aware formatted output
    stats: Dict[str, Any] = field(default_factory=dict)


# ── Internal metadata keys ───────────────────────────────────────────

_META_KIND = "ltm_kind"
_META_TAGS = "ltm_tags"
_META_SESSION = "ltm_session"
_META_GOAL = "ltm_goal"
_META_REINFORCED = "ltm_reinforced"
_META_FORGOTTEN = "ltm_forgotten"
_META_CREATED = "ltm_created"


# ══════════════════════════════════════════════════════════════════════
# AgentMemory — the public API
# ══════════════════════════════════════════════════════════════════════

class AgentMemory:
    """
    Long-term memory layer for agents, backed by the Graph Manifold Kernel.

    Usage::

        mem = AgentMemory.create(db_path=":memory:")

        # Store
        entry = mem.remember(
            "User prefers concise answers, no bullet points.",
            kind=MemoryKind.INSTRUCTION,
            tags=["user_pref", "formatting"],
            session_id="sess_001",
        )

        # Recall
        result = mem.recall(
            "What format does the user want?",
            strategy=RecallStrategy.PRECISE,
            budget=5,
        )

        # Reinforce (this memory keeps proving useful)
        mem.reinforce(entry.memory_id)

        # Reflect (get dimension-aware context for prompt injection)
        context = mem.reflect("How should I format my response?")

        # Forget (soft-delete — stops appearing in recall)
        mem.forget(entry.memory_id)
    """

    def __init__(self, kernel: ManifoldKernel) -> None:
        self._kernel = kernel
        self._store = kernel.store
        # Internal index: memory_id → metadata dict (cached from DB)
        self._meta_cache: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create(
        cls,
        db_path: str = "_project_library/agent_memory.db",
        semantic_backend: str = "none",
    ) -> "AgentMemory":
        """Factory for standalone LTM instances."""
        cfg = KernelConfig.with_defaults(db_path=db_path)
        cfg.semantic.backend = semantic_backend
        kernel = ManifoldKernel(cfg)
        return cls(kernel)

    @property
    def kernel(self) -> ManifoldKernel:
        """Direct access to the underlying kernel for advanced use."""
        return self._kernel

    def close(self) -> None:
        self._kernel.close()

    # ══════════════════════════════════════════════════════════════════
    # REMEMBER — store a new memory
    # ══════════════════════════════════════════════════════════════════

    def remember(
        self,
        text: str,
        kind: MemoryKind = MemoryKind.OBSERVATION,
        tags: Optional[List[str]] = None,
        session_id: str = "",
        goal_id: str = "",
        links_to: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """
        Store a new memory.

        The text is ingested as a single artifact (no chunking for short
        memories, normal chunking for long ones).  Metadata is stored in
        the artifact's metadata_json field.  Explicit links create typed
        relation edges.

        Args:
            text:       The content to remember.
            kind:       What type of memory this is.
            tags:       Freeform labels for filtering.
            session_id: Agent session that produced this memory.
            goal_id:    Goal/task context for boundary dampening.
            links_to:   List of memory_ids to create DERIVED_FROM edges to.

        Returns:
            A MemoryEntry with the assigned memory_id.
        """
        tags = tags or []
        links_to = links_to or []
        now = datetime.now(timezone.utc).isoformat()

        # Build metadata
        meta = {
            _META_KIND: kind.value,
            _META_TAGS: tags,
            _META_SESSION: session_id,
            _META_GOAL: goal_id,
            _META_REINFORCED: 0,
            _META_FORGOTTEN: False,
            _META_CREATED: now,
        }
        meta_json = json.dumps(meta)

        # Write as a temporary file so the existing ingest pipeline can
        # process it (preserves chunking, semantic embedding, etc.)
        # For short memories (< chunk_size), this produces exactly 1 artifact.
        c_hash = content_hash(text)
        source_id = make_source_id()
        art_id = make_artifact_id()

        # Register source
        self._store.add_source(SourceRecord(
            source_id=source_id,
            path=f"memory://{kind.value}/{art_id}",
            file_hash=c_hash,
            metadata_json=meta_json,
        ))

        # Register artifact
        self._store.add_artifact(ArtifactRecord(
            artifact_id=art_id,
            source_id=source_id,
            artifact_type=kind.to_artifact_type(),
            content_hash=c_hash,
            metadata_json=meta_json,
        ))

        # Verbatim
        self._store.add_verbatim(VerbatimRecord(
            artifact_id=art_id,
            raw_text=text,
            normalized_text=text,
            char_start=0,
            char_end=len(text),
        ))

        # Structural (memory:// virtual path)
        self._store.add_structural(StructuralRecord(
            artifact_id=art_id,
            container_id=source_id,
            path=f"memory://{kind.value}/{art_id}",
            depth=0,
            ordinal=0,
        ))

        # Semantic (if embedder available)
        try:
            adapter = self._kernel.semantic_adapter
            sem_result = adapter.embed(text)
            from ..ingest.semantic_adapter import vector_to_blob
            blob = vector_to_blob(sem_result.vector) if sem_result.vector else b""
            self._store.add_semantic(SemanticRecord(
                artifact_id=art_id,
                semantic_backend=sem_result.backend,
                feature_blob=blob,
                norm=sem_result.norm,
            ))
        except Exception:
            self._store.add_semantic(SemanticRecord(artifact_id=art_id))

        # Source relation
        self._store.add_relation(RelationRecord(
            relation_id=make_relation_id(),
            from_id=art_id,
            to_id=source_id,
            relation_type=RelationType.BELONGS_TO_SOURCE,
        ))

        # Session anchor
        if session_id:
            self._store.add_relation(RelationRecord(
                relation_id=make_relation_id(),
                from_id=art_id,
                to_id=session_id,
                relation_type=RelationType.ANCHORED_TO_SESSION,
            ))

        # Explicit links
        for target_id in links_to:
            self._store.add_relation(RelationRecord(
                relation_id=make_relation_id(),
                from_id=art_id,
                to_id=target_id,
                relation_type=RelationType.DERIVED_FROM,
            ))

        # Cache metadata
        self._meta_cache[art_id] = meta

        entry = MemoryEntry(
            memory_id=art_id,
            text=text,
            kind=kind,
            tags=tags,
            session_id=session_id,
            goal_id=goal_id,
            created_at=now,
            linked_to=links_to,
        )

        logger.info("Remembered [%s] %s: %.40s...", kind.value, art_id, text)
        return entry

    # ══════════════════════════════════════════════════════════════════
    # RECALL — query memories
    # ══════════════════════════════════════════════════════════════════

    def recall(
        self,
        query: str,
        strategy: RecallStrategy = RecallStrategy.BALANCED,
        budget: int = 10,
        min_score: float = 0.0,
        filter_kinds: Optional[Set[MemoryKind]] = None,
        filter_tags: Optional[Set[str]] = None,
        filter_session: Optional[str] = None,
        exclude_forgotten: bool = True,
    ) -> RecallResult:
        """
        Recall memories relevant to a query.

        Uses the kernel's full projection + lens pipeline, then filters
        by memory-specific metadata (kind, tags, session, forgotten status).

        Args:
            query:             What to search for.
            strategy:          Which lens profile to use for scoring.
            budget:            Maximum memories to return.
            min_score:         Minimum score threshold.
            filter_kinds:      Only return these memory kinds.
            filter_tags:       Only return memories with ALL of these tags.
            filter_session:    Only return memories from this session.
            exclude_forgotten: Skip soft-deleted memories (default True).

        Returns:
            RecallResult with ranked memories, scores, and score components.
        """
        lens = strategy.to_lens_profile()

        # Run the full kernel pipeline
        bag = self._kernel.extract_evidence(
            query=query,
            lens_profile=lens,
            max_items=budget * 3,  # over-fetch to allow post-filtering
            min_score=min_score,
        )

        # Post-filter by LTM metadata
        memories: List[MemoryEntry] = []
        scores: Dict[str, float] = {}
        components: Dict[str, Dict[str, float]] = {}

        for item in bag.items:
            meta = self._get_meta(item.artifact_id)
            if meta is None:
                continue  # not a memory (could be ingested file data)

            # Check forgotten
            if exclude_forgotten and meta.get(_META_FORGOTTEN, False):
                continue

            # Check kind filter
            if filter_kinds:
                item_kind = MemoryKind(meta.get(_META_KIND, "observation"))
                if item_kind not in filter_kinds:
                    continue

            # Check tag filter
            if filter_tags:
                item_tags = set(meta.get(_META_TAGS, []))
                if not filter_tags.issubset(item_tags):
                    continue

            # Check session filter
            if filter_session:
                if meta.get(_META_SESSION, "") != filter_session:
                    continue

            # Build MemoryEntry from artifact + metadata
            entry = MemoryEntry(
                memory_id=item.artifact_id,
                text=item.text_snippet,
                kind=MemoryKind(meta.get(_META_KIND, "observation")),
                tags=meta.get(_META_TAGS, []),
                session_id=meta.get(_META_SESSION, ""),
                goal_id=meta.get(_META_GOAL, ""),
                created_at=meta.get(_META_CREATED, ""),
                reinforcement_count=meta.get(_META_REINFORCED, 0),
                forgotten=meta.get(_META_FORGOTTEN, False),
            )

            memories.append(entry)
            scores[item.artifact_id] = item.score
            components[item.artifact_id] = item.score_components

            if len(memories) >= budget:
                break

        return RecallResult(
            query=query,
            strategy=strategy,
            memories=memories,
            scores=scores,
            score_components=components,
            stats={
                "candidates_before_filter": len(bag.items),
                "candidates_after_filter": len(memories),
                "lens_profile": lens,
                "projection_nodes": bag.stats.total_nodes_in_projection if bag.stats else 0,
            },
        )

    # ══════════════════════════════════════════════════════════════════
    # REFLECT — recall + interrogation for prompt injection
    # ══════════════════════════════════════════════════════════════════

    def reflect(
        self,
        query: str,
        strategy: RecallStrategy = RecallStrategy.BALANCED,
        budget: int = 8,
        mode: str = "chat",
        scope: str = "local",
    ) -> RecallResult:
        """
        Recall memories AND produce dimension-aware interrogated context.

        This is the main method for agents that want ready-to-inject
        context blocks for their prompts.

        Returns:
            RecallResult with .interrogated_context populated.
        """
        result = self.recall(query, strategy=strategy, budget=budget)

        if result.memories:
            # Re-extract evidence items for interrogation
            bag = self._kernel.extract_evidence(
                query=query,
                lens_profile=strategy.to_lens_profile(),
                max_items=budget,
            )
            # Filter to only memory items
            memory_ids = {m.memory_id for m in result.memories}
            memory_items = [it for it in bag.items if it.artifact_id in memory_ids]

            if memory_items:
                result.interrogated_context = self._kernel.interrogate(
                    memory_items, query, mode=mode, scope=scope,
                )

        return result

    # ══════════════════════════════════════════════════════════════════
    # REINFORCE — strengthen a memory's relevance
    # ══════════════════════════════════════════════════════════════════

    def reinforce(self, memory_id: str) -> int:
        """
        Bump the reinforcement count for a memory.

        Returns the new reinforcement count.
        Reinforced memories get a scoring boost in the gravity pipeline.
        """
        meta = self._get_meta(memory_id)
        if meta is None:
            logger.warning("Cannot reinforce unknown memory: %s", memory_id)
            return 0

        count = meta.get(_META_REINFORCED, 0) + 1
        meta[_META_REINFORCED] = count
        self._persist_meta(memory_id, meta)
        logger.info("Reinforced %s → count=%d", memory_id, count)
        return count

    # ══════════════════════════════════════════════════════════════════
    # FORGET — soft-delete a memory from recall results
    # ══════════════════════════════════════════════════════════════════

    def forget(self, memory_id: str) -> bool:
        """
        Soft-delete a memory. It stays in storage but won't appear
        in recall results (unless exclude_forgotten=False).

        Returns True if the memory was found and marked forgotten.
        """
        meta = self._get_meta(memory_id)
        if meta is None:
            return False

        meta[_META_FORGOTTEN] = True
        self._persist_meta(memory_id, meta)
        logger.info("Forgot %s", memory_id)
        return True

    def unforget(self, memory_id: str) -> bool:
        """Restore a soft-deleted memory to active recall."""
        meta = self._get_meta(memory_id)
        if meta is None:
            return False

        meta[_META_FORGOTTEN] = False
        self._persist_meta(memory_id, meta)
        logger.info("Unforgot %s", memory_id)
        return True

    # ══════════════════════════════════════════════════════════════════
    # LINK — create explicit edges between memories
    # ══════════════════════════════════════════════════════════════════

    def link(
        self,
        from_id: str,
        to_id: str,
        relation: RelationType = RelationType.DERIVED_FROM,
        weight: float = 1.0,
    ) -> str:
        """Create an explicit typed edge between two memories."""
        rel_id = make_relation_id()
        self._store.add_relation(RelationRecord(
            relation_id=rel_id,
            from_id=from_id,
            to_id=to_id,
            relation_type=relation,
            weight=weight,
        ))
        logger.info("Linked %s → %s (%s)", from_id, to_id, relation.value)
        return rel_id

    # ══════════════════════════════════════════════════════════════════
    # SESSION DUMP — all memories from a session
    # ══════════════════════════════════════════════════════════════════

    def session_dump(
        self,
        session_id: str,
        include_forgotten: bool = False,
    ) -> List[MemoryEntry]:
        """Return all memories from a specific session, ordered by creation time."""
        entries = []
        # Walk all artifacts and check metadata
        for art in self._store.list_artifacts():
            meta = self._get_meta(art.artifact_id)
            if meta is None:
                continue
            if meta.get(_META_SESSION, "") != session_id:
                continue
            if not include_forgotten and meta.get(_META_FORGOTTEN, False):
                continue

            verb = self._store.get_verbatim(art.artifact_id)
            entries.append(MemoryEntry(
                memory_id=art.artifact_id,
                text=verb.raw_text if verb else "",
                kind=MemoryKind(meta.get(_META_KIND, "observation")),
                tags=meta.get(_META_TAGS, []),
                session_id=session_id,
                goal_id=meta.get(_META_GOAL, ""),
                created_at=meta.get(_META_CREATED, ""),
                reinforcement_count=meta.get(_META_REINFORCED, 0),
                forgotten=meta.get(_META_FORGOTTEN, False),
            ))

        entries.sort(key=lambda e: e.created_at)
        return entries

    # ══════════════════════════════════════════════════════════════════
    # STATS
    # ══════════════════════════════════════════════════════════════════

    def stats(self) -> Dict[str, Any]:
        """Memory layer statistics."""
        kernel_stats = self._kernel.stats()

        # Count by kind
        kind_counts: Dict[str, int] = {}
        forgotten_count = 0
        total_reinforcements = 0

        for art in self._store.list_artifacts():
            meta = self._get_meta(art.artifact_id)
            if meta is None:
                continue
            k = meta.get(_META_KIND, "unknown")
            kind_counts[k] = kind_counts.get(k, 0) + 1
            if meta.get(_META_FORGOTTEN, False):
                forgotten_count += 1
            total_reinforcements += meta.get(_META_REINFORCED, 0)

        return {
            "total_memories": sum(kind_counts.values()),
            "by_kind": kind_counts,
            "forgotten": forgotten_count,
            "total_reinforcements": total_reinforcements,
            "kernel": kernel_stats,
        }

    # ══════════════════════════════════════════════════════════════════
    # Internal helpers
    # ══════════════════════════════════════════════════════════════════

    def _get_meta(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """Load memory metadata from cache or DB."""
        if artifact_id in self._meta_cache:
            return self._meta_cache[artifact_id]

        art = self._store.get_artifact(artifact_id)
        if art is None:
            return None

        try:
            meta = json.loads(art.metadata_json)
            if _META_KIND not in meta:
                return None  # not an LTM artifact
            self._meta_cache[artifact_id] = meta
            return meta
        except (json.JSONDecodeError, TypeError):
            return None

    def _persist_meta(self, artifact_id: str, meta: Dict[str, Any]) -> None:
        """Write updated metadata back to the artifact record."""
        self._meta_cache[artifact_id] = meta
        meta_json = json.dumps(meta)
        # Update via raw SQL (the store doesn't expose an update_artifact method)
        self._store.conn.execute(
            "UPDATE artifacts SET metadata_json = ? WHERE artifact_id = ?",
            (meta_json, artifact_id),
        )
        self._store.conn.commit()

    # ══════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ══════════════════════════════════════════════════════════════════

    def _ensure_sessions_table(self) -> None:
        """Create the sessions table if it doesn't exist."""
        self._store.conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id    TEXT PRIMARY KEY,
                name          TEXT NOT NULL DEFAULT '',
                created_at    TEXT NOT NULL,
                updated_at    TEXT NOT NULL,
                message_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}'
            )
        """)
        self._store.conn.commit()

    def _count_session_memories(self, session_id: str) -> int:
        """Count memories belonging to a session."""
        count = 0
        for art in self._store.list_artifacts():
            meta = self._get_meta(art.artifact_id)
            if meta and meta.get(_META_SESSION, "") == session_id:
                if not meta.get(_META_FORGOTTEN, False):
                    count += 1
        return count

    def save_session(self, session_id: str, name: str = "") -> None:
        """Upsert session metadata. Computes message_count from stored memories."""
        self._ensure_sessions_table()
        now = datetime.now(timezone.utc).isoformat()
        msg_count = self._count_session_memories(session_id)

        existing = self._store.conn.execute(
            "SELECT session_id, name FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()

        if existing:
            # Update — keep existing name unless a new one is provided
            update_name = name if name else existing[1]
            self._store.conn.execute(
                "UPDATE sessions SET name = ?, updated_at = ?, message_count = ? WHERE session_id = ?",
                (update_name, now, msg_count, session_id),
            )
        else:
            self._store.conn.execute(
                "INSERT INTO sessions (session_id, name, created_at, updated_at, message_count) VALUES (?, ?, ?, ?, ?)",
                (session_id, name, now, now, msg_count),
            )
        self._store.conn.commit()
        logger.info("Session saved: %s (%s) — %d memories", session_id, name or "(unnamed)", msg_count)

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Return session metadata, or None if not found."""
        self._ensure_sessions_table()
        row = self._store.conn.execute(
            "SELECT session_id, name, created_at, updated_at, message_count FROM sessions WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if row:
            return {
                "session_id": row[0], "name": row[1], "created_at": row[2],
                "updated_at": row[3], "message_count": row[4],
            }
        return None

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Return all saved sessions, most recently updated first."""
        self._ensure_sessions_table()
        rows = self._store.conn.execute(
            "SELECT session_id, name, created_at, updated_at, message_count FROM sessions ORDER BY updated_at DESC"
        ).fetchall()
        return [
            {"session_id": r[0], "name": r[1], "created_at": r[2], "updated_at": r[3], "message_count": r[4]}
            for r in rows
        ]

    def rename_session(self, session_id: str, new_name: str) -> None:
        """Rename a saved session."""
        self._ensure_sessions_table()
        now = datetime.now(timezone.utc).isoformat()
        self._store.conn.execute(
            "UPDATE sessions SET name = ?, updated_at = ? WHERE session_id = ?",
            (new_name, now, session_id),
        )
        self._store.conn.commit()
        logger.info("Session renamed: %s -> %s", session_id, new_name)

    def delete_session(self, session_id: str) -> int:
        """
        Delete a session and all its memories.
        Returns the number of memories removed.
        """
        self._ensure_sessions_table()

        # Find all artifact IDs belonging to this session
        to_delete = []
        for art in self._store.list_artifacts():
            meta = self._get_meta(art.artifact_id)
            if meta and meta.get(_META_SESSION, "") == session_id:
                to_delete.append(art.artifact_id)

        # Delete from all dimension tables + relations
        conn = self._store.conn
        for aid in to_delete:
            conn.execute("DELETE FROM verbatim WHERE artifact_id = ?", (aid,))
            conn.execute("DELETE FROM structural WHERE artifact_id = ?", (aid,))
            conn.execute("DELETE FROM semantic WHERE artifact_id = ?", (aid,))
            conn.execute("DELETE FROM relations WHERE from_id = ? OR to_id = ?", (aid, aid))
            conn.execute("DELETE FROM sources WHERE artifact_id = ?", (aid,))
            conn.execute("DELETE FROM artifacts WHERE artifact_id = ?", (aid,))
            self._meta_cache.pop(aid, None)

        # Delete session row
        conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()

        logger.info("Session deleted: %s — removed %d memories", session_id, len(to_delete))
        return len(to_delete)
