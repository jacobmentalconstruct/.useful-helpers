# 0017 — T5a Declared: One Surface, Observe and Select

- **Date:** 2026-08-09
- **Tranche:** T5a — One Surface: Observe and Select
- **Status:** **DECLARED. Gate written and failing.** Entry opened before
  implementation, per BCC §2.8 step 7.

First tranche run under the amended loop. Steps 1–7 below; the hard stop at step 12
is where this returns for approval.

---

## 1. Tranche (step 2)

**Outcome, one sentence.** A single shell opens a project, browses it, and inspects
what is selected — with browse selection and operation inclusion kept as separate
state domains, so clicking a file authorises nothing.

**Changed surfaces.** `src/ui/controller.py` (new), `src/ui/shell.py` (new),
`src/app.py` (one mode, one probe), `gates/t05a_observe_select.py`,
`gates/run.py`, `docs/ARCHITECTURE.md`, `AGENTS.md`.

---

## 2. Current state, as measured (step 3)

Not remembered — read out of a fresh clone this morning.

```
src/ui/app_ui.py          186 lines   composition + four headless probes
src/ui/registry_view.py   217
src/ui/mapper_view.py     466
src/ui/planner_view.py    260
src/ui/installer_view.py  197
src/lib/theme.py           71        already implemented
```

**Four windows, not one surface.** `src/app.py` dispatches `ui`, `map`, `install`,
`plan` to four separate roots. E3 fails today by construction.

**The pattern is repeated four times.** Every view carries its own
`queue.Queue` + `threading.Thread(daemon=True)` + `widget.after(_POLL_MS, ...)`:
`installer_view` 35/126/138, `mapper_view` 54/376/388, `planner_view` 42/172/184,
`registry_view` 51/173/185. Building a shell by copying it makes five.

**What is already built and can be used rather than invented:**

- `presence.FIELDS` already declares `browse_selection` and `operation_inclusion`
  as distinct entries — T2 anticipated exactly this tranche's core distinction.
- `watch.poll()` with a measured cost of 0.29 ms and `SUGGESTED_INTERVAL_MS = 150`.
- `invoke(..., client="gui")` with cancellation, per-call timeout, and reaping.
- `tools/file_tree` — Observe, `operates_on: project`, takes `root/kind/ext/limit/
  ignore`. The explorer's data source exists; it needs no new tool.
- The headless-probe idiom: `run_probe`, `run_planner_probe`, `run_installer_probe`
  build real widgets, pump `root.update()`, tear down, print one JSON line. That is
  what makes rule 8 affordable here, and the shell's probe follows it.

**Registry:** 95 tools — Observe 52, Apply 41, Sandbox 2, across 22 categories.
**Chains:** there is no `chains/` directory. Playbooks run through
`playbook.run_playbook()`. T5a does not need either; noted so T5b does not discover
it late.

---

## 3. What this tranche is not for (step 4)

- **No tool execution from the shell.** Not one Apply, not one Observe. That is T5b.
- **No event view.** The ledger and presence rendering is T5b.
- **Not retiring the four views.** They stay, working, as the regression reference.
  Retiring them is T5b, and doing it here would remove the only second
  implementation available to compare against.
- **No new tools.** `file_tree` and `attach` already exist.
- **No theming work.** `src/lib/theme.py` is done.
- **No cancellation or progress UI.** Wired in T4, surfaced in T5b.

---

## 4. Completion condition and stop conditions (step 5)

**`gates/t05a_observe_select.py`** — written first, and **failing now**, which is
the only evidence that it is a condition rather than a wish:

```
[FAIL] a single shell module exists
[FAIL] the worker pattern is extracted into a controller
[PASS] the legacy views are still present as a regression reference
[FAIL] the shell builds and tears down headlessly  (unknown mode: ui-shell-probe)
=> t05a_observe_select BLOCKED
```

Fourteen assertions: shell and controller exist; the shell spawns no thread of its
own and reaches the seam only through the controller; the four legacy views survive;
it builds and tears down headlessly; opening a project populates the explorer and
binds the target it was pointed at; context renders for a file **and** for a folder;
browsing does not change inclusion **and** inclusion does not move browsing; rescan
picks up a change; presence reports both domains accurately to an agent; shutdown
leaves nothing running.

**Two hazards encoded as assertions rather than left to be discovered**, per the
standing practice from T2:

**Hazard 1 — selection authorises.** The easy implementation hands the tool
workspace "the selected file". Then clicking in the explorer has silently nominated
an operand, and a later Apply acts on whatever the operator last looked at.
Asserted in **both directions**, because one direction passing is exactly the
partial fix that makes the other look intentional.

**Hazard 2 — the fifth copy of the pattern.** Asserted structurally on the shell's
source, because a shell that copies the pattern and a shell that uses the controller
both run correctly, and only one of them is right.

**Stop conditions.** Stop and report if: the controller cannot be extracted without
changing view behaviour (the views are the regression reference and must keep
passing); `tkinter` is unavailable such that the probe can only SKIP, which is not a
pass and would leave the tranche blocked pending an operator run on Windows; or the
explorer needs a tool that does not exist, which would mean the boundary was drawn
wrong and T5a should be re-declared rather than widened.

---

## 5. The plan (step 6)

Declared so step 12 has something to be reviewed against. Work outside it is either
a recorded discovery or refused scope creep.

1. **Extract the controller.** `src/ui/controller.py` — one worker thread, one
   queue, one `after()` pump, dispatching through `invoke(..., client="gui")`.
   Derived from the four views' common shape, not invented.
2. **Migrate one existing view onto it** — `registry_view`, the smallest — and
   confirm its probe still passes. This is the differential: if the controller is
   wrong, the view that already worked will say so before any new code depends on it.
3. **Build the shell.** `src/ui/shell.py`: explorer pane, context pane, project-open
   flow. `minsize(900, 600)`, mousewheel bound on every scrollable, non-truncating
   button rows, per the `_UsefulHelperScriptsMENU` UX intent.
4. **Wire the two state domains**, independent in both directions, published through
   `presence.update()`.
5. **Add `ui-shell-probe`** to `src/app.py`, following the existing probe idiom.
6. **Consolidate** (step 9): ruff, dead code, no duplicated pump, docstrings.
7. **Verify** (step 10): the t05a gate, the full suite from a fresh clone with no
   environment variables, and the discovery pass — harness `run` and `seam`,
   perturbation of the shell's shutdown path, and a mutation check that at least one
   new assertion has been seen to fail.
8. **Resolve staleness** (step 15): `docs/ARCHITECTURE.md` and `AGENTS.md` both
   describe four separate windows.

---

## 6. Known risks (step 2)

- **`tkinter` absent from the sandbox.** Every behavioural assertion here runs
  through a real widget build. This tranche will produce honest SKIPs in the sandbox
  and needs a Windows run to close. Flagged now, not at the gate.
- **Windows process-group kill still unverified** — already backlogged as High
  before T5b, and T5a is the last quiet moment to confirm it.
- **The controller is a refactor of working code.** The four views passing after
  migration is the check; step 2 of the plan exists for that reason alone.

---

## 7. Found while declaring, fixed immediately

`gates/run.py` globbed `t[0-9][0-9]_*.py`, which **cannot match
`t05a_observe_select.py`**. The split into T5a/T5b was made at the plan level in a
previous session, and the gate mechanism was never told.

The failure mode is the bad one: the gate would not have failed, it would have been
**absent**, while `gates/run.py` reported `SUITE: PASS`. A false green produced by a
naming convention rather than by any code.

Pattern widened to `t[0-9][0-9]*_*.py`, and protocol §3.1 now specifies
`t<NN>[<variant>]_<slug>.py` with the reason attached.

---

## 8. Next

Implementation — plan steps 1 through 5, then consolidate and verify. Returns at
BCC step 12 for operator review, and is not parked before that.
