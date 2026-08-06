from __future__ import annotations

import unittest

from src.shell.event_bus import EventBus


class EventBusTests(unittest.TestCase):
    def test_publish_delivers_to_specific_and_wildcard_subscribers(self) -> None:
        bus = EventBus()
        seen: list[str] = []

        bus.subscribe("alpha", lambda event: seen.append(f"specific:{event.event_type}"))
        bus.subscribe("*", lambda event: seen.append(f"wildcard:{event.event_type}"))

        event = bus.publish("alpha", {"value": 3})

        self.assertEqual(event.payload["value"], 3)
        self.assertEqual(
            seen,
            ["specific:alpha", "wildcard:alpha"],
        )

    def test_recent_events_returns_latest_subset(self) -> None:
        bus = EventBus()
        for index in range(5):
            bus.publish("tick", {"index": index})

        recent = bus.recent_events(limit=2)

        self.assertEqual(len(recent), 2)
        self.assertEqual(recent[0]["payload"]["index"], 3)
        self.assertEqual(recent[1]["payload"]["index"], 4)


if __name__ == "__main__":
    unittest.main()
