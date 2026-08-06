"""
SQLite persistence layer for Evidence Bag nodes.

Owns the schema, CRUD, connection management, and embedding blob storage.
Completely independent of any application — takes a db path and works.

Thread safety: uses check_same_thread=False with a timeout, matching the
same pattern as the host app's existing KnowledgeBase.
"""

from __future__ import annotations

import json
import sqlite3
import struct
import threading
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from evidence_bag.node import Node, NodeKind, TrustState

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS eb_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS eb_nodes (
    node_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT    NOT NULL,
    content       TEXT    NOT NULL,
    tags_json     TEXT    NOT NULL DEFAULT '[]',
    source_ref    TEXT    NOT NULL DEFAULT '',
    created_at    REAL    NOT NULL,
    access_count  INTEGER NOT NULL DEFAULT 0,
    goal_id       TEXT,
    trust_state   TEXT    NOT NULL DEFAULT 'normal',
    connections_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS eb_embeddings (
    node_id      INTEGER PRIMARY KEY,
    vector_blob  BLOB    NOT NULL,
    FOREIGN KEY (node_id) REFERENCES eb_nodes(node_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_eb_nodes_kind ON eb_nodes(kind);
CREATE INDEX IF NOT EXISTS idx_eb_nodes_goal ON eb_nodes(goal_id);
"""


def _pack_vector(vec: List[float]) -> bytes:
    """Pack a list of floats into a compact binary blob (float32)."""
    return struct.pack(f"{len(vec)}f", *vec)


def _unpack_vector(blob: bytes) -> List[float]:
    """Unpack a binary blob back into a list of floats."""
    n = len(blob) // 4
    return list(struct.unpack(f"{n}f", blob))


class NodeStore:
    """
    SQLite-backed storage for evidence bag nodes.

    Usage:
        store = NodeStore("path/to/memory.db")
        node_id = store.insert(node)
        nodes = store.get_all()
        store.close()
    """

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = str(db_path)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(
            self._db_path,
            check_same_thread=False,
            timeout=10,
        )
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_schema()

    # ------------------------------------------------------------------
    # Schema management
    # ------------------------------------------------------------------

    def _ensure_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(_SCHEMA_SQL)

        cur.execute(
            "SELECT value FROM eb_meta WHERE key='schema_version'"
        )
        row = cur.fetchone()
        stored = int(row[0]) if row else 0

        if stored < SCHEMA_VERSION:
            cur.execute(
                "INSERT OR REPLACE INTO eb_meta(key, value) VALUES (?, ?)",
                ("schema_version", str(SCHEMA_VERSION)),
            )
        self._conn.commit()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def insert(self, node: Node) -> int:
        """
        Insert a node and its optional embedding. Returns the new node_id.
        """
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                """INSERT INTO eb_nodes
                   (kind, content, tags_json, source_ref, created_at,
                    access_count, goal_id, trust_state, connections_json)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    node.kind.value,
                    node.content,
                    json.dumps(node.tags),
                    node.source_ref,
                    node.created_at,
                    node.access_count,
                    node.goal_id,
                    node.trust_state.value,
                    json.dumps(node.connections),
                ),
            )
            node_id = cur.lastrowid

            if node.vector is not None:
                cur.execute(
                    "INSERT INTO eb_embeddings(node_id, vector_blob) VALUES (?, ?)",
                    (node_id, _pack_vector(node.vector)),
                )

            self._conn.commit()
            node.node_id = node_id
            return node_id

    def insert_batch(self, nodes: List[Node]) -> List[int]:
        """Insert multiple nodes in a single transaction. Returns list of IDs."""
        ids = []
        with self._lock:
            cur = self._conn.cursor()
            for node in nodes:
                cur.execute(
                    """INSERT INTO eb_nodes
                       (kind, content, tags_json, source_ref, created_at,
                        access_count, goal_id, trust_state, connections_json)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        node.kind.value,
                        node.content,
                        json.dumps(node.tags),
                        node.source_ref,
                        node.created_at,
                        node.access_count,
                        node.goal_id,
                        node.trust_state.value,
                        json.dumps(node.connections),
                    ),
                )
                node_id = cur.lastrowid
                node.node_id = node_id
                ids.append(node_id)

                if node.vector is not None:
                    cur.execute(
                        "INSERT INTO eb_embeddings(node_id, vector_blob) VALUES (?, ?)",
                        (node_id, _pack_vector(node.vector)),
                    )
            self._conn.commit()
        return ids

    def get(self, node_id: int) -> Optional[Node]:
        """Retrieve a single node by ID, or None if missing."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM eb_nodes WHERE node_id=?", (node_id,))
        row = cur.fetchone()
        if row is None:
            return None
        node = self._row_to_node(row)

        cur.execute(
            "SELECT vector_blob FROM eb_embeddings WHERE node_id=?",
            (node_id,),
        )
        vec_row = cur.fetchone()
        if vec_row:
            node.vector = _unpack_vector(vec_row[0])
        return node

    def get_all(self) -> List[Node]:
        """Retrieve all nodes with their embeddings."""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM eb_nodes ORDER BY node_id")
        rows = cur.fetchall()

        # Bulk-load embeddings
        cur.execute("SELECT node_id, vector_blob FROM eb_embeddings")
        vec_map: Dict[int, List[float]] = {}
        for nid, blob in cur.fetchall():
            vec_map[nid] = _unpack_vector(blob)

        nodes = []
        for row in rows:
            node = self._row_to_node(row)
            if node.node_id in vec_map:
                node.vector = vec_map[node.node_id]
            nodes.append(node)
        return nodes

    def get_by_kind(self, kind: NodeKind) -> List[Node]:
        """Retrieve all nodes of a given kind."""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM eb_nodes WHERE kind=? ORDER BY node_id",
            (kind.value,),
        )
        rows = cur.fetchall()

        node_ids = [r[0] for r in rows]
        vec_map = self._load_vectors(node_ids)

        nodes = []
        for row in rows:
            node = self._row_to_node(row)
            if node.node_id in vec_map:
                node.vector = vec_map[node.node_id]
            nodes.append(node)
        return nodes

    def get_connected(self, node_id: int) -> List[Node]:
        """Retrieve all nodes connected to the given node."""
        node = self.get(node_id)
        if node is None or not node.connections:
            return []
        placeholders = ",".join("?" for _ in node.connections)
        cur = self._conn.cursor()
        cur.execute(
            f"SELECT * FROM eb_nodes WHERE node_id IN ({placeholders})",
            node.connections,
        )
        rows = cur.fetchall()
        vec_map = self._load_vectors(node.connections)

        nodes = []
        for row in rows:
            n = self._row_to_node(row)
            if n.node_id in vec_map:
                n.vector = vec_map[n.node_id]
            nodes.append(n)
        return nodes

    def increment_access(self, node_id: int) -> None:
        """Bump access_count by 1."""
        with self._lock:
            self._conn.execute(
                "UPDATE eb_nodes SET access_count = access_count + 1 WHERE node_id=?",
                (node_id,),
            )
            self._conn.commit()

    def increment_access_batch(self, node_ids: List[int]) -> None:
        """Bump access_count for multiple nodes in one transaction."""
        if not node_ids:
            return
        with self._lock:
            cur = self._conn.cursor()
            for nid in node_ids:
                cur.execute(
                    "UPDATE eb_nodes SET access_count = access_count + 1 WHERE node_id=?",
                    (nid,),
                )
            self._conn.commit()

    def update_vector(self, node_id: int, vector: List[float]) -> None:
        """Insert or replace the embedding vector for a node."""
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO eb_embeddings(node_id, vector_blob) VALUES (?, ?)",
                (node_id, _pack_vector(vector)),
            )
            self._conn.commit()

    def add_connection(self, from_id: int, to_id: int) -> None:
        """Add a directed edge from one node to another."""
        with self._lock:
            cur = self._conn.cursor()
            cur.execute(
                "SELECT connections_json FROM eb_nodes WHERE node_id=?",
                (from_id,),
            )
            row = cur.fetchone()
            if row is None:
                return
            conns = json.loads(row[0])
            if to_id not in conns:
                conns.append(to_id)
                cur.execute(
                    "UPDATE eb_nodes SET connections_json=? WHERE node_id=?",
                    (json.dumps(conns), from_id),
                )
                self._conn.commit()

    def delete(self, node_id: int) -> None:
        """Delete a node and its embedding."""
        with self._lock:
            self._conn.execute(
                "DELETE FROM eb_nodes WHERE node_id=?", (node_id,)
            )
            self._conn.commit()

    def count(self) -> int:
        """Return total node count."""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM eb_nodes")
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _row_to_node(self, row: Tuple) -> Node:
        return Node(
            node_id=row[0],
            kind=NodeKind(row[1]),
            content=row[2],
            tags=json.loads(row[3]),
            source_ref=row[4],
            created_at=row[5],
            access_count=row[6],
            goal_id=row[7],
            trust_state=TrustState(row[8]),
            connections=json.loads(row[9]),
            vector=None,  # loaded separately
        )

    def _load_vectors(self, node_ids: List[int]) -> Dict[int, List[float]]:
        if not node_ids:
            return {}
        placeholders = ",".join("?" for _ in node_ids)
        cur = self._conn.cursor()
        cur.execute(
            f"SELECT node_id, vector_blob FROM eb_embeddings WHERE node_id IN ({placeholders})",
            node_ids,
        )
        return {nid: _unpack_vector(blob) for nid, blob in cur.fetchall()}

    def close(self) -> None:
        """Commit and close the database connection."""
        try:
            self._conn.commit()
        except Exception:
            pass
        self._conn.close()
