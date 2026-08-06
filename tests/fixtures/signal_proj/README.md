# signal_proj — analyzer fixture (T-signal)

A deliberately-shaped tiny project (parse-only; never executed) that encodes the *valid*
patterns the field report said the analyzers wrongly flagged. The T-signal smoke tests assert
the analyzers now signal correctly against it:

- **Intended layering** `cli / web (adapters) → services → domain`, plus ONE deliberate illegal
  back-edge `domain → services` (also a cycle) — for `domain_boundary_audit`.
- **Framework entrypoints** (`@app.command`, `@router.get`) that have no static caller but are
  live — for `dead_code` (must NOT be high-confidence).
- **One genuinely-dead** top-level function and **one `__all__`-exported** function — for
  `dead_code` (high vs low).
- **A blocking call in an `async def`** (a real finding) and the **same class of call in a sync
  `def`** (informational, not a defect) — for `blocking_call_scan`.
