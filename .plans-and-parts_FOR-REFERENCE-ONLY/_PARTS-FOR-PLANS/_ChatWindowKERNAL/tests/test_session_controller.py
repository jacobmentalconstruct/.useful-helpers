from __future__ import annotations

import unittest

from src.runtime.activity_stream import ActivityStream
from src.runtime.agent_host.session_controller import HostSessionController
from src.runtime.data_hooks import DataHookCatalog


class _ImmediateTaskManager:
    def submit_task(self, _name, _fn, *_args, on_success=None, on_error=None, **_kwargs):
        if on_success is not None:
            on_success(
                {
                    "hardware": {
                        "cpu_label": "CPU 8 threads",
                        "ram_summary": "RAM 4.0/8.0 GB",
                        "gpu_label": "GPU unavailable",
                        "vram_summary": "VRAM unavailable",
                        "updated_at": "2026-03-15T12:00:03Z",
                    },
                    "available_models": ["echo/test", "qwen2.5:3b"],
                    "model_status": "Echo/test ready",
                }
            )
        return "task-1"


class _FakeAdapter:
    def __init__(self) -> None:
        self._model = "echo/test"
        self._loop = "plan_act_observe"
        self._session = {
            "session_id": "sess-a",
            "name": "Alpha",
            "created_at": "2026-03-15T12:00:00Z",
            "updated_at": "2026-03-15T12:00:01Z",
            "message_count": 2,
        }
        self._sessions = [dict(self._session)]

    def current_session_info(self):
        return dict(self._session)

    def list_sessions(self):
        return [dict(item) for item in self._sessions]

    def runtime_status(self, *, refresh_models: bool = False):
        return {
            "model_name": self._model,
            "model_status": "Echo/test ready" if self._model == "echo/test" else "Configured",
            "loop_name": self._loop,
            "session_id": self._session["session_id"],
            "use_echo": self._model == "echo/test",
            "available_models": self.list_models(refresh=refresh_models),
        }

    def list_models(self, *, refresh: bool = False):
        return ["echo/test", "qwen2.5:3b"]

    def list_loops(self):
        return ["plan_act_observe", "react"]

    def switch_model(self, model_name: str):
        self._model = model_name

    def switch_loop(self, loop_name: str):
        self._loop = loop_name

    def save_current_session(self, name: str = ""):
        if name:
            self._session["name"] = name
        return dict(self._session)

    def new_session(self, name: str = ""):
        self._session = {
            "session_id": "sess-b",
            "name": name,
            "created_at": "2026-03-15T12:05:00Z",
            "updated_at": "2026-03-15T12:05:00Z",
            "message_count": 0,
        }
        self._sessions.insert(0, dict(self._session))
        return dict(self._session)

    def load_session(self, session_id: str):
        match = next(item for item in self._sessions if item["session_id"] == session_id)
        self._session = dict(match)
        return dict(self._session)

    def rename_session(self, session_id: str, new_name: str):
        for item in self._sessions:
            if item["session_id"] == session_id:
                item["name"] = new_name
                if session_id == self._session["session_id"]:
                    self._session["name"] = new_name
                return dict(item)
        return dict(self._session)

    def delete_session(self, session_id: str):
        self._sessions = [item for item in self._sessions if item["session_id"] != session_id]
        return 1

    def reset_session(self):
        return self.new_session("")


class SessionControllerTests(unittest.TestCase):
    def test_snapshot_reflects_model_loop_and_session_changes(self) -> None:
        controller = HostSessionController(
            _FakeAdapter(),
            _ImmediateTaskManager(),
            ActivityStream(),
            DataHookCatalog(),
        )

        initial = controller.get_snapshot()
        controller.set_model("qwen2.5:3b")
        controller.set_loop("react")
        created = controller.create_session("Beta")
        renamed = controller.rename_session(created.session_id, "Gamma")
        refreshed = controller.refresh_snapshot()

        self.assertEqual(initial.current_model, "echo/test")
        self.assertEqual(refreshed.current_model, "qwen2.5:3b")
        self.assertEqual(refreshed.current_loop, "react")
        self.assertEqual(renamed.name, "Gamma")
        self.assertEqual(refreshed.active_session.name, "Gamma")
        self.assertIn("session.snapshot", {hook["hook_id"] for hook in controller._data_hook_catalog.snapshot()})
