"""
Owns: uncaught exception capture, crash report writing, and best-effort shutdown requests.
Does not own: normal task failures, lifecycle sequencing, or status bar widgets.
Collaborates with: the app kernel, runtime snapshot builder, and status controller.
"""

from __future__ import annotations

import json
import logging
import sys
import threading
import traceback
from pathlib import Path
from types import TracebackType
from typing import Callable
import tkinter.messagebox as messagebox

from src.runtime.activity_stream import ActivityStream
from src.shell.constants import ACTIVITY_SYSTEM_ERROR
from src.shell.constants import STATUS_ERROR
from src.utils.file_io import ensure_directory
from src.utils.time_utils import compact_timestamp, utc_timestamp

SnapshotWriter = Callable[[str], Path]
ShutdownRequester = Callable[[str], None]


class CrashHandler:
    def __init__(
        self,
        paths,
        event_bus,
        status_controller,
        *,
        activity_stream: ActivityStream | None = None,
        snapshot_writer: SnapshotWriter,
        request_shutdown: ShutdownRequester,
    ) -> None:
        self._paths = paths
        self._event_bus = event_bus
        self._status_controller = status_controller
        self._activity_stream = activity_stream
        self._snapshot_writer = snapshot_writer
        self._request_shutdown = request_shutdown
        self._logger = logging.getLogger("shell.crash")
        self._handling_lock = threading.Lock()
        self._root = None

    def install(self, root) -> None:
        self._root = root
        sys.excepthook = self.handle_exception
        threading.excepthook = self._handle_thread_exception
        root.report_callback_exception = self._handle_tk_exception
        self._logger.debug("Crash handler installed.")

    def handle_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        self._process_exception(
            origin="sys.excepthook",
            exc_type=exc_type,
            exc_value=exc_value,
            exc_traceback=exc_traceback,
            fatal=True,
        )

    def _handle_tk_exception(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ) -> None:
        self._process_exception(
            origin="tk_callback",
            exc_type=exc_type,
            exc_value=exc_value,
            exc_traceback=exc_traceback,
            fatal=True,
        )

    def _handle_thread_exception(self, args) -> None:
        self._process_exception(
            origin=f"thread:{args.thread.name}",
            exc_type=args.exc_type,
            exc_value=args.exc_value,
            exc_traceback=args.exc_traceback,
            fatal=True,
        )

    def _process_exception(
        self,
        *,
        origin: str,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
        fatal: bool,
    ) -> None:
        if exc_type is KeyboardInterrupt:
            return

        if not self._handling_lock.acquire(blocking=False):
            self._logger.error("Crash handler re-entry prevented. origin=%s", origin)
            return

        try:
            traceback_text = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
            self._logger.error(
                "Unhandled exception captured. origin=%s error=%s",
                origin,
                exc_value,
            )
            self._logger.debug(traceback_text)
            self._status_controller.set_status(
                "Application error captured. See crash report.",
                level=STATUS_ERROR,
                detail=str(exc_value),
            )
            self._event_bus.publish(
                "exception_raised",
                {"origin": origin, "error_message": str(exc_value)},
            )
            if self._activity_stream is not None:
                self._activity_stream.append_event(
                    ACTIVITY_SYSTEM_ERROR,
                    "crash_handler",
                    "Unhandled exception captured.",
                    detail=str(exc_value),
                    level="error",
                    payload={"origin": origin},
                )

            snapshot_path = None
            try:
                snapshot_path = self._snapshot_writer("crash")
            except Exception:
                self._logger.exception("Failed to write crash snapshot.")

            report_path = write_crash_report(
                self._paths.crash_reports_dir,
                origin=origin,
                error_message=str(exc_value),
                traceback_text=traceback_text,
                snapshot_path=snapshot_path,
            )
            self._logger.error("Crash report written. path=%s", report_path)

            if fatal and threading.current_thread() is threading.main_thread():
                self._show_dialog(str(report_path))

            if fatal:
                self._request_shutdown("fatal_exception")
        finally:
            self._handling_lock.release()

    def _show_dialog(self, report_path: str) -> None:
        if self._root is None:
            return
        try:
            messagebox.showerror(
                "ChatWindowKERNAL Error",
                f"An unhandled error was captured.\nCrash report: {report_path}",
            )
        except Exception:
            self._logger.exception("Failed to show crash dialog.")


def write_crash_report(
    crash_reports_dir: Path,
    *,
    origin: str,
    error_message: str,
    traceback_text: str,
    snapshot_path: Path | None = None,
) -> Path:
    ensure_directory(crash_reports_dir)
    report_path = crash_reports_dir / f"crash_{compact_timestamp()}.json"
    payload = {
        "captured_at": utc_timestamp(),
        "origin": origin,
        "error_message": error_message,
        "traceback": traceback_text,
        "snapshot_path": str(snapshot_path) if snapshot_path else None,
    }
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return report_path
