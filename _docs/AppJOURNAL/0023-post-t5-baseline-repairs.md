# 0023 — Post-T5 Baseline: Four Repairs From The First Windows Run

- **Date:** 2026-08-10
- **Reopens:** T4 (Cancellation and Progress) and T1 (One Ship Manifest)
- **Authority:** operator disposition, 2026-08-10
- **Status:** in progress

The workflow's first real execution on Windows. Four reds, three of them never
before observable.

---

## 1. Justifications, stated before work begins

`TRANCHE_PROTOCOL.md` §5.2.

**T4 — correctness.** Cancellation loses descendants on Windows. A tool process
survived the seam that started it, confirmed by PID. In use that is a worker holding
a file lock or a server holding a port after the sidecar is gone.

**T1 — correctness.** The active ship-manifest gate is **BLOCKED**: generated output
under `_projectmapper/` is tracked, ships in the payload, and carries build-machine
absolute paths and predecessor content. T1 owns the ship boundary, so this is a T1
regression. It is **not** deferred into T6: T6 establishes instance identity and
installation semantics, and must not become a grab-bag for payload defects merely
because installation eventually consumes a payload.

Two further repairs need no reopening — a missed caller in the test harness, and a
test precondition.

---

## 2. A — the diagnosis I gave was wrong, twice

I reported: *"`taskkill /F /T` does not reap the grandchild."*

**The run does not establish that.** The operator was right to reject it, and the
real picture is worse: there are **two independent defects**, and the gate exercised
neither of the ones I named.

### 2.1 What the gate actually exercised

The gate calls `proc.terminate()` on the **seam process**. On Windows that is
`TerminateProcess`, which delivers no signal and runs no `atexit`. So:

```python
src/core/invoke.py:164
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, _handler)      # Windows will never call this
```

`install_shutdown_handlers()` registers a handler Windows cannot invoke, and
`reap_all()` never runs. `_terminate()` is not involved at all — the whole seam
process is gone before any of its code could execute.

**Established: shutdown-triggered reaping does not happen on Windows.**

### 2.2 What reading establishes separately

```python
src/core/invoke.py:71  _terminate()
    if os.name == "nt":
        proc.send_signal(signal.CTRL_BREAK_EVENT)
    ...
    try:
        proc.wait(timeout=5)
        return                    # <-- taskkill /T is never reached
    except subprocess.TimeoutExpired:
        pass
    ...
        subprocess.run(["taskkill", "/F", "/T", "/PID", ...])
```

If the direct child exits within the 5-second wait — which a Python process
receiving `CTRL_BREAK_EVENT` will, via `KeyboardInterrupt` — `_terminate()` returns
and the tree escalation **never runs**. Descendants survive.

**Politeness defeats the escalation.** The better-behaved the direct child, the more
reliably its grandchildren are orphaned. This is on the explicit-cancel path, which
the failing gate did not exercise, so it is asserted from reading and is instrumented
below rather than claimed.

### 2.3 The corrected claim

> **Windows process-tree ownership is not durable. Cancellation and shutdown can
> both lose descendants, because the tree is reconstructed at kill time instead of
> being held.**

Two symptoms, one cause. `CTRL_BREAK_EVENT` reaches only processes sharing a console
group; `taskkill /T` walks a parent-child tree that has already been broken; neither
survives the parent being terminated abruptly.

A **Job Object** holds ownership instead of rediscovering it. `KILL_ON_JOB_CLOSE`
means descendants die when the job handle closes — including when the owner is
`TerminateProcess`-ed, which no signal handler can intercept.

Built as an explicit process-tree/lifetime abstraction, not raw `ctypes` scattered
through `_terminate()`.

**One job per operation**, matching the existing `_RUNNING` map: a single job for the
whole seam would make cancelling one operation kill every other in-flight one.

**An honest asymmetry:** with job objects Windows becomes *stronger* than POSIX here.
Nothing can catch `SIGKILL`, so a POSIX seam killed with `-9` still orphans its
group. That limit is irreducible and is recorded rather than hidden.

---

## 3. B — the fourth missed caller

`tests/test_smoke.py:2096` still calls `tempfile.mkdtemp()`, which `setUpClass`
redirects into the tree — the defect repaired at three other sites in 0014.

**It survived four gate runs because it skips in the sandbox for want of `tkinter`.**
Its first execution was today.

Moved to `_foreign_target()`. The probe is also marked **legacy/transitional**:
making its test valid must not imply the runtime installer has regained product
authority. T5 settled that; T6 rehomes the surface.

---

## 4. C + D — one root cause, two failures

```
_projectmapper/.useful-helpers-workbench_project_filedump.md            }
_projectmapper/.useful-helpers-workbench_project_tree.md                } tracked
_projectmapper/.useful-helpers-workbench_project_tree_and_filedump.md   } 8.4 MB
```

Generated by `projectmapper`, absent from `REGENERABLE`, absent from
`PAYLOAD_EXCLUDE`. Three observed consequences:

- payload is **288 files**, not 275 — a distribution leak
- the payload carries **build-machine absolute paths**
- the payload carries `mindshard` — the known-partial sentinel **fired**, on
  filedumped parts-bin content. A tripwire calibrated to the wrong project caught a
  real leak by accident, which is an argument for keeping tripwires, not for
  trusting them

**D is a consequence.** The dangling-link checker parses Markdown *copied inside*
those filedumps as though the filedumps were authoritative docs. All 20 dangling
links come from the two files. Fixing C removes D.

**Not repaired by adding a name to an exclusion set.** Ownership is fixed properly:
classify `REGENERABLE`, exclude from payload, ignore future regeneration, untrack
the generated copies.

---

## 5. E — a test precondition, not a delegate defect

Confirmed as the operator predicted:

```python
tools/summarize_shared.py:21   DEFAULT_MODEL = "qwen2.5:3b"
tools/delegate/cli.py:37       DEFAULT_MODEL = "qwen2.5:7b"
```

The test guards on `summarize_shared.available()` — which establishes only that
**3b** is usable — and then invokes `delegate`, which requests **7b**. With 3b
present and 7b absent, `ran: False` is the correct outcome of a wrong precondition.

The `ResourceWarning` about an unclosed socket to `127.0.0.1:11434` is a separate
cleanup issue and is **not** evidence for `ran=False`. Using it as the explanation
would have been the same mistake as §2 — a plausible story accepted without a
measurement.

The guard now probes the model the invocation will actually use, and the failure
captures the full delegate output rather than asserting on one key.

---

## 6. What the repair exposed in the gate itself

Building the fix made two things visible that the old gate could not have shown.

### 6.1 There was no grandchild

`t04`'s fixture slept in **one process**. So *"cancelling reaps the child, leaving no
orphan"* asserted only that the direct child died — **one level, not a tree** — while
the defect it is named for is a *descendant* surviving.

It was untestable by construction: on POSIX a single `killpg` covers depth one
trivially. The fixture now spawns a real grandchild and records both PIDs, and both
paths assert both levels. That is the shape a real tool leaves behind — a dev server,
a watcher, a worker holding a lock.

### 6.2 The POSIX suite cannot discriminate the defect being fixed

Mutation-tested, and it **failed to fail**:

```
MUTATION: restore the old early return (skip tree escalation)
  [PASS] seam shutdown reaps the GRANDCHILD too
  [PASS] explicit cancel reaps the GRANDCHILD too
  => t04_cancellation PASS
```

`terminate()` signals the whole process group first, so on POSIX the grandchild dies
from that signal whether or not the escalation runs. The defect is **Windows-only**,
because `CTRL_BREAK_EVENT` reaches only console-attached processes.

Declared in `t04.KNOWN_LIMITATIONS` and printed by the runner, using the mechanism
built two entries ago:

```
  [PARTIAL] explicit cancel reaps the GRANDCHILD too
            coverage: platform-partial
            disposition: only a Windows run can prove this assertion;
                         treat a Linux green as silence, not evidence
  [PARTIAL] seam shutdown reaps the GRANDCHILD too
            coverage: platform-partial
            limitation: the Job Object path HAS NEVER EXECUTED
```

**The Windows fix is unproven.** `src/core/proctree.py` is written against documented
Win32 behaviour and reasoned from the failure CI reported — not from a passing run.
Saying so is the whole point of the limitation mechanism.

### 6.3 The sentinel caught my own comment

After classifying `_projectmapper` I wrote a comment in `payload.py` containing the
literal token `parts-bin`, and `t01` failed:

```
[FAIL] no build-machine path or known predecessor sentinel ships
       ['src/core/payload.py (parts-bin)']
```

A correct fire. The manifest must name what it excludes — that is self-knowledge
under `SIDECAR:INSTANCE-OWNERSHIP` — but my *prose* introduced lineage vocabulary
into a shipped file for no functional reason. Reworded. The tripwire earned its keep
twice in one day, having also caught the `_projectmapper` leak.

---

## 7. Result

Fresh clone, **no environment variables**, Linux:

```
ruff check .           ->  All checks passed
python -m unittest     ->  Ran 85 tests, OK (skipped=8)
python gates/run.py    ->  t00 t01 t02 t03 t04 t05  SUITE: PASS
                           138 assertions, + 4 declared PARTIAL
payload                ->  280 files (was 288; 8 filedump/tree artifacts gone)
```

`src/core/proctree.py` — new. `_terminate()` reduced to a delegation; the
unconditional escalation and the ownership both live in one place.

---

## 8. Windows is still the authority

Four things in this entry can only be settled on Windows, and none of them may be
claimed here:

1. the Job Object is created and assigned (`ProcessTree.durable`)
2. seam shutdown reaps the tree when the seam is `TerminateProcess`-ed
3. explicit cancel reaps the tree when the direct child exits promptly
4. `test_c7_delegate` passes or skips honestly against `qwen2.5:7b`

---

## 9. Second Windows run — what it settled, and what it corrected

### 9.1 Settled

```
[PASS] explicit cancel reaps the child, leaving no orphan
[PASS] explicit cancel reaps the GRANDCHILD too      <- the escalation fix, on Windows
[PASS] an in-flight operation is cancellable through the seam
[PASS] seam shutdown reaps the child, leaving no orphan
[PASS] no build-machine path or known predecessor sentinel ships   (was FAIL)
[PASS] test_docs_have_no_dangling_links                             (was FAIL)
[PASS] test_installer_probe_builds                                  (was FAIL)
```

The unconditional escalation is confirmed **on the platform where the defect
existed**. Payload 288 → 286.

### 9.2 The remaining orphan, and why per-operation jobs could never fix it

```
[FAIL] seam shutdown reaps the GRANDCHILD too — pid 26976 survived
```

The direct child now dies; its grandchild does not. **Job membership is not
retroactive**, and the seam's sequence is:

```
proc = Popen(tool)                  <- the tool is running from here
ProcessTree(proc)                   <- assigned to the job only now
```

Between those two statements the tool can already have spawned children, and those
are never in the job. The fixture spawns its grandchild as its **first statement**,
so it lost that race every time.

No amount of care in `ProcessTree` closes this. The window is inherent to assigning
*after* creating, and the alternative — `CREATE_SUSPENDED` plus `ResumeThread` —
means reaching past `subprocess.Popen` into the thread handle it does not expose.

**`contain_self()`** inverts it: the seam puts **itself** in a kill-on-close job at
startup, before any tool exists. Windows places every descendant in the job
automatically, at any depth, with no window. When the seam dies by any means —
including `TerminateProcess`, which runs no handler and no `atexit` — the job closes
and the tree goes.

`ProcessTree` stays for **cancel**, where per-operation granularity is the point:
cancelling one operation must not kill every other one in flight. Two mechanisms,
two purposes, and the first Windows run is what showed they are not the same
problem.

### 9.3 §5 was wrong, and the better message is what showed it

The failure now reads:

```
error='ollama package not installed (pip install ollama); cannot delegate'
```

Not a model mismatch. **`delegate` runs under `${ROOT_VENV_PYTHON}`** — a different
interpreter from the one running the tests. The test process can `import ollama`;
the venv cannot. My §5 fix probed the right model in the wrong interpreter.

Three versions of one guard, each plausible:

| | Guarded on | Wrong because |
| --- | --- | --- |
| v1 | `summarize_shared.available()` | the summarizer's model (3b), not delegate's (7b) |
| v2 | the right model, in-process | delegate runs under another interpreter |
| v3 | **the tool's own answer** | — |

**No in-process probe can establish what a tool running under another interpreter
will find.** So the tool is asked, and its documented unavailability contract
decides: `configure` present and `ran` false means skip — and the *shape* of that
reply is asserted, so a delegate that always reported unavailable would still have
to say so in the documented form, and would still surface as a skip rather than a
pass.

### 9.4 Result

```
fresh clone, zero env vars, Linux:
  ruff clean · 85 tests OK · six gates · SUITE: PASS · 138 assertions + 4 PARTIAL
```

`t00`'s two reds were the uncommitted working tree, not defects.

---

## 10. Third Windows run — the baseline

```
python smoke_test.py   ->  Ran 85 tests, OK (skipped=1)
                           skipped: 'delegate cannot run here: ollama package not installed'

python gates/run.py    ->  t00 t01 t02 t03 t04 t05
  [PASS] seam shutdown reaps the child, leaving no orphan
  [PASS] seam shutdown reaps the GRANDCHILD too          <- contain_self(), on Windows
  [PASS] an in-flight operation is cancellable through the seam
  [PASS] explicit cancel reaps the child, leaving no orphan
  [PASS] explicit cancel reaps the GRANDCHILD too
```

**Every red is closed.** The only remaining `t00` failure was the operator's
uncommitted working tree, not a defect.

The five-tranche question is answered on the platform where it mattered: **the seam
no longer leaves anything running, by either path.**

### 10.1 Two corrections the green run demanded

A limitation that errs cautiously is still a false statement once it is out of date,
so both were fixed the same day:

- `t04.KNOWN_LIMITATIONS` claimed the Windows mechanism **"HAS NEVER EXECUTED."**
  It has now, and it passed. Rewritten to state what is actually true and permanent:
  *one assertion name covers two different mechanisms — POSIX process groups and a
  Windows kill-on-close job — so a green on either platform says nothing about the
  other.* That limitation does not expire.
- `proctree`'s module docstring said **"ONE JOB PER OPERATION."** True of
  `ProcessTree`, and it is precisely why that design could not close the shutdown
  hole. Rewritten as *two mechanisms, two purposes*.

### 10.2 A residual gap, made audible

`contain_self()` degrades honestly and therefore **silently**. On a host that
refuses the job, the guarantee is simply weaker with no signal — which is exactly
how "we fixed that" outlives the point at which it was true.

The seam now logs it:

```
invoke: process containment unavailable - tools may outlive this process
        if it is terminated abruptly
```

Recorded in the limitation as a known gap: the seam says so; nothing asserts it.

### 10.3 Final

```
fresh clone, zero env vars, Linux  ->  ruff clean · 85 OK · SUITE: PASS
Windows                            ->  85 OK (1 honest skip) · six gates PASS
```

**T4 and T1 re-park.** Both reopenings are discharged, and the post-T5 baseline is
trustworthy on both platforms — which is what T6 was waiting for.

---

## 11. Fourth and fifth Windows runs — the mechanism was never active

### 11.1 A false green found by a log, one run after adding it

Run 4 was fully green — and carried this, in a line nobody was reading:

```
[PASS] toolkit runs and registers its tools
       stderr=invoke: process containment unavailable - tools may outlive this process
```

**`contain_self()` was returning False.** The job object had never worked on Windows
at any point. So the two runs I reported as *"verified on Windows"* were a mechanism
being credited with a result it had no part in — I read a passing kill as evidence
that the thing meant to cause it had worked.

**Root cause: ctypes defaults `restype` to `c_int`.** A Win32 `HANDLE` on 64-bit
Windows is 64 bits, so `CreateJobObjectW` silently **truncated** the handle it
returned; every later call got a corrupted handle and failed; and this module's
honest degradation turned that into a quiet `False`.

The warning that exposed it had been added **one run earlier**, for exactly this
reason: *"a silently weaker guarantee is how 'we fixed that' survives past the point
where it is true."*

### 11.2 Repaired

- **`_kernel32()`** declares `restype`/`argtypes` once for every job call, so no
  site can forget. A binary contract written twice is the one-authority defect in a
  form that corrupts memory rather than merely disagreeing.
- **`containment_error()`** reports *why*, via `GetLastError()`, and the seam logs it.
- **The gate asserts containment is in force** rather than inferring it from a
  passing kill. A silent failure is now a red.
- **A silent-skip hole in the gate itself:** the grandchild branch had no `else`. If
  the fixture had not yet written `gpid`, the assertion simply did not run, and the
  suite printed a clean verdict one assertion short. An absent check now fails
  explicitly. **Third time in this entry that the failure mode was absence rather
  than wrongness.**

### 11.3 Causation, not correlation

Stability was not enough. Three consecutive Windows runs passed — but the assertion
had also passed in run 4 with the mechanism dead, so repeated greens proved the tree
gets reaped, not that this is what reaps it.

`SUITE_DISABLE_CONTAINMENT=1` was added as a permanent kill-switch, following the
project's own `SUITE_LLM_DISABLE` / `SUITE_SUMMARY_DISABLE` idiom, so the experiment
is repeatable by anyone rather than a patch nobody can rerun.

```
SUITE_DISABLE_CONTAINMENT=1  ->  [FAIL] process containment is in force on Windows
                                 [FAIL] seam shutdown reaps the GRANDCHILD too
                                        pid 7532 survived
default                      ->  both PASS
```

**Containment is what reaps the tree.** Necessary, not merely present.

And the same run left **`explicit cancel reaps the GRANDCHILD too` GREEN** — the
switch disables only the seam-wide job, leaving the per-operation `ProcessTree`
untouched. That confirms the *"two mechanisms, two purposes"* claim, which until this
run was a design assertion with no evidence behind it.

### 11.4 Final

```
Windows  ->  85 tests OK (1 honest skip) · six gates PASS · working tree clean
Linux    ->  85 tests OK · six gates PASS · ruff clean
             138 assertions + 4 declared PARTIAL
```

**T4 and T1 re-park.** The post-T5 baseline is trustworthy on both platforms.

---

## 12. Standing note

**A check's coverage is part of its claim** — and platform reach, sentinel
completeness, and *tree depth* are all coverage.

`t04` reported PASS for a full tranche while testing one process deep, on a platform
where the defect could not occur, using a mechanism that could not fail. Three
independent ways of proving less than the name promised, in one assertion, all
invisible in a column of green.

