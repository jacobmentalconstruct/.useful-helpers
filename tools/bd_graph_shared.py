"""
FILE:       tools/bd_graph_shared.py
ROLE:       Shared BD graph primitives for the T-bd-graph tool pack.
DOMAIN:     tool
DOES:       Splits text into HyperHunk-like records, emits deterministic HyperNode-like
            records, stores them in workspace-local SQLite, and reads query/projection views.
DEPENDS ON: (stdlib) ast, hashlib, json, os, re, sqlite3, pathlib
WIRES TO:   tools/bd_split, bd_emit, bd_scribe, bd_status, bd_query, bd_project, bd_index
NOTES:      A small deterministic substrate: content-addressed hunks, occurrence
            nodes with structural/semantic surfaces, and typed weighted relations.
"""
from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from tools import embed_shared
from tools._toolkit import suite_home

TEXT_EXTENSIONS = {
    ".py", ".md", ".markdown", ".txt", ".rst", ".json", ".yaml", ".yml",
    ".html", ".htm", ".xml", ".js", ".ts", ".tsx", ".jsx", ".css",
}
SKIP_DIRS = {
    ".git", ".venv", "venv", "__pycache__", "_artifacts",
    "node_modules", "build", "dist", ".pytest_cache",
}
REQUIRED_TABLES = {"bd_metadata", "content_nodes", "occurrence_nodes", "relations"}
WORD_RE = re.compile(r"[A-Za-z0-9_]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

ATTENTION_WEIGHTS = {
    "function_definition": 2.0,
    "class_definition": 2.0,
    "method_definition": 1.8,
    "md_heading": 1.5,
    "md_code_block": 1.4,
    "module_preamble": 1.2,
    "paragraph": 1.0,
    "md_paragraph": 1.0,
    "json_document": 1.0,
}

DDL = """
PRAGMA journal_mode=OFF;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS bd_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS content_nodes (
    hunk_id TEXT PRIMARY KEY,
    node_kind TEXT NOT NULL,
    content TEXT NOT NULL,
    attention_weight REAL NOT NULL DEFAULT 1.0,
    static_mass INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS occurrence_nodes (
    occurrence_id TEXT PRIMARY KEY,
    hunk_id TEXT NOT NULL REFERENCES content_nodes(hunk_id),
    origin_id TEXT NOT NULL,
    layer_type TEXT NOT NULL,
    structural_path TEXT NOT NULL DEFAULT '',
    sibling_index INTEGER NOT NULL DEFAULT 0,
    start_line INTEGER NOT NULL DEFAULT 0,
    end_line INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    vector_json TEXT NOT NULL DEFAULT '[]',
    dimensions INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS relations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_occ_id TEXT NOT NULL,
    op TEXT NOT NULL,
    target_occ_id TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 1.0
);

CREATE INDEX IF NOT EXISTS idx_occ_hunk ON occurrence_nodes(hunk_id);
CREATE INDEX IF NOT EXISTS idx_occ_origin ON occurrence_nodes(origin_id);
CREATE INDEX IF NOT EXISTS idx_rel_source ON relations(source_occ_id);
CREATE INDEX IF NOT EXISTS idx_rel_target ON relations(target_occ_id);
"""


def inside(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def workspace_path(value: str | None, default: str = ".") -> Path:
    workspace = Path.cwd().resolve()
    path = (workspace / str(value or default)).resolve()
    if not inside(workspace, path):
        raise ValueError("path must stay inside the workspace")
    return path


def default_db_path() -> Path:
    # The graph DB is generated toolkit state: default it under the toolkit home so the host
    # project stays clean. An explicit `db` arg (below) can still target the work-target cwd.
    return suite_home() / "_artifacts" / "bd_graph" / "cold_anatomy.sqlite3"


def db_path_from_args(args: dict) -> Path:
    raw = args.get("db")
    return workspace_path(str(raw)) if raw else default_db_path()


def safe_read(path: Path, max_bytes: int = 1_000_000) -> str:
    if path.stat().st_size > max_bytes:
        raise ValueError(f"file too large for bd graph split: {path}")
    return path.read_text(encoding="utf-8", errors="replace")


def iter_text_files(root: Path, max_files: int = 250) -> Iterable[Path]:
    if root.is_file():
        if root.suffix.lower() in TEXT_EXTENSIONS:
            yield root
        return
    count = 0
    for current, dir_names, file_names in os.walk(root):
        dir_names[:] = sorted(d for d in dir_names if d not in SKIP_DIRS)
        for name in sorted(file_names):
            path = Path(current) / name
            if path.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            yield path
            count += 1
            if count >= max_files:
                return


def attention_weight(node_kind: str) -> float:
    if node_kind.startswith("fragment_of_"):
        return 0.7
    return ATTENTION_WEIGHTS.get(node_kind, 1.0)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def make_hunk(
    content: str,
    origin_id: str,
    layer_type: str,
    node_kind: str,
    structural_path: str,
    sibling_index: int,
    parent_occurrence_id: str | None = None,
    prev_sibling_occurrence_id: str | None = None,
    metadata: dict | None = None,
) -> dict:
    hunk_id = _sha(f"{node_kind}:{content}")
    occurrence_id = _sha(f"{origin_id}:{structural_path}:{sibling_index}:{hunk_id}")
    return {
        "content": content,
        "origin_id": origin_id,
        "layer_type": layer_type,
        "node_kind": node_kind,
        "structural_path": structural_path,
        "sibling_index": sibling_index,
        "parent_occurrence_id": parent_occurrence_id,
        "prev_sibling_occurrence_id": prev_sibling_occurrence_id,
        "metadata": metadata or {},
        "hunk_id": hunk_id,
        "occurrence_id": occurrence_id,
    }


def _line_slice(lines: list[str], start: int, end: int) -> str:
    return "\n".join(lines[max(start - 1, 0):max(end, start)]).strip()


def _fragment(
    content: str,
    origin_id: str,
    layer_type: str,
    node_kind: str,
    structural_path: str,
    sibling_start: int,
    max_size: int,
    parent: str | None,
    prev: str | None,
    metadata: dict,
) -> list[dict]:
    text = content.strip()
    if not text or (len(text) <= 3 and not WORD_RE.search(text)):
        return []
    if len(text) <= max_size:
        return [make_hunk(text, origin_id, layer_type, node_kind, structural_path,
                          sibling_start, parent, prev, metadata)]

    rows = []
    index = 0
    local_prev = prev
    while text:
        chunk = text[:max_size]
        cut = max(chunk.rfind("\n"), chunk.rfind(" "))
        if cut > max_size // 3:
            chunk = text[:cut]
        text = text[len(chunk):].strip()
        kind = f"fragment_of_{node_kind}"
        path = f"{structural_path}/fragment[{index}]"
        meta = {**metadata, "fragment_index": index}
        row = make_hunk(chunk.strip(), origin_id, layer_type, kind, path,
                        sibling_start + index, parent, local_prev, meta)
        rows.append(row)
        local_prev = row["occurrence_id"]
        index += 1
    return rows


def split_text(text: str, origin_id: str, max_size: int = 1000) -> list[dict]:
    suffix = Path(origin_id).suffix.lower()
    max_size = max(80, min(int(max_size), 50_000))
    if suffix == ".py":
        return _split_python(text, origin_id, max_size)
    if suffix in {".md", ".markdown", ".rst"}:
        return _split_markdown(text, origin_id, max_size)
    node_kind = "json_document" if suffix == ".json" else "paragraph"
    return _split_paragraphs(text, origin_id, "REGEX", node_kind, "doc", max_size)


def _split_python(text: str, origin_id: str, max_size: int) -> list[dict]:
    lines = text.splitlines()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _split_paragraphs(text, origin_id, "CHAR", "paragraph", "doc", max_size)

    rows: list[dict] = []
    prev = None
    top_nodes = [n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]
    first_line = min((getattr(n, "lineno", 1) for n in top_nodes), default=1)
    if first_line > 1:
        preamble = _line_slice(lines, 1, first_line - 1)
        part = _fragment(preamble, origin_id, "AST", "module_preamble", "module/preamble",
                         0, max_size, None, prev, {"line_start": 1, "line_end": first_line - 1})
        rows.extend(part)
        if part:
            prev = part[-1]["occurrence_id"]

    sibling = len(rows)
    for node in top_nodes:
        kind = "class_definition" if isinstance(node, ast.ClassDef) else "function_definition"
        name = getattr(node, "name", "symbol")
        end = getattr(node, "end_lineno", getattr(node, "lineno", 1))
        content = _line_slice(lines, getattr(node, "lineno", 1), end)
        path = f"module/{kind}:{name}"
        part = _fragment(content, origin_id, "AST", kind, path, sibling, max_size, None, prev,
                         {"name": name, "line_start": getattr(node, "lineno", 1), "line_end": end})
        rows.extend(part)
        if part:
            prev = part[-1]["occurrence_id"]
            sibling += len(part)
    if not rows:
        return _split_paragraphs(text, origin_id, "REGEX", "paragraph", "doc", max_size)
    return rows


def _split_markdown(text: str, origin_id: str, max_size: int) -> list[dict]:
    rows = []
    current_title = "intro"
    current_lines: list[str] = []
    current_start = 1
    sibling = 0
    prev = None

    def flush(end_line: int) -> None:
        nonlocal sibling, prev, current_lines
        block = "\n".join(current_lines).strip()
        if not block:
            current_lines = []
            return
        path = f"doc/{current_title}"
        part = _fragment(block, origin_id, "CST", "md_paragraph", path, sibling,
                         max_size, None, prev,
                         {"heading": current_title, "line_start": current_start, "line_end": end_line})
        rows.extend(part)
        if part:
            prev = part[-1]["occurrence_id"]
            sibling += len(part)
        current_lines = []

    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        match = HEADING_RE.match(line)
        if match:
            flush(i - 1)
            title = match.group(2).strip()
            hunk = make_hunk(line.strip(), origin_id, "CST", "md_heading",
                             f"doc/heading:{title}", sibling, None, prev,
                             {"level": len(match.group(1)), "heading": title,
                              "line_start": i, "line_end": i})
            rows.append(hunk)
            prev = hunk["occurrence_id"]
            sibling += 1
            current_title = title
        else:
            if not current_lines:
                current_start = i
            current_lines.append(line)
    flush(len(lines))
    return rows or _split_paragraphs(text, origin_id, "REGEX", "paragraph", "doc", max_size)


def _split_paragraphs(text: str, origin_id: str, layer_type: str, node_kind: str,
                      base_path: str, max_size: int) -> list[dict]:
    rows = []
    prev = None
    # Keep each paragraph's char offset so we can report its 1-based line range (Gb).
    paras: list[tuple[str, int]] = []
    for m in re.finditer(r"(.+?)(?:\n\s*\n+|\Z)", text, re.S):
        chunk = m.group(1).strip()
        if chunk:
            paras.append((chunk, m.start(1)))
    if not paras and text.strip():
        paras = [(text.strip(), 0)]
    for idx, (para, offset) in enumerate(paras):
        line_start = text.count("\n", 0, offset) + 1
        meta = {"paragraph_index": idx, "line_start": line_start,
                "line_end": line_start + para.count("\n")}
        part = _fragment(para, origin_id, layer_type, node_kind, f"{base_path}/paragraph[{idx}]",
                         len(rows), max_size, None, prev, meta)
        rows.extend(part)
        if part:
            prev = part[-1]["occurrence_id"]
    return rows


def split_path(path: Path, max_size: int = 1000, max_files: int = 250,
               limit: int = 2000) -> list[dict]:
    workspace = Path.cwd().resolve()
    rows: list[dict] = []
    for file in iter_text_files(path, max_files=max_files):
        rel = file.relative_to(workspace).as_posix() if inside(workspace, file) else file.as_posix()
        rows.extend(split_text(safe_read(file), rel, max_size=max_size))
        if len(rows) >= limit:
            return rows[:limit]
    return rows


def tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in WORD_RE.finditer(text)]


def emit_node(hunk: dict, dimensions: int = 16, vector_cache: dict | None = None) -> dict:
    content = str(hunk.get("content") or "")
    node_kind = str(hunk.get("node_kind") or "paragraph")
    symbols = tokenize(content)
    meta = hunk.get("metadata") or {}
    hunk_id = hunk.get("hunk_id") or _sha(f"{node_kind}:{content}")
    # CAS reuse: a hunk_id is a content hash, so if the SAME content is already embedded (in a
    # prior index of this DB, same backend), reuse that vector instead of paying Ollama again.
    # The caller only supplies a cache when its backend matches the current one, so the tag is
    # safe. Otherwise embed for real (Ollama when reachable, lexical fallback). (Ga + review.)
    if vector_cache is not None and hunk_id in vector_cache:
        vector, backend = vector_cache[hunk_id], embed_shared.current_backend()
    else:
        vector, backend = embed_shared.embed(content)
    return {
        "hunk_id": hunk_id,
        "occurrence_id": hunk.get("occurrence_id") or _sha(
            f"{hunk.get('origin_id')}:{hunk.get('structural_path')}:{hunk.get('sibling_index')}:{hunk.get('hunk_id')}"
        ),
        "attention_weight": attention_weight(node_kind),
        "start_line": int(meta.get("line_start") or 0),  # Gb: so expand() can cite file:Lx-Ly
        "end_line": int(meta.get("line_end") or 0),
        "verbatim": {
            "content_id": "sha256:" + str(hunk.get("hunk_id") or _sha(f"{node_kind}:{content}")),
            "content": content,
            "symbols": symbols,
            "node_kind": node_kind,
        },
        "structural": {
            "origin_id": hunk.get("origin_id") or "",
            "layer_type": hunk.get("layer_type") or "REGEX",
            "structural_path": hunk.get("structural_path") or "",
            "sibling_index": int(hunk.get("sibling_index") or 0),
            "parent_occurrence_id": hunk.get("parent_occurrence_id"),
            "prev_sibling_occurrence_id": hunk.get("prev_sibling_occurrence_id"),
            "metadata": hunk.get("metadata") or {},
        },
        "vector": {"vector": vector, "dimensions": len(vector), "backend": backend},
    }


def emit_nodes(hunks: list[dict], dimensions: int = 16, limit: int = 2000,
               vector_cache: dict | None = None) -> list[dict]:
    return [emit_node(h, dimensions=dimensions, vector_cache=vector_cache)
            for h in hunks[:max(1, min(limit, 10_000))]]


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(DDL)
    # Migrate a pre-Gb DB in place: CREATE TABLE IF NOT EXISTS won't add columns to an existing
    # table, so add start_line/end_line if they're missing (graph DBs are disposable, but be kind).
    cols = {r[1] for r in conn.execute("PRAGMA table_info(occurrence_nodes)")}
    for col in ("start_line", "end_line"):
        if col not in cols:
            conn.execute(f"ALTER TABLE occurrence_nodes ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0")
    conn.execute("INSERT OR REPLACE INTO bd_metadata(key, value) VALUES('schema', 'bd_graph_v2')")
    return conn


def ingest_nodes(path: Path, nodes: list[dict]) -> dict:
    # Record the embedding backend so query_db embeds questions in the SAME space. If nodes carry
    # more than one (Ollama died mid-run), the real one wins  -  lexical vectors just rank low then.
    backends = [str((n.get("vector") or {}).get("backend") or "") for n in nodes]
    backends = [b for b in backends if b]
    chosen = next((b for b in backends if b.startswith("ollama:")), backends[0] if backends else "")
    with open_db(path) as conn:
        if chosen:
            conn.execute("INSERT OR REPLACE INTO bd_metadata(key, value) VALUES('embed_backend', ?)",
                         (chosen,))
        for node in nodes:
            verbatim = node.get("verbatim") or {}
            structural = node.get("structural") or {}
            vector = node.get("vector") or {}
            hunk_id = str(node.get("hunk_id"))
            occurrence_id = str(node.get("occurrence_id"))
            content = str(verbatim.get("content") or "")
            node_kind = str(verbatim.get("node_kind") or "paragraph")
            conn.execute(
                """INSERT INTO content_nodes(hunk_id, node_kind, content, attention_weight)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(hunk_id) DO NOTHING""",
                (hunk_id, node_kind, content, float(node.get("attention_weight", 1.0))),
            )
            conn.execute(
                """INSERT INTO occurrence_nodes
                   (occurrence_id, hunk_id, origin_id, layer_type, structural_path,
                    sibling_index, start_line, end_line, metadata_json, vector_json, dimensions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(occurrence_id) DO NOTHING""",
                (
                    occurrence_id, hunk_id, str(structural.get("origin_id") or ""),
                    str(structural.get("layer_type") or ""), str(structural.get("structural_path") or ""),
                    int(structural.get("sibling_index") or 0),
                    int(node.get("start_line") or 0), int(node.get("end_line") or 0),
                    json.dumps(structural.get("metadata") or {}, sort_keys=True),
                    json.dumps(vector.get("vector") or []),
                    int(vector.get("dimensions") or 0),
                ),
            )
            parent = structural.get("parent_occurrence_id")
            prev = structural.get("prev_sibling_occurrence_id")
            if parent:
                conn.execute(
                    "INSERT INTO relations(source_occ_id, op, target_occ_id, weight) VALUES (?, 'pull', ?, 1.0)",
                    (occurrence_id, str(parent)),
                )
            if prev:
                conn.execute(
                    "INSERT INTO relations(source_occ_id, op, target_occ_id, weight) VALUES (?, 'precedes', ?, 0.8)",
                    (occurrence_id, str(prev)),
                )
        conn.execute(
            """UPDATE content_nodes
               SET static_mass = (
                   SELECT COUNT(*) FROM occurrence_nodes o
                   WHERE o.hunk_id = content_nodes.hunk_id
               )"""
        )
        conn.commit()
    return db_status(path)


def db_status(path: Path) -> dict:
    if not path.exists():
        return {"exists": False, "content_nodes": 0, "occurrence_nodes": 0, "relations": 0}
    with sqlite3.connect(str(path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        counts = {"exists": True, "path": path.as_posix(), "tables": sorted(tables),
                  "missing_tables": sorted(REQUIRED_TABLES - tables)}
        for table in sorted(REQUIRED_TABLES & tables):
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return counts


def _citation(origin_id: str, start_line: int, end_line: int) -> str:
    """A source citation an agent can open: `path:Lx-Ly` (or `path` when lines are unknown)."""
    if start_line and end_line and end_line >= start_line:
        return f"{origin_id}:L{start_line}-L{end_line}" if end_line > start_line else f"{origin_id}:L{start_line}"
    return origin_id


# ---------------------------------------------------------------- knowledge layer (Ge)
# Journal entries and evidence items become KNOWLEDGE nodes linked to the code they touch, so
# `why(path_or_symbol)` traverses from code to the decisions/proof that shaped it. This is the
# difference between a code index and project memory (field report G7).

def _path_match(origin: str, ref: str) -> bool:
    """True if two file paths refer to the same file  -  exact, or one a path-suffix of the other
    (handles `app/cli.py` recorded as `cli.py`, etc.). Suffix, never bare basename, to avoid
    linking every `cli.py` in a repo to one another."""
    o, r = origin.strip().strip("./"), ref.strip().strip("./")
    if not o or not r:
        return False
    return o == r or o.endswith("/" + r) or r.endswith("/" + o)


def _journal_text(entry: dict) -> str:
    parts = [str(entry.get("title") or ""), str(entry.get("summary") or "")]
    decisions = entry.get("decisions") or []
    if decisions:
        parts.append("Decisions:\n" + "\n".join(f"- {d}" for d in decisions))
    return "\n\n".join(p for p in parts if p.strip())


def _as_paths(value) -> list[str]:
    if not value:
        return []
    return [str(x) for x in value] if isinstance(value, list) else [str(value)]


def read_state_journal(state_db: Path) -> list[dict]:
    """Journal entries from a state DB (list-fields decoded). [] if absent/empty."""
    if not state_db.exists():
        return []
    with sqlite3.connect(str(state_db)) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT * FROM journal_entries ORDER BY entry_no").fetchall()
        except sqlite3.Error:  # missing table OR a corrupt/foreign file  -  treat as empty
            return []
    out = []
    for r in rows:
        d = dict(r)
        for k in ("files_changed", "decisions", "backlog"):
            d[k] = json.loads(d[k]) if d.get(k) else []
        out.append(d)
    return out


def read_state_evidence(state_db: Path) -> list[dict]:
    """Evidence items from a state DB. [] if absent/empty."""
    if not state_db.exists():
        return []
    with sqlite3.connect(str(state_db)) as conn:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute("SELECT * FROM evidence ORDER BY created_at").fetchall()
        except sqlite3.Error:  # missing table OR a corrupt/foreign file  -  treat as empty
            return []
    return [dict(r) for r in rows]


def _knowledge_node(origin_id: str, node_kind: str, structural_path: str,
                    content: str, metadata: dict) -> dict:
    hunk = make_hunk(content or origin_id, origin_id, "KNOWLEDGE", node_kind,
                     structural_path, 0, metadata=metadata)
    return emit_node(hunk)


def ingest_knowledge(path: Path, journal_rows: list[dict], evidence_rows: list[dict],
                     link_cap: int = 50) -> dict:
    """Ingest journal/evidence as KNOWLEDGE nodes and link each to the code it references
    (`relates_to` edges, capped per node). Idempotent: re-running dedups on content hash and
    ON CONFLICT, and edges are de-duplicated below."""
    nodes: list[dict] = []
    refs: list[tuple[str, list[str]]] = []  # (knowledge occurrence_id, referenced paths)

    for e in journal_rows:
        uid = str(e.get("uid") or "")
        node = _knowledge_node(
            f"journal:{uid}", "journal_entry",
            f"journal/{e.get('entry_no')}:{e.get('title', '')}", _journal_text(e),
            {"kind": "journal_entry", "uid": uid, "entry_no": e.get("entry_no"),
             "title": e.get("title", ""), "status": e.get("status")})
        nodes.append(node)
        refs.append((node["occurrence_id"], _as_paths(e.get("files_changed"))))

    for ev in evidence_rows:
        eid = str(ev.get("evidence_id") or "")
        node = _knowledge_node(
            f"evidence:{eid}", "evidence_item", f"evidence/{eid}",
            f"[{ev.get('kind')}] {ev.get('summary', '')}",
            {"kind": "evidence_item", "evidence_id": eid, "ev_kind": ev.get("kind"),
             "source_path": ev.get("source_path"), "attached_to": ev.get("attached_to")})
        nodes.append(node)
        refs.append((node["occurrence_id"], _as_paths(ev.get("source_path"))))

    if nodes:
        ingest_nodes(path, nodes)

    edges = 0
    with open_db(path) as conn:
        code = [(str(o), str(oid)) for o, oid in conn.execute(
            "SELECT occurrence_id, origin_id FROM occurrence_nodes WHERE layer_type != 'KNOWLEDGE'")]
        existing = {(s, t) for s, t in conn.execute(
            "SELECT source_occ_id, target_occ_id FROM relations WHERE op='relates_to'")}
        for know_occ, paths in refs:
            linked = 0
            for p in paths:
                for occ, origin in code:
                    if linked >= link_cap:
                        break
                    if _path_match(origin, p) and (know_occ, occ) not in existing:
                        conn.execute(
                            "INSERT INTO relations(source_occ_id, op, target_occ_id, weight) "
                            "VALUES (?, 'relates_to', ?, 1.0)", (know_occ, occ))
                        existing.add((know_occ, occ))
                        edges += 1
                        linked += 1
        conn.commit()
    return {"knowledge_nodes": len(nodes), "relations_added": edges, "status": db_status(path)}


def why_db(path: Path, target: str, limit: int = 20) -> dict:
    """From a code path/symbol, return the knowledge (decisions/evidence) linked to it."""
    if not path.exists():
        return {"target": target, "code_matches": 0, "knowledge": []}
    with sqlite3.connect(str(path)) as conn:
        code = [str(occ) for occ, origin, spath in conn.execute(
            "SELECT occurrence_id, origin_id, structural_path FROM occurrence_nodes "
            "WHERE layer_type != 'KNOWLEDGE'")
            if _path_match(str(origin), target) or target in str(spath)]
        if not code:
            return {"target": target, "code_matches": 0, "knowledge": []}
        ph = ",".join("?" * len(code))
        know = set()
        for (k,) in conn.execute(
            f"SELECT DISTINCT source_occ_id FROM relations "
            f"WHERE op='relates_to' AND target_occ_id IN ({ph})", code):
            know.add(k)
        for (k,) in conn.execute(
            f"SELECT DISTINCT target_occ_id FROM relations "
            f"WHERE op='relates_to' AND source_occ_id IN ({ph})", code):
            know.add(k)
        if not know:
            return {"target": target, "code_matches": len(code), "knowledge": []}
        kph = ",".join("?" * len(know))
        rows = conn.execute(
            f"""SELECT o.origin_id, o.structural_path, o.metadata_json, c.node_kind, c.content
                FROM occurrence_nodes o JOIN content_nodes c ON c.hunk_id = o.hunk_id
                WHERE o.occurrence_id IN ({kph})""", list(know)).fetchall()
    knowledge = [{
        "origin_id": r[0], "structural_path": r[1], "node_kind": r[3],
        "summary": str(r[4])[:400],
        "metadata": json.loads(r[2] or "{}"),
    } for r in rows][:max(1, min(int(limit), 200))]
    knowledge.sort(key=lambda k: k["origin_id"])
    return {"target": target, "code_matches": len(code), "knowledge": knowledge}


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        # Different-length vectors are different spaces (e.g. a lexical query vs Ollama-stored
        # vectors after Ollama went away). zip() would silently truncate and score garbage; say 0.
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if not na or not nb:
        return 0.0
    return dot / (na * nb)


def _read_metadata(conn, key: str, default: str = "") -> str:
    row = conn.execute("SELECT value FROM bd_metadata WHERE key = ?", (key,)).fetchone()
    return str(row[0]) if row else default


def current_embed_backend() -> str:
    """The embedding backend this process would use right now (ollama:... or lexical:...)."""
    return embed_shared.current_backend()


def load_reusable_vectors(path: Path) -> dict:
    """Vectors from an existing DB that are safe to reuse on a re-index  -  i.e. it was built with
    the SAME backend this process would use now. Empty when the DB is absent or its backend
    differs (a lexical->ollama upgrade, say), which correctly forces a full re-embed.

    This is the CAS "free lunch": a content-hash (hunk_id) already embedded is never re-embedded.
    """
    if not path.exists():
        return {}
    with sqlite3.connect(str(path)) as conn:
        tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "occurrence_nodes" not in tables:
            return {}
        if _read_metadata(conn, "embed_backend", "") != current_embed_backend():
            return {}
        cache: dict[str, list[float]] = {}
        for hid, vjson in conn.execute("SELECT hunk_id, vector_json FROM occurrence_nodes"):
            if hid in cache:
                continue
            try:
                vec = json.loads(vjson or "[]")
            except json.JSONDecodeError:
                continue
            if vec:
                cache[str(hid)] = vec
    return cache


def query_db(path: Path, query: str, top_k: int = 8, hops: int = 1) -> dict:
    q_tokens = set(tokenize(query))
    rows = []
    with sqlite3.connect(str(path)) as conn:
        # Embed the query in the SAME backend the index was built with, so cosine compares like
        # with like. Semantic when the index is real; lexical when it is a fallback index.
        backend = _read_metadata(conn, "embed_backend", embed_shared.LEXICAL_BACKEND)
        q_vec, actual = embed_shared.embed_in_backend(query, backend)
        # Semantic only if the query embedded in the SAME space the index was built in. If the
        # index is ollama: but Ollama is gone now, `actual` is lexical and cosine will be 0
        # (dim guard)  -  we fall back to keyword ranking and report the degradation honestly.
        semantic = backend.startswith("ollama:") and actual == backend
        degraded = backend.startswith("ollama:") and not semantic
        for row in conn.execute(
            """SELECT o.occurrence_id, o.hunk_id, o.origin_id, o.layer_type,
                      o.structural_path, c.node_kind, c.content, c.attention_weight,
                      c.static_mass, o.vector_json, o.start_line, o.end_line
               FROM occurrence_nodes o
               JOIN content_nodes c ON c.hunk_id = o.hunk_id"""
        ):
            content = str(row[6])
            c_tokens = set(tokenize(content))
            overlap = len(q_tokens & c_tokens) / max(len(q_tokens), 1)  # 0..1
            phrase = 1.0 if query.lower() in content.lower() else 0.0
            try:
                cos = _cosine(q_vec, json.loads(row[9] or "[]"))
            except json.JSONDecodeError:
                cos = 0.0
            # Semantic index: cosine leads (paraphrase-tolerant), keyword overlap refines.
            # Lexical index: overlap leads, the (lexical) cosine only refines. Field report Ga.
            if semantic:
                score = 0.60 * cos + 0.30 * overlap + 0.10 * phrase + 0.02 * float(row[7])
            else:
                score = 0.55 * overlap + 0.30 * cos + 0.15 * phrase + 0.02 * float(row[7])
            start_line, end_line = int(row[10] or 0), int(row[11] or 0)
            rows.append({
                "occurrence_id": row[0],
                "hunk_id": row[1],
                "origin_id": row[2],
                "layer_type": row[3],
                "structural_path": row[4],
                "node_kind": row[5],
                "score": round(score, 6),
                "cosine": round(cos, 4),
                "start_line": start_line,
                "end_line": end_line,
                "citation": _citation(row[2], start_line, end_line),
                "content_snippet": content[:240],
                "static_mass": row[8],
            })
    rows.sort(key=lambda r: (-r["score"], r["origin_id"], r["structural_path"]))
    anchors = rows[:max(1, min(int(top_k), 100))]
    graph = project_db(path, [a["occurrence_id"] for a in anchors], hops=hops, include_content=False)
    retrieval = {"backend": backend, "semantic": semantic}
    if degraded:
        retrieval["degraded"] = "index is semantic but no embedding backend is reachable now; " \
                                "ranking fell back to keyword overlap"
    return {"anchors": anchors, "graph": graph, "retrieval": retrieval,
            "summary": {"anchors": len(anchors), "nodes": len(graph["nodes"]),
                        "edges": len(graph["edges"]), "query_tokens": sorted(q_tokens)}}


def project_db(path: Path, occurrence_ids: list[str], hops: int = 2,
               include_content: bool = True) -> dict:
    if not occurrence_ids:
        return {"nodes": [], "edges": [], "summary": {"nodes": 0, "edges": 0}}
    hops = max(0, min(int(hops), 6))
    visited = set(occurrence_ids)
    frontier = set(occurrence_ids)
    with sqlite3.connect(str(path)) as conn:
        for _ in range(hops):
            if not frontier:
                break
            placeholders = ",".join("?" * len(frontier))
            neighbours = conn.execute(
                f"""SELECT DISTINCT target_occ_id FROM relations
                    WHERE source_occ_id IN ({placeholders})
                    UNION
                    SELECT DISTINCT source_occ_id FROM relations
                    WHERE target_occ_id IN ({placeholders})""",
                list(frontier) + list(frontier),
            ).fetchall()
            new_nodes = {row[0] for row in neighbours} - visited
            visited |= new_nodes
            frontier = new_nodes
        placeholders = ",".join("?" * len(visited))
        node_rows = conn.execute(
            f"""SELECT o.occurrence_id, o.hunk_id, o.origin_id, o.layer_type,
                      o.structural_path, o.sibling_index, c.node_kind, c.content,
                      c.attention_weight, c.static_mass, o.start_line, o.end_line
               FROM occurrence_nodes o
               JOIN content_nodes c ON c.hunk_id = o.hunk_id
               WHERE o.occurrence_id IN ({placeholders})""",
            list(visited),
        ).fetchall()
        edge_rows = conn.execute(
            f"""SELECT source_occ_id, op, target_occ_id, weight
                FROM relations
                WHERE source_occ_id IN ({placeholders})
                  AND target_occ_id IN ({placeholders})""",
            list(visited) + list(visited),
        ).fetchall()
    nodes = []
    for row in node_rows:
        start_line, end_line = int(row[10] or 0), int(row[11] or 0)
        item = {
            "occurrence_id": row[0],
            "hunk_id": row[1],
            "origin_id": row[2],
            "layer_type": row[3],
            "structural_path": row[4],
            "sibling_index": row[5],
            "node_kind": row[6],
            "attention_weight": row[8],
            "static_mass": row[9],
            "start_line": start_line,
            "end_line": end_line,
            "citation": _citation(row[2], start_line, end_line),
        }
        item["content" if include_content else "content_snippet"] = row[7] if include_content else row[7][:160]
        nodes.append(item)
    edges = [
        {"source_occurrence_id": row[0], "op": row[1], "target_occurrence_id": row[2], "weight": row[3]}
        for row in edge_rows
    ]
    return {"nodes": sorted(nodes, key=lambda n: (n["origin_id"], n["sibling_index"])),
            "edges": edges, "summary": {"nodes": len(nodes), "edges": len(edges), "hops": hops}}
