from __future__ import annotations

import time
import unittest

from src.shell.event_bus import EventBus
from src.shell.task_manager import TaskManager


class TaskManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.event_bus = EventBus()
        self.task_manager = TaskManager(self.event_bus, max_workers=2)

    def tearDown(self) -> None:
        self.task_manager.shutdown(wait=True)

    def test_successful_task_returns_result_to_queue(self) -> None:
        self.task_manager.submit_task("double", lambda value: value * 2, 21)

        result = self._wait_for_single_result()

        self.assertEqual(result.state, "completed")
        self.assertEqual(result.result, 42)

    def test_failed_task_returns_error_result(self) -> None:
        def boom() -> None:
            raise RuntimeError("kaboom")

        self.task_manager.submit_task("boom", boom)
        result = self._wait_for_single_result()

        self.assertEqual(result.state, "failed")
        self.assertIn("kaboom", result.error_message)

    def _wait_for_single_result(self):
        deadline = time.time() + 5
        while time.time() < deadline:
            results = self.task_manager.drain_completed()
            if results:
                return results[0]
            time.sleep(0.05)
        self.fail("Timed out waiting for task result.")


if __name__ == "__main__":
    unittest.main()
