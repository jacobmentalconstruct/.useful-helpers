import sqlite3
import os
import json
import logging
import threading
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from src.microservices._IngestEngineMS import IngestEngineMS
from src.microservices._FeedbackValidationMS import FeedbackValidationMS
from src.microservices._SignalBusMS import SignalBusMS
from src.microservices._CognitiveMemoryMS import CognitiveMemoryMS
from src.microservices._HydrationFactoryMS import HydrationFactoryMS
from src.microservices._ErrorNotifierMS import ErrorNotifierMS
from src.microservices._ConfigStoreMS import ConfigStoreMS
from src.microservices._CodeFormatterMS import CodeFormatterMS
from src.microservices._TreeMapperMS import TreeMapperMS
from src.microservices._VectorFactoryMS import VectorFactoryMS
from src.microservices._SemanticChunkerMS import SemanticChunkerMS
from src.microservices._SessionManagerMS import SessionManagerMS, SessionData
from src.microservices._IngestPipelineMS import IngestPipelineMS
from src.microservices._RAGRetrievalMS import RAGRetrievalMS
from src.microservices.microservice_std_lib import service_metadata
from src.cell_identity import CellIdentity


class _NullStore:
    """Drop-in replacement when FAISS is unavailable. RAG silently disabled."""
    def add(self, embeddings, metadatas): pass
    def search(self, query_vector, k): return []
    def count(self): return 0
    def clear(self): pass


class Backend:
    """
    ROLE: Orchestration / Logic Hub — pure downstream task list runner.
    SERVICES: Ingest, Validation, SignalBus, Memory, Factory, Notifier, ConfigStore
    STATE: Persistent (SQLite / JSON)
    """
    def __init__(self, db_path: str = None, memory_path: str = None,
                 cell_id: str = None, cell_name: str = None):
        # BOOTSTRAP: Define persistence paths
        project_root = os.path.abspath(os.getcwd())
        db_dir = os.path.join(project_root, "_db")
        os.makedirs(db_dir, exist_ok=True)

        # IDENTITY
        self.identity = CellIdentity(cell_id, cell_name)
        self.cell_id = self.identity.cell_id
        self.cell_name = self.identity.cell_name

        if db_path is None:
            db_path = os.path.join(db_dir, "app_internal.db")

        self.db_path = db_path
        self.logger = logging.getLogger(self.__class__.__name__)
        self._init_db()

        self.engine = IngestEngineMS()
        self.validator = FeedbackValidationMS()
        self.bus = SignalBusMS()
        self.notifier = ErrorNotifierMS(self.bus)
        self.config_store = ConfigStoreMS()

        # BOOTSTRAP: Initialize Specialists (orchestration-owned)
        self.formatter = CodeFormatterMS()
        self.mapper = TreeMapperMS()
        self.vector_factory = VectorFactoryMS()

        # DI: Package and inject services into the Fabricator
        specialists = {
            'formatter': self.formatter,
            'mapper': self.mapper,
            'vector_factory': self.vector_factory,
            'ingest_engine': self.engine
        }
        self.factory = HydrationFactoryMS(services=specialists)

        # Configure memory with Long-Term flush capability
        mem_config = {
            'persistence_path': memory_path,
            'summarizer_func': self._summarize_memory_stub,
            'long_term_ingest_func': self._flush_to_vector_db
        } if memory_path else {
            'summarizer_func': self._summarize_memory_stub,
            'long_term_ingest_func': self._flush_to_vector_db
        }
        self.memory = CognitiveMemoryMS(config=mem_config)

        # Initialize state from persistent storage
        self.system_role: str = self.get_setting('last_system_role') or "You are a helpful AI assistant."

        # RAG / SESSION services
        self.session_manager = SessionManagerMS(os.path.join(project_root, "_sessions"))
        self.ingest_pipeline = IngestPipelineMS(
            chunker=SemanticChunkerMS(),
            ingest_engine=self.engine,
        )
        self.rag_retrieval = RAGRetrievalMS(ingest_engine=self.engine)

        # Bootstrap active session
        last_name = self.config_store.get('last_session_name')
        self.current_session: SessionData = self._resolve_startup_session(last_name)
        self.current_store = self._create_store(self.current_session.vector_path)

        # TASK QUEUE: ordered list of task dicts
        # Each task: { label, model, role, system_prompt, user_content }
        self.task_queue: list = self._load_task_queue()
        self._queue_running: bool = False

    # -------------------------------------------------------------------------
    # Models
    # -------------------------------------------------------------------------

    def get_models(self):
        """Fetches available Ollama models."""
        models = self.engine.get_available_models()
        return models if models else ["No Models Found"]

    def set_system_role(self, role_text: str) -> None:
        self.system_role = role_text
        self.save_setting('last_system_role', role_text)

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------

    def _init_db(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.executescript("""
                    CREATE TABLE IF NOT EXISTS personas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        role_text TEXT,
                        sys_prompt_text TEXT,
                        task_prompt_text TEXT,
                        is_default INTEGER DEFAULT 0,
                        last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                    CREATE TABLE IF NOT EXISTS saved_roles (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, content TEXT, is_default INTEGER DEFAULT 0);
                    CREATE TABLE IF NOT EXISTS saved_sys_prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, content TEXT, is_default INTEGER DEFAULT 0);
                    CREATE TABLE IF NOT EXISTS saved_task_prompts (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, content TEXT, is_default INTEGER DEFAULT 0);
                """)

                try:
                    cols = {row[1] for row in conn.execute("PRAGMA table_info(personas)").fetchall()}
                    if 'task_prompt_text' not in cols:
                        conn.execute("ALTER TABLE personas ADD COLUMN task_prompt_text TEXT")
                    if 'last_modified' not in cols:
                        conn.execute("ALTER TABLE personas ADD COLUMN last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    if 'is_default' not in cols:
                        conn.execute("ALTER TABLE personas ADD COLUMN is_default INTEGER DEFAULT 0")
                except sqlite3.Error as mig_e:
                    self.logger.error(f"Personas migration failed: {mig_e}")

        except sqlite3.Error as e:
            self.logger.error(f"Database initialization failed: {e}")

    def save_setting(self, key: str, value: Any) -> None:
        self.config_store.set(key, value)

    def get_setting(self, key: str) -> Optional[Any]:
        return self.config_store.get(key)

    def save_persona(self, name: str, role: str, sys_prompt: str, task_prompt: str = "", is_default: bool = False) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                if is_default:
                    conn.execute("UPDATE personas SET is_default = 0")
                conn.execute(
                    """
                    INSERT INTO personas (name, role_text, sys_prompt_text, task_prompt_text, is_default, last_modified)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        role_text=excluded.role_text,
                        sys_prompt_text=excluded.sys_prompt_text,
                        task_prompt_text=excluded.task_prompt_text,
                        is_default=excluded.is_default,
                        last_modified=excluded.last_modified
                    """,
                    (name, role, sys_prompt, task_prompt, 1 if is_default else 0, datetime.now().isoformat())
                )
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Failed to save persona '{name}': {e}")
            return False

    def get_default_item(self, table_name: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            col = "role_text" if table_name == 'personas' else "content"
            res = conn.execute(f"SELECT {col} FROM {table_name} WHERE is_default = 1").fetchone()
            return res[0] if res else None

    def get_repository_items(self, table_name: str) -> List[Tuple[int, str, str, int]]:
        valid_tables = ['saved_roles', 'saved_sys_prompts', 'saved_task_prompts', 'personas']
        if table_name not in valid_tables:
            return []
        with sqlite3.connect(self.db_path) as conn:
            if table_name == 'personas':
                return conn.execute("SELECT id, name, role_text, is_default FROM personas ORDER BY name ASC").fetchall()
            return conn.execute(f"SELECT id, name, content, is_default FROM {table_name} ORDER BY name ASC").fetchall()

    def save_repository_item(self, table_name: str, name: str, content: str, is_default: bool = False) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                if is_default:
                    conn.execute(f"UPDATE {table_name} SET is_default = 0")
                conn.execute(f"INSERT OR REPLACE INTO {table_name} (name, content, is_default) VALUES (?, ?, ?)",
                             (name, content, 1 if is_default else 0))
            return True
        except sqlite3.Error as e:
            self.logger.error(f"Repo save failed for {table_name}: {e}")
            return False

    def set_as_default(self, table_name: str, item_id: int) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"UPDATE {table_name} SET is_default = 0")
            conn.execute(f"UPDATE {table_name} SET is_default = 1 WHERE id = ?", (item_id,))

    def delete_repository_item(self, table_name: str, item_id: int) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(f"DELETE FROM {table_name} WHERE id = ?", (item_id,))
            return True
        except sqlite3.Error:
            return False

    # -------------------------------------------------------------------------
    # Single-task inference
    # -------------------------------------------------------------------------

    def process_submission(self, content: str, model: str, role: str, prompt: str, inherited_context: str = "") -> Dict[str, Any]:
        artifact = {
            "metadata": {
                "model": model,
                "timestamp": datetime.now().isoformat(),
                "source": "_theCELL_Task_Runner",
                "version": "2.0.0"
            },
            "instructions": {
                "system_role": role,
                "system_prompt": prompt,
                "inherited_context": inherited_context
            },
            "payload": content.strip()
        }

        self.memory.add_entry(role="user", content=content, metadata=artifact['metadata'])
        self.logger.info(f"Artifact generated for model: {model}")
        self.bus.emit(SignalBusMS.SIGNAL_PROCESS_START, artifact)

        thread = threading.Thread(target=self._run_inference_thread, args=(artifact,))
        thread.daemon = True
        thread.start()

        return artifact

    def _run_inference_thread(self, artifact: Dict[str, Any]):
        try:
            model = artifact['metadata']['model']
            sys_role = artifact['instructions']['system_role']
            sys_prompt = artifact['instructions']['system_prompt']
            inherited = artifact['instructions'].get('inherited_context', '')
            user_payload = artifact['payload']

            full_system = f"ROLE: {sys_role}\n\nSYSTEM INSTRUCTIONS:\n{sys_prompt}".strip()

            # RAG: retrieve relevant context from active session store
            embed_model = self.config_store.get('embed_model') or 'nomic-embed-text'
            rag_context = self.rag_retrieval.retrieve(user_payload, self.current_store, embed_model)

            if rag_context and inherited:
                user_payload = f"TASK: {user_payload}\n\n{rag_context}\n\n### PREVIOUS OUTPUT ###\n{inherited}"
            elif rag_context:
                user_payload = f"TASK: {user_payload}\n\n{rag_context}"
            elif inherited:
                user_payload = f"TASK: {user_payload}\n\n### REFERENCE CONTEXT (PREVIOUS OUTPUT) ###\n{inherited}"

            response_buffer = []
            stream = self.engine.generate_stream(prompt=user_payload, model=model, system=full_system)

            for token in stream:
                self.bus.emit(SignalBusMS.SIGNAL_LOG_APPEND, token)
                response_buffer.append(token)

            final_response = "".join(response_buffer)
            artifact['response'] = final_response

            self.memory.add_entry(role="assistant", content=final_response, metadata=artifact['metadata'])
            self.bus.emit(SignalBusMS.SIGNAL_PROCESS_COMPLETE, artifact)

        except Exception as e:
            error_msg = f"Inference failed: {str(e)}"
            self.logger.error(error_msg)
            self.bus.emit(SignalBusMS.SIGNAL_LOG_APPEND, f"\n[SYSTEM ERROR]: {error_msg}")

    # -------------------------------------------------------------------------
    # Task Queue
    # -------------------------------------------------------------------------

    def add_task(self, task: dict) -> None:
        """Appends a task dict to the queue. Keys: label, model, role, system_prompt, user_content."""
        self.task_queue.append(task)

    def remove_task(self, index: int) -> None:
        if 0 <= index < len(self.task_queue):
            self.task_queue.pop(index)

    def clear_queue(self) -> None:
        self.task_queue.clear()
        self._queue_running = False

    def run_queue(self) -> None:
        """Starts sequential execution of all tasks in the queue."""
        if not self.task_queue or self._queue_running:
            return
        self._queue_running = True
        self._start_task(0, "")

    def _start_task(self, index: int, inherited_context: str) -> None:
        if index >= len(self.task_queue):
            self._queue_running = False
            self.bus.emit("queue_complete", {})
            return

        task = self.task_queue[index]
        self.bus.emit("queue_progress", {
            "current": index + 1,
            "total": len(self.task_queue),
            "label": task.get("label", f"Task {index + 1}")
        })

        # Wire a one-shot handler: unsubscribes itself after firing
        def on_done(artifact, idx=index):
            self.bus.unsubscribe("process_complete", on_done)
            self._on_task_done(idx, artifact)

        self.bus.subscribe("process_complete", on_done)

        model = task.get("model") or self.get_setting("last_model") or ""
        self.process_submission(
            content=task.get("user_content", ""),
            model=model,
            role=task.get("role", ""),
            prompt=task.get("system_prompt", ""),
            inherited_context=inherited_context
        )

    def _on_task_done(self, index: int, artifact: dict) -> None:
        response = artifact.get("response", "")
        next_context = f"Previous task output:\n{response}" if response else ""
        self._start_task(index + 1, next_context)

    # -------------------------------------------------------------------------
    # Session management (thin delegation)
    # -------------------------------------------------------------------------

    def _resolve_startup_session(self, last_name: Optional[str]) -> SessionData:
        """Load last session or create 'default' if none exists."""
        if last_name:
            try:
                return self.session_manager.load_session(last_name)
            except FileNotFoundError:
                pass
        sessions = self.session_manager.list_sessions()
        if sessions:
            return sessions[0]
        return self.session_manager.new_session('default', 'Default session')

    def _load_task_queue(self) -> list:
        """Restore task queue from current session's tasks.json."""
        path = self.current_session.task_path
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _create_store(self, vector_path: str):
        """Create a FaissStore, falling back to a NullStore if FAISS is unavailable."""
        try:
            return self.vector_factory.create('faiss', {'path': vector_path, 'dim': 768})
        except Exception as e:
            self.logger.warning(f"Vector store unavailable ({e}). RAG disabled for this session.")
            return _NullStore()

    def _rebuild_store(self) -> None:
        """Point current_store at the active session's vector path."""
        self.current_store = self._create_store(self.current_session.vector_path)

    def switch_session(self, name: str) -> None:
        self.save_current_session()
        self.current_session = self.session_manager.load_session(name)
        self.task_queue = self._load_task_queue()
        self._rebuild_store()
        self.config_store.set('last_session_name', name)
        self.bus.emit("session_switched", self.current_session)

    def new_session(self, name: str, description: str = "") -> None:
        self.save_current_session()
        self.current_session = self.session_manager.new_session(name, description)
        self.task_queue = []
        self._rebuild_store()
        self.config_store.set('last_session_name', self.current_session.name)
        self.bus.emit("session_switched", self.current_session)

    def save_current_session(self) -> None:
        self.session_manager.save_session(self.current_session, self.task_queue)

    def list_sessions(self) -> List[SessionData]:
        return self.session_manager.list_sessions()

    def delete_session(self, name: str) -> None:
        self.session_manager.delete_session(name)
        if self.current_session.name == name:
            remaining = self.session_manager.list_sessions()
            if remaining:
                self.switch_session(remaining[0].name)
            else:
                self.new_session('default', 'Default session')

    def ingest_file(self, file_path: str, embed_model: str) -> Dict[str, Any]:
        stats = self.ingest_pipeline.ingest_file(file_path, self.current_store, embed_model)
        self.current_session.chunk_count += stats['chunks_added']
        if file_path not in self.current_session.ingested_files:
            self.current_session.ingested_files.append(file_path)
        self.config_store.set('embed_model', embed_model)
        self.bus.emit("session_stats_updated", self.current_session)
        return stats

    def ingest_directory(self, dir_path: str, extensions: list, embed_model: str) -> Dict[str, Any]:
        stats = self.ingest_pipeline.ingest_directory(dir_path, extensions, self.current_store, embed_model)
        self.current_session.chunk_count += stats['total_chunks_added']
        self.config_store.set('embed_model', embed_model)
        self.bus.emit("session_stats_updated", self.current_session)
        return stats

    def clear_session_vectors(self) -> None:
        self.current_store.clear()
        self.current_session.chunk_count = 0
        self.current_session.ingested_files = []
        self.bus.emit("session_stats_updated", self.current_session)

    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------

    def export_artifact(self, artifact: Dict[str, Any], destination: str, path: str = None) -> Dict[str, Any]:
        try:
            mode_map = {"File": "scaffold", "Vector": "memory", "Project Capture": "blueprint"}
            mode = mode_map.get(destination, "scaffold")
            target = path if path else ("cell_memory_bank" if destination == "Vector" else "export.txt")
            return self.factory.hydrate_artifact(artifact, mode=mode, destination=target)
        except Exception as e:
            self.bus.emit(SignalBusMS.SIGNAL_ERROR, {"message": f"Export failed: {str(e)}", "level": "ERROR"})
            return {"status": "error", "message": str(e)}

    # -------------------------------------------------------------------------
    # Feedback
    # -------------------------------------------------------------------------

    def record_feedback(self, artifact: Dict[str, Any], is_accepted: bool) -> None:
        self.validator.validate_artifact(artifact, is_accepted)

    # -------------------------------------------------------------------------
    # Cell rename
    # -------------------------------------------------------------------------

    def rename_cell(self, new_name: str) -> None:
        old_name = self.cell_name
        self.identity.rename(new_name)
        self.cell_name = self.identity.cell_name
        self.bus.emit("cell_renamed", {
            "cell_id": self.cell_id,
            "old_name": old_name,
            "new_name": self.cell_name
        })
        self.bus.emit("update_window_title", f"_theCELL [{self.cell_name}]")

    # -------------------------------------------------------------------------
    # Long-term memory helpers
    # -------------------------------------------------------------------------

    def _summarize_memory_stub(self, text: str) -> str:
        return f"Session Summary [{datetime.now().isoformat()}]: {text[:200]}..."

    def _flush_to_vector_db(self, text: str, metadata: Dict[str, Any]) -> None:
        artifact = {"payload": text, "metadata": metadata}
        self.factory.hydrate_artifact(artifact, mode="memory", destination="long_term_history")
