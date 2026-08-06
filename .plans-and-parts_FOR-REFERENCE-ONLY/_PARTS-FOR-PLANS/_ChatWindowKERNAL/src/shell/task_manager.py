"""
Owns: background task submission, execution tracking, and queue-based completion delivery.
Does not own: UI updates, widget mutation, or lifecycle shutdown policy.
Collaborates with: the app kernel, status controller, and runtime snapshots.
"""

from __future__ import annotations

import logging
import queue
import threading
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from src.shell.constants import DEFAULT_TASK_POOL_SIZE, MAX_RECENT_TASKS
from src.utils.time_utils import utc_timestamp

TaskSuccessCallback = Callable[[Any], None]
TaskErrorCallback = Callable[["TaskResult"], None]


@dataclass
class TaskRecord:
    task_id: str
    name: str
    state: str
    submitted_at: str
    started_at: str | None = None
    completed_at: str | None = None
    result_preview: str | None = None
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    on_success: TaskSuccessCallback | None = field(default=None, repr=False)
    on_error: TaskErrorCallback | None = field(default=None, repr=False)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "state": self.state,
            "submitted_at": self.submitted_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result_preview": self.result_preview,
            "error_message": self.error_message,
            "metadata": dict(self.metadata),
        }


@dataclass
class TaskResult:
    task_id: str
    name: str
    state: str
    completed_at: str
    result: Any = None
    error_message: str | None = None
    traceback_text: str | None = None
    on_success: TaskSuccessCallback | None = field(default=None, repr=False)
    on_error: TaskErrorCallback | None = field(default=None, repr=False)


class TaskManager:
    def __init__(self, event_bus, max_workers: int = DEFAULT_TASK_POOL_SIZE) -> None:
        self._logger = logging.getLogger("shell.tasks")
        self._event_bus = event_bus
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="chatwindowkernal",
        )
        self._records: dict[str, TaskRecord] = {}
        self._result_queue: queue.Queue[TaskResult] = queue.Queue()
        self._lock = threading.Lock()
        self._accepting_tasks = True

    def submit_task(
        self,
        name: str,
        fn: Callable[..., Any],
        *args: Any,
        on_success: TaskSuccessCallback | None = None,
        on_error: TaskErrorCallback | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        if not callable(fn):
            raise TypeError("fn must be callable")

        with self._lock:
            if not self._accepting_tasks:
                raise RuntimeError("Task manager is not accepting new tasks.")

            task_id = str(uuid.uuid4())
            record = TaskRecord(
                task_id=task_id,
                name=name,
                state="queued",
                submitted_at=utc_timestamp(),
                metadata=metadata or {},
                on_success=on_success,
                on_error=on_error,
            )
            self._records[task_id] = record

        self._logger.info("Task submitted. task_id=%s name=%s", task_id, name)
        self._event_bus.publish(
            "task_submitted",
            {"task_id": task_id, "name": name, "metadata": record.metadata},
        )
        self._executor.submit(self._run_task, task_id, fn, args, kwargs)
        return task_id

    def drain_completed(self, limit: int = 100) -> list[TaskResult]:
        results: list[TaskResult] = []
        while len(results) < limit:
            try:
                results.append(self._result_queue.get_nowait())
            except queue.Empty:
                break
        return results

    def active_task_count(self) -> int:
        with self._lock:
            return sum(1 for record in self._records.values() if record.state in {"queued", "running"})

    def snapshot(self, limit: int = MAX_RECENT_TASKS) -> list[dict[str, Any]]:
        with self._lock:
            records = list(self._records.values())

        records.sort(key=lambda record: record.submitted_at)
        return [record.to_dict() for record in records[-limit:]]

    def shutdown(self, wait: bool = False) -> None:
        with self._lock:
            self._accepting_tasks = False

        self._logger.info("Task manager shutting down. wait=%s", wait)
        self._executor.shutdown(wait=wait, cancel_futures=False)

    def _run_task(
        self,
        task_id: str,
        fn: Callable[..., Any],
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        with self._lock:
            record = self._records[task_id]
            record.state = "running"
            record.started_at = utc_timestamp()

        self._logger.debug("Task running. task_id=%s name=%s", task_id, record.name)

        try:
            result = fn(*args, **kwargs)
        except Exception as exc:
            traceback_text = traceback.format_exc()
            with self._lock:
                record = self._records[task_id]
                record.state = "failed"
                record.completed_at = utc_timestamp()
                record.error_message = str(exc)

            task_result = TaskResult(
                task_id=task_id,
                name=record.name,
                state="failed",
                completed_at=record.completed_at or utc_timestamp(),
                error_message=str(exc),
                traceback_text=traceback_text,
                on_error=record.on_error,
            )
            self._result_queue.put(task_result)
            self._logger.exception("Task failed. task_id=%s name=%s", task_id, record.name)
            self._event_bus.publish(
                "task_failed",
                {
                    "task_id": task_id,
                    "name": record.name,
                    "error_message": str(exc),
                },
            )
            return

        preview = _summarize_result(result)
        with self._lock:
            record = self._records[task_id]
            record.state = "completed"
            record.completed_at = utc_timestamp()
            record.result_preview = preview

        task_result = TaskResult(
            task_id=task_id,
            name=record.name,
            state="completed",
            completed_at=record.completed_at or utc_timestamp(),
            result=result,
            on_success=record.on_success,
        )
        self._result_queue.put(task_result)
        self._logger.info("Task completed. task_id=%s name=%s", task_id, record.name)
        self._event_bus.publish(
            "task_completed",
            {"task_id": task_id, "name": record.name, "result_preview": preview},
        )


def _summarize_result(result: Any) -> str:
    preview = repr(result)
    if len(preview) > 160:
        return f"{preview[:157]}..."
    return preview
