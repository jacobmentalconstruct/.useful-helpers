# Headless Agent Package

This package is isolated from the app factory and UI stack.

It aligns to the text-adventure agent manifest:
- `agent_sessions`
- `agent_memory`
- `agent_knowledge`

Core behaviors:
- append memory rows with token counts
- assemble context as pinned + recent unpinned
- search older evicted memory for reinjection
- store and search knowledge in SQLite
- summarize and pin evicted spans when needed
