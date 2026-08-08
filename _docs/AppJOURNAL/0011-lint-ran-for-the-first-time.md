# 0011 — Lint Ran For The First Time, And Found Two Defects

- **Date:** 2026-08-08
- **Tranche:** T2 (post-park repair) and a standing-gap closure
- **Status:** **Repaired. Three gates green, lint clean, suite green.**

---

## 1. What Happened

The Windows run was requested to confirm a zero-skip suite. It came back with one
failure — and it was the check that had never once run in this project's life.

```
F401  gates/t02_ledger_presence.py:18   unused `import json`
I001  tools/vendor_export/cli.py:11     import block un-sorted
```

Both mine. Both introduced in the same session. Both auto-fixable.

---

## 2. The Blind Spot, Confirmed Exactly As Recorded

Journal 0010 recorded this as corollary 3 of the lint capability gap:

> Lint has exactly one path, and it is the wrong one. `test_self_lint_clean` is
> the only enforcement of the style bar. It lives in the test suite, shells out to
> `ruff`, and **skips silently when ruff is absent** — which it is in the
> development sandbox. So the bar goes unenforced there and no gate notices.

That was written as a theoretical risk. It was already true. **Every tranche since
T0 was built and parked without ever being linted**, and nothing said so — the
skip was one line among eighty-five, and the gate reported green.

The moment the check ran, it had a two-error backlog waiting.

---

## 3. Two Repairs

**`ruff` installed in the development sandbox.** The suite no longer skips it here.
Skips fall from 9 to 8; the remainder are `tkinter` (5) and `ollama` (3), both
genuinely absent and honestly reported.

**Lint surfaced as its own gate assertion**, with an honest `SKIP` naming the
missing dependency rather than passing over it. A capability whose only path is a
test that can vanish is not enforced. A skip must be *visible*.

---

## 4. A Correction To My Own Judgement

In the T2 review I wrote:

> This review is evidence that the `lint` tool **would not have caught either
> bug** — static analysis reported zero on the same files and was right to. Lint's
> value is ergonomic and stylistic, not defect-finding.

The first half stands: lint would not have caught the presence lifecycle bug or the
per-event migration cost. Neither is visible to a linter.

The second half was wrong, and wrong in a way worth recording. I reasoned from one
sample — the two bugs I had just found — and concluded about a whole class. Lint
covers a **different** defect class that nothing else here covers, and it had
errors waiting the moment it ran. Judging a tool by whether it would have caught
the last bug is how blind spots get argued for.

---

## 5. Verification

```
ruff check .                      -> All checks passed
fresh clone -> 85 tests in 22.6s  -> OK (skipped=8)
fresh clone -> t00 · t01 · t02    -> PASS, lint asserted at gate level
Windows     -> t01 PASS · t02 PASS, vend 279 files, self-hosting 279 = 279
```

Windows also confirmed the T2 work independently: the migration, the decision
event, presence surviving a CLI call, and the structural cost check all pass on a
host that has never run any of it before.

---

## 6. Standing Gaps After This

- `lint` **tool** — still recorded, still worth building; what it adds over the
  raw command is structured findings, Observe authority, manifest-derived scope,
  and honest unavailability. Its priority is unchanged, but its *rationale* is now
  evidence rather than argument.
- `tkinter` and `ollama` absent in the sandbox — 8 honest skips. Windows covers
  the Tk paths.
- `presence.update()` read-modify-write — carried to T3 with the transport
  decision.
- `VERSION` does not move with tool changes.

**Next.** T3 — Live Channel, with the presence concurrency model settled as its
first act.
