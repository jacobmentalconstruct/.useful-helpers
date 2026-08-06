# Testing

Status: conventions defined Tranche 0. **No tests exist. Nothing has been run.**

---

## 1. Current Verification Standing

There is no test suite, no smoke check, and no baseline, because there is no
runtime code.

No command has been executed in this project. The isolated Linux environment
failed to start during Tranches 0 and 1, and no Windows shell was available.

Historical test counts in inherited material are **not** verification of this
project and must never be reported as current.

---

## 2. Layout

Tests mirror the runtime package:

```
tests/
  core/          paths, scanning, selection, inspection, classification
  operations/    manifests, registry, authority, dispatcher, events, results
  integrations/  toolkit bridge, process service
  tools/         per-tool backends
  storage/       schema, sqlite, state, settings
  ui/            startup, panels, smoke
```

Runner: `pytest`, invoked from the project root. Tests must not require the GUI
except in `tests/ui/`.

---

## 3. Principles

- **Backend before UI.** No behavior may be testable only through the GUI.
- **Temporary directories.** Every filesystem test builds its own tree under
  `tmp_path`. No test touches the developer's real projects.
- **State isolation.** Tests set `USEFUL_HELPERS_STATE_ROOT` to a temporary
  location. A test run never writes to the real user-data location.
- **Toolkit isolation.** Bridge tests set `SUITE_HOME`, `SUITE_PROJECT_ROOT`,
  and `SUITE_STATE_ROOT` explicitly to temporary locations, and assert the
  toolkit honoured them.
- **No network by default.** Any test needing network is marked and skipped
  unless explicitly enabled.
- **Honest gaps.** Where behavior cannot be tested, the gap is recorded in the
  journal with its residual risk rather than left implied.

---

## 4. Required Coverage

### 4.1 Foundation

Path containment; root separation; file classification; exclusion behavior;
scan stability; inclusion state; inspection; configuration; state-root behavior.

### 4.2 Operation framework

Manifest validation; authority ceilings; dry-run/apply behavior; confirmation;
target generation mismatch; cancellation; event recording; result
normalization; client attribution; subprocess failure; timeout; malformed
output; unauthorized writes.

### 4.3 Tool integration

Temporary directories for snapshot creation, text writes, line numbering, patch
batches, Git repositories, UI-mapping fixtures, and reversible evidence stores.

### 4.4 Boundary assertions — non-negotiable

- Runtime imports do not reference `.plans-and-parts_FOR-REFERENCE-ONLY`.
- Runtime imports do not reference `_design`.
- Runtime imports do not reference `_harness`.
- Reference directories can be renamed or removed without breaking tests.
- `.bcc/` can be removed without breaking runtime.
- `_docs/` can be removed without breaking runtime.
- Project operations cannot escape the selected root.
- Generated default artifacts do not silently appear in the selected project.
- Toolkit calls cannot mutate the target when manifest authority says Observe.

These are implemented as real tests, not as review checklist items.

### 4.5 UI

Application startup; project-open flow; explorer population; browse selection;
inclusion toggling; context rendering; tool opening; operation progress;
completion and failure display; cancellation; clean shutdown.

---

## 5. Toolkit Safety Gate

Before Tranche 6, the seven checks in `CAPABILITY_MATRIX.md` §7 must be
**executed** and their real output recorded as evidence. Until then, all
toolkit behavioral claims remain provisional.

---

## 6. Acceptance Evidence

Each tranche closeout records: commands run, test results, manual checks,
generated artifacts inspected, changed files, remaining risks, cleanup
performed, and the next tranche.

Normal passing checks may be summarized. Blocking or diagnostically important
failures are recorded with enough detail to be useful later.
