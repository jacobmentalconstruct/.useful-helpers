"""
SERVICE_NAME: _SessionManagerMS
ROLE: Session Persistence Domain — directory CRUD, metadata/task JSON I/O.
Does NOT know about FAISS, embeddings, UI, Backend, or signals.
"""
import json
import os
import re
import shutil
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional

from .base_service import BaseService
from .microservice_std_lib import service_metadata


@dataclass
class SessionData:
    name: str
    path: str              # abs path to session dir
    vector_path: str       # {path}/vectors.index
    task_path: str         # {path}/tasks.json
    memory_path: str       # {path}/memory.jsonl
    created_at: str
    description: str
    ingested_files: List[str] = field(default_factory=list)
    chunk_count: int = 0
    embed_model: str = "nomic-embed-text"


@service_metadata(
    name='SessionManager',
    version='1.0.0',
    description='Persistence domain: session directory CRUD + metadata/task JSON I/O.',
    tags=['persistence', 'session'],
    capabilities=['session-crud', 'atomic-write'],
    internal_dependencies=['base_service', 'microservice_std_lib'],
    external_dependencies=[],
)
class SessionManagerMS(BaseService):

    def __init__(self, sessions_root: str):
        super().__init__('SessionManager')
        self.sessions_root = os.path.abspath(sessions_root)
        os.makedirs(self.sessions_root, exist_ok=True)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def new_session(self, name: str, description: str = "") -> SessionData:
        """Create a new session directory and write metadata.json."""
        safe = self._sanitize(name)
        path = os.path.join(self.sessions_root, safe)
        if os.path.exists(path):
            raise ValueError(f"Session '{safe}' already exists.")
        os.makedirs(path, exist_ok=True)
        session = self._make_session_data(safe, path, description)
        self._write_metadata(session)
        return session

    def load_session(self, name: str) -> SessionData:
        """Read metadata.json and return a SessionData. Does NOT create FaissStore."""
        safe = self._sanitize(name)
        path = os.path.join(self.sessions_root, safe)
        meta_path = os.path.join(path, "metadata.json")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Session '{safe}' not found.")
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
        return SessionData(
            name=meta['name'],
            path=path,
            vector_path=os.path.join(path, "vectors.index"),
            task_path=os.path.join(path, "tasks.json"),
            memory_path=os.path.join(path, "memory.jsonl"),
            created_at=meta.get('created_at', ''),
            description=meta.get('description', ''),
            ingested_files=meta.get('ingested_files', []),
            chunk_count=meta.get('chunk_count', 0),
            embed_model=meta.get('embed_model', 'nomic-embed-text'),
        )

    def save_session(self, session: SessionData, task_queue: list) -> None:
        """Atomic write of tasks.json and metadata.json."""
        self._atomic_write(session.task_path, task_queue)
        self._write_metadata(session)

    def list_sessions(self) -> List[SessionData]:
        """List all sessions sorted by modification time (newest first)."""
        results = []
        try:
            entries = os.listdir(self.sessions_root)
        except OSError:
            return results
        for entry in entries:
            path = os.path.join(self.sessions_root, entry)
            meta_path = os.path.join(path, "metadata.json")
            if os.path.isdir(path) and os.path.exists(meta_path):
                try:
                    results.append((os.path.getmtime(path), self.load_session(entry)))
                except Exception as e:
                    self.logger.warning(f"Skipping session '{entry}': {e}")
        results.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in results]

    def delete_session(self, name: str) -> None:
        """Remove session directory entirely."""
        safe = self._sanitize(name)
        path = os.path.join(self.sessions_root, safe)
        if os.path.exists(path):
            shutil.rmtree(path)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _sanitize(self, name: str) -> str:
        return re.sub(r'[^\w\-]', '_', name.strip())

    def _make_session_data(self, safe_name: str, path: str, description: str) -> SessionData:
        return SessionData(
            name=safe_name,
            path=path,
            vector_path=os.path.join(path, "vectors.index"),
            task_path=os.path.join(path, "tasks.json"),
            memory_path=os.path.join(path, "memory.jsonl"),
            created_at=datetime.now().isoformat(),
            description=description,
            ingested_files=[],
            chunk_count=0,
            embed_model='nomic-embed-text',
        )

    def _write_metadata(self, session: SessionData) -> None:
        meta = {
            'name': session.name,
            'created_at': session.created_at,
            'description': session.description,
            'ingested_files': session.ingested_files,
            'chunk_count': session.chunk_count,
            'embed_model': session.embed_model,
        }
        self._atomic_write(os.path.join(session.path, "metadata.json"), meta)

    def _atomic_write(self, path: str, data) -> None:
        tmp = path + ".tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            os.replace(tmp, path)
        except Exception as e:
            self.logger.error(f"Atomic write failed for {path}: {e}")
            if os.path.exists(tmp):
                os.remove(tmp)
