from __future__ import annotations

import unittest

from src.runtime.activity_stream import ActivityStream


class ActivityStreamTests(unittest.TestCase):
    def test_append_event_notifies_subscribers_and_supports_filters(self) -> None:
        stream = ActivityStream(max_history=10)
        received: list[tuple[str, str]] = []
        stream.subscribe(lambda event: received.append((event.family, event.summary)))

        agent_event = stream.append_event(
            "agent.turn",
            "agent_host",
            "Turn submitted.",
            payload={"turn_id": "turn-1"},
        )
        stream.append_event(
            "tool.completed",
            "tool_service",
            "Tool finished.",
            level="warning",
        )

        filtered = stream.recent_events(
            families=["agent"],
            levels=["info"],
            sources=["agent_host"],
        )

        self.assertEqual(received[0], ("agent.turn", "Turn submitted."))
        self.assertEqual(len(received), 2)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["event_id"], agent_event.event_id)
        self.assertEqual(filtered[0]["family"], "agent.turn")

    def test_history_limit_discards_oldest_events(self) -> None:
        stream = ActivityStream(max_history=2)
        stream.append_event("ui.interaction", "chat_panel", "first")
        stream.append_event("ui.interaction", "chat_panel", "second")
        stream.append_event("ui.interaction", "chat_panel", "third")

        events = stream.recent_events()

        self.assertEqual([event["summary"] for event in events], ["second", "third"])


if __name__ == "__main__":
    unittest.main()
