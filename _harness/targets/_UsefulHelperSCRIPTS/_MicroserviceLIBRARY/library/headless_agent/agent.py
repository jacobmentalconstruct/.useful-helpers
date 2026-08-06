"""Headless SQLite-backed agent aligned to the game agent DB manifest."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def estimate_tokens(text: str) -> int:
    return len([part for part in re.split(r"\s+", str(text).strip()) if part])


def normalize_terms(text: str) -> List[str]:
    return [part for part in re.findall(r"[A-Za-z0-9_:-]+", str(text).lower()) if len(part) >= 2]


@dataclass
class AgentContextBundle:
    session_id: str
    user_input: str
    pinned_memories: List[Dict[str, Any]]
    recent_memories: List[Dict[str, Any]]
    evicted_memories: List[Dict[str, Any]]
    knowledge_hits: List[Dict[str, Any]]
    model_messages: List[Dict[str, str]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SQLiteSessionAgent:
    def __init__(
        self,
        db_path: Path | str,
        *,
        window_limit: int = 20,
        token_budget: int = 4000,
    ) -> None:
        self.db_path = Path(db_path).resolve()
        self.window_limit = max(1, int(window_limit))
        self.token_budget = max(1, int(token_budget))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.fts_enabled = False
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                '''
                CREATE TABLE IF NOT EXISTS agent_sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TEXT NOT NULL,
                    ended_at TEXT,
                    model TEXT DEFAULT '',
                    status TEXT DEFAULT 'active',
                    config_json TEXT DEFAULT '{}'
                );

                CREATE TABLE IF NOT EXISTS agent_memory (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    token_count INTEGER DEFAULT 0,
                    is_pinned INTEGER DEFAULT 0,
                    metadata_json TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_agent_memory_session ON agent_memory(session_id, memory_id);
                CREATE INDEX IF NOT EXISTS idx_agent_memory_pinned ON agent_memory(session_id, is_pinned, memory_id);

                CREATE TABLE IF NOT EXISTS agent_knowledge (
                    chunk_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    category TEXT DEFAULT 'observation',
                    content TEXT NOT NULL,
                    embedding BLOB,
                    created_at TEXT NOT NULL,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    metadata_json TEXT DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_agent_knowledge_category ON agent_knowledge(category, created_at);
                '''
            )
            try:
                conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS agent_memory_fts USING fts5(memory_id UNINDEXED, session_id UNINDEXED, content)")
                conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS agent_knowledge_fts USING fts5(chunk_id UNINDEXED, category UNINDEXED, content)")
                self.fts_enabled = True
            except sqlite3.OperationalError:
                self.fts_enabled = False

    def create_session(self, *, model: str = '', config: Optional[Dict[str, Any]] = None, session_id: Optional[str] = None) -> str:
        session_id = session_id or f"sess_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
        now = utc_now()
        payload = dict(config or {})
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO agent_sessions (session_id, started_at, ended_at, model, status, config_json) VALUES (?, COALESCE((SELECT started_at FROM agent_sessions WHERE session_id = ?), ?), (SELECT ended_at FROM agent_sessions WHERE session_id = ?), ?, COALESCE((SELECT status FROM agent_sessions WHERE session_id = ?), 'active'), ?)",
                (session_id, session_id, now, session_id, str(model or '').strip(), session_id, json.dumps(payload, sort_keys=True)),
            )
        return session_id

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM agent_sessions WHERE status = 'active' ORDER BY started_at DESC LIMIT 1"
            ).fetchone()
        return self._session_row_to_dict(row) if row else None

    def end_session(self, session_id: str) -> bool:
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE agent_sessions SET status = 'ended', ended_at = ? WHERE session_id = ? AND status != 'ended'",
                (utc_now(), session_id),
            )
        return result.rowcount > 0

    def append_memory(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        token_count: Optional[int] = None,
        is_pinned: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        self._require_session(session_id)
        role = str(role).strip()
        content = str(content)
        if not role:
            raise ValueError('role is required')
        if not content.strip():
            raise ValueError('content is required')
        metadata_json = json.dumps(dict(metadata or {}), sort_keys=True)
        count = int(token_count if token_count is not None else estimate_tokens(content))
        with self._connect() as conn:
            row = conn.execute(
                "INSERT INTO agent_memory (session_id, created_at, role, content, token_count, is_pinned, metadata_json) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING memory_id",
                (session_id, utc_now(), role, content, count, 1 if is_pinned else 0, metadata_json),
            ).fetchone()
            memory_id = int(row['memory_id'])
            if self.fts_enabled:
                conn.execute(
                    "INSERT INTO agent_memory_fts (memory_id, session_id, content) VALUES (?, ?, ?)",
                    (memory_id, session_id, content),
                )
        return memory_id

    def pin_memory(self, memory_id: int) -> bool:
        with self._connect() as conn:
            result = conn.execute(
                "UPDATE agent_memory SET is_pinned = 1 WHERE memory_id = ?",
                (int(memory_id),),
            )
        return result.rowcount > 0

    def get_full_context(self, session_id: str, window_limit: Optional[int] = None) -> List[Dict[str, Any]]:
        self._require_session(session_id)
        limit = max(1, int(window_limit or self.window_limit))
        with self._connect() as conn:
            pinned = conn.execute(
                "SELECT * FROM agent_memory WHERE session_id = ? AND is_pinned = 1 ORDER BY memory_id ASC",
                (session_id,),
            ).fetchall()
            recent = conn.execute(
                "SELECT * FROM agent_memory WHERE session_id = ? AND is_pinned = 0 ORDER BY memory_id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        recent_payload = [self._memory_row_to_dict(row) for row in reversed(recent)]
        return [self._memory_row_to_dict(row) for row in pinned] + recent_payload

    def count_window_tokens(self, session_id: str, window_limit: Optional[int] = None) -> int:
        return sum(item['token_count'] for item in self.get_full_context(session_id, window_limit=window_limit))

    def evict_oldest_memories(self, session_id: str, keep_recent: Optional[int] = None) -> List[Dict[str, Any]]:
        self._require_session(session_id)
        keep_recent = max(1, int(keep_recent or self.window_limit))
        evicted_payload: List[Dict[str, Any]] = []
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM agent_memory WHERE session_id = ? AND is_pinned = 0 ORDER BY memory_id ASC",
                (session_id,),
            ).fetchall()
            overflow = len(rows) - keep_recent
            if overflow <= 0:
                return []
            evicted_rows = rows[:overflow]
            for row in evicted_rows:
                metadata = json.loads(row['metadata_json'] or '{}')
                metadata['evicted_at'] = utc_now()
                metadata['eviction_reason'] = 'window_overflow'
                conn.execute(
                    "UPDATE agent_memory SET metadata_json = ? WHERE memory_id = ?",
                    (json.dumps(metadata, sort_keys=True), row['memory_id']),
                )
                payload = self._memory_row_to_dict(row)
                payload['metadata'] = metadata
                evicted_payload.append(payload)
        return evicted_payload

    def summarize_and_pin_evicted(self, session_id: str, keep_recent: Optional[int] = None) -> Optional[int]:
        evicted = self.evict_oldest_memories(session_id, keep_recent=keep_recent)
        if not evicted:
            return None
        lines = [f"[{item['role']}] {item['content']}" for item in evicted]
        summary = "Summary of evicted conversation segment:\n" + "\n".join(lines)
        return self.append_memory(
            session_id=session_id,
            role='summary',
            content=summary,
            is_pinned=True,
            metadata={'source_memory_ids': [item['memory_id'] for item in evicted]},
        )

    def store_knowledge(
        self,
        *,
        source: str,
        content: str,
        category: str = 'observation',
        embedding: bytes | None = None,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_id: Optional[str] = None,
    ) -> str:
        source = str(source).strip()
        content = str(content)
        category = str(category).strip() or 'observation'
        if not source:
            raise ValueError('source is required')
        if not content.strip():
            raise ValueError('content is required')
        chunk_id = chunk_id or f"know_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO agent_knowledge (chunk_id, source, category, content, embedding, created_at, last_accessed, access_count, metadata_json) VALUES (?, ?, ?, ?, ?, COALESCE((SELECT created_at FROM agent_knowledge WHERE chunk_id = ?), ?), (SELECT last_accessed FROM agent_knowledge WHERE chunk_id = ?), COALESCE((SELECT access_count FROM agent_knowledge WHERE chunk_id = ?), 0), ?)",
                (chunk_id, source, category, content, embedding, chunk_id, utc_now(), chunk_id, chunk_id, json.dumps(dict(metadata or {}), sort_keys=True)),
            )
            if self.fts_enabled:
                conn.execute("DELETE FROM agent_knowledge_fts WHERE chunk_id = ?", (chunk_id,))
                conn.execute(
                    "INSERT INTO agent_knowledge_fts (chunk_id, category, content) VALUES (?, ?, ?)",
                    (chunk_id, category, content),
                )
        return chunk_id

    def search_knowledge(self, query: str, category: str = '', limit: int = 10) -> List[Dict[str, Any]]:
        query = str(query).strip()
        category = str(category).strip()
        limit = max(1, int(limit))
        if not query:
            return []
        with self._connect() as conn:
            if self.fts_enabled:
                if category:
                    rows = conn.execute(
                        '''
                        SELECT ak.chunk_id, ak.source, ak.category, ak.content, ak.embedding, ak.created_at, ak.last_accessed, ak.access_count, ak.metadata_json, bm25(agent_knowledge_fts) AS score
                        FROM agent_knowledge_fts
                        JOIN agent_knowledge ak ON ak.chunk_id = agent_knowledge_fts.chunk_id
                        WHERE agent_knowledge_fts MATCH ? AND ak.category = ?
                        ORDER BY score
                        LIMIT ?
                        ''',
                        (self._fts_query(query), category, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        '''
                        SELECT ak.chunk_id, ak.source, ak.category, ak.content, ak.embedding, ak.created_at, ak.last_accessed, ak.access_count, ak.metadata_json, bm25(agent_knowledge_fts) AS score
                        FROM agent_knowledge_fts
                        JOIN agent_knowledge ak ON ak.chunk_id = agent_knowledge_fts.chunk_id
                        WHERE agent_knowledge_fts MATCH ?
                        ORDER BY score
                        LIMIT ?
                        ''',
                        (self._fts_query(query), limit),
                    ).fetchall()
                hits = [self._knowledge_row_to_dict(row) for row in rows]
            else:
                sql = "SELECT * FROM agent_knowledge"
                params: List[Any] = []
                if category:
                    sql += " WHERE category = ?"
                    params.append(category)
                rows = conn.execute(sql, params).fetchall()
                hits = self._fallback_rank(query, rows, self._knowledge_row_to_dict, limit)

            now = utc_now()
            for hit in hits:
                conn.execute(
                    "UPDATE agent_knowledge SET last_accessed = ?, access_count = access_count + 1 WHERE chunk_id = ?",
                    (now, hit['chunk_id']),
                )
                hit['last_accessed'] = now
                hit['access_count'] = int(hit.get('access_count', 0)) + 1
        return hits

    def search_evicted_memory(self, session_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        self._require_session(session_id)
        query = str(query).strip()
        limit = max(1, int(limit))
        if not query:
            return []
        with self._connect() as conn:
            cutoff_row = conn.execute(
                "SELECT COALESCE(MAX(memory_id), 0) AS max_memory_id FROM (SELECT memory_id FROM agent_memory WHERE session_id = ? AND is_pinned = 0 ORDER BY memory_id DESC LIMIT ?)",
                (session_id, self.window_limit),
            ).fetchone()
            cutoff = int(cutoff_row['max_memory_id'] or 0)
            rows = conn.execute(
                "SELECT * FROM agent_memory WHERE session_id = ? AND is_pinned = 0 AND memory_id < ? ORDER BY memory_id DESC",
                (session_id, cutoff if cutoff else 0),
            ).fetchall()
        return self._fallback_rank(query, rows, self._memory_row_to_dict, limit)

    def build_context(
        self,
        session_id: str,
        user_input: str,
        *,
        system_prompt: str = '',
        knowledge_limit: int = 4,
        evicted_limit: int = 4,
        window_limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._require_session(session_id)
        query = str(user_input)
        context_rows = self.get_full_context(session_id, window_limit=window_limit)
        pinned = [row for row in context_rows if row['is_pinned']]
        recent = [row for row in context_rows if not row['is_pinned']]
        evicted = self.search_evicted_memory(session_id, query, limit=evicted_limit)
        knowledge = self.search_knowledge(query, limit=knowledge_limit)

        model_messages: List[Dict[str, str]] = []
        if system_prompt.strip():
            model_messages.append({'role': 'system', 'content': system_prompt.strip()})
        for row in pinned:
            model_messages.append({'role': row['role'], 'content': row['content']})
        if knowledge:
            model_messages.append({'role': 'system', 'content': 'Retrieved knowledge:\n' + self._format_knowledge_hits(knowledge)})
        if evicted:
            model_messages.append({'role': 'system', 'content': 'Relevant evicted session memory:\n' + self._format_evicted_hits(evicted)})
        for row in recent:
            model_messages.append({'role': row['role'], 'content': row['content']})
        model_messages.append({'role': 'user', 'content': query})

        bundle = AgentContextBundle(
            session_id=session_id,
            user_input=query,
            pinned_memories=pinned,
            recent_memories=recent,
            evicted_memories=evicted,
            knowledge_hits=knowledge,
            model_messages=model_messages,
        )
        return bundle.to_dict()

    def _require_session(self, session_id: str) -> None:
        with self._connect() as conn:
            row = conn.execute("SELECT 1 FROM agent_sessions WHERE session_id = ?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(f'Unknown session: {session_id}')

    def _fts_query(self, query: str) -> str:
        terms = normalize_terms(query)
        return ' OR '.join(terms) if terms else query

    def _fallback_rank(self, query: str, rows: List[sqlite3.Row], converter, limit: int) -> List[Dict[str, Any]]:
        terms = normalize_terms(query)
        ranked: List[tuple[int, Dict[str, Any]]] = []
        for row in rows:
            payload = converter(row)
            haystack = payload.get('content', '').lower()
            score = sum(haystack.count(term) for term in terms)
            if score > 0:
                ranked.append((score, payload))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in ranked[:limit]]

    def _session_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            'session_id': row['session_id'],
            'started_at': row['started_at'],
            'ended_at': row['ended_at'],
            'model': row['model'],
            'status': row['status'],
            'config': json.loads(row['config_json'] or '{}'),
        }

    def _memory_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            'memory_id': int(row['memory_id']),
            'session_id': row['session_id'],
            'created_at': row['created_at'],
            'role': row['role'],
            'content': row['content'],
            'token_count': int(row['token_count'] or 0),
            'is_pinned': bool(row['is_pinned']),
            'metadata': json.loads(row['metadata_json'] or '{}'),
        }

    def _knowledge_row_to_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        payload = {
            'chunk_id': row['chunk_id'],
            'source': row['source'],
            'category': row['category'],
            'content': row['content'],
            'embedding': row['embedding'],
            'created_at': row['created_at'],
            'last_accessed': row['last_accessed'],
            'access_count': int(row['access_count'] or 0),
            'metadata': json.loads(row['metadata_json'] or '{}'),
        }
        if 'score' in row.keys():
            payload['score'] = row['score']
        return payload

    def _format_knowledge_hits(self, hits: List[Dict[str, Any]]) -> str:
        return '\n'.join(f"- [{item['category']}] {item['source']}: {item['content']}" for item in hits)

    def _format_evicted_hits(self, hits: List[Dict[str, Any]]) -> str:
        return '\n'.join(f"- mem {item['memory_id']} [{item['role']}]: {item['content']}" for item in hits)
