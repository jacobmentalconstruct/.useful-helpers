# Tranche Protocol

Status: **DRAFT for operator agreement.**
Date: 2026-08-06.
Authority: subordinate to `CHARTER.md` and `BUILDER-CONSTRAINT-CONTRACT.md`.

This is the repeatable procedure. It is run identically for every tranche, and it
can only end in one of three states: **parked**, **blocked**, or **awaiting
approval**. There is no "mostly done".

`awaiting approval` is the state a tranche sits in between the builder finishing and
the operator accepting. It was added on 2026-08-09, after four tranches had been
closed by the builder alone.

---

## 1. Why This Document Exists

The BCC already defines the workflow loop at anchor
`BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`. That loop is **adopted here unchanged.**
Writing a competing one would be the exact drift this project is eliminating.

What the BCC lacks is enforcement. Its testable-closure rule says untested
behavior is provisional, but nothing *makes* that true. Prose cannot close a
tranche — this was demonstrated on 2026-08-05, when a tranche was parked as
complete with every finding unverified, and stayed that way until a shell became
available and one check overturned it.

This document adds the missing mechanism: **the gate**.

---

## 2. The Loop

**The loop lives in the BCC**, at anchor `BCC-WORKFLOW-REQUIRED-TRANCHE-LOOP`
(§2.8) — seventeen steps in four blocks, with three terminal states: **parked**,
**blocked**, **awaiting approval**.

It is not reproduced here. An earlier revision of this document copied it verbatim,
which meant two copies that could drift — the exact failure mode this project was
started to remove. Read it there.

What belongs here is the **mechanism**: how this project satisfies steps that the
BCC states in general terms.

| BCC step | This project's mechanism |
| --- | --- |
| 5 · declare the completion condition | **Write the gate** — `gates/t<NN>_<slug>.py`, authored before implementation (§3.2 rule 1) |
| 9 · consolidate | ruff clean; dead code removed; debris to `_trash/` |
| 10 · verify and review critically | the gate suite (§3) **and** the discovery pass (§3.4), which are different activities |
| 10 · record the configuration | fresh clone, **no environment variables**, both platforms |
| 12 · submit for operator review | present outcome, checks, unexpected findings, and carried items — then stop |
| 16 · park cleanly | §5 parking criteria; **a passing gate is necessary and not sufficient** |

Two things the BCC leaves open that this project fixes:

- **The completion condition is executable.** Prose cannot close a tranche. This was
  demonstrated on 2026-08-05, when a tranche parked as complete with every finding
  unverified and stayed that way until a shell became available and one check
  overturned it.
- **A green gate is not approval.** The gate proves the builder's own claim. Step 12
  exists because the builder is not the party entitled to accept it.

---

## 3. The Gate

### 3.1 What it is

A gate is an executable check that exits `0` only when the tranche's stated
outcome is actually true. One gate per tranche, living at:

```
gates/t<NN>[<variant>]_<slug>.py
```

The optional variant letter carries a split tranche: `t05a_observe_select.py`,
`t05b_operate_verify.py`. It is part of the discovery pattern in `run.py`, not
decoration — an earlier pattern matched only `t<NN>_`, so a split tranche's gate
would have been absent from a suite that still reported PASS.

Run individually, or all of them:

```
python gates/run.py            # every gate; the suite
python gates/run.py t03        # one
```

### 3.2 Rules

1. **Written first.** The gate is authored during tranche declaration, before
   implementation. If the outcome cannot be expressed as a check, the tranche is
   not well enough defined to start.
2. **Binary.** Exit 0 or non-zero. No score, no percentage, no partial credit.
3. **No manual steps.** A gate that requires a human to look at something is not
   a gate. If a thing genuinely needs eyes, the gate asserts the *artifact* that
   the eyes would examine exists and has expected properties.
4. **Names what failed.** A failing gate prints which assertion failed and the
   observed value. "Gate failed" is not acceptable output.
5. **Runs from the project root**, offline, with no network and no local model.
6. **Cumulative.** Every prior gate must still pass. A tranche that breaks an
   earlier gate is not done, regardless of its own gate.
7. **Honest skip.** If a check cannot run on this host — Windows-only behavior,
   read-only mount on a non-Linux host — it reports `SKIPPED` with a reason and
   the suite exits non-zero unless the skip is explicitly registered as accepted.
   A skipped check must never read as a pass.

8. **Exercise a real consumer entrance appropriate to the tranche outcome.**
   A gate must exercise the thing under test through the entrance used by its real
   consumer, not only through an internal implementation seam.

   | Outcome under test | Its real consumer entrance |
   | --- | --- |
   | runtime capability | `cli`, `mcp`, the GUI, the setup application, or another actual caller |
   | governance or authority surface | the documented context-entry / read path an entering agent is instructed to follow |
   | build or distribution artifact | the actual assembler / build / package entrance |
   | any other artifact | the real consuming interface for that artifact |

   Direct function-level assertions may **supplement** this. They do not
   **substitute** for consumer-path proof where such a path exists.

   This is not style. A check that only calls functions cannot see how they are
   *composed*, and composition is where defects of assembly live. T2 parked green
   with fourteen assertions, every one of them unit-level, while a real bug sat in
   the wiring: `presence.clear()` behaved perfectly when called directly, and
   destroyed the operator's context on every CLI invocation.

   T0 asserted through `cli tool-list`; T2 did not, and that difference is the whole
   explanation. Written down here so it stops being an accident of style.

   **Generalised 2026-08-09.** The rule previously named only `cli`, `mcp` and the
   GUI. T5's outcome is a governance model, which has no runtime capability to
   invoke — and satisfying the rule by locally reinterpreting "real entrance" for
   one tranche would have produced *protocol text ≠ actual practice*, the exact
   defect T5 exists to formalise. The abstraction belongs in the rule.

   **A historical note this rule used to get wrong.** It cited T1 as asserting
   through "a real `sidecar_install`". That was the project's belief at the time.
   `sidecar_install` is a *runtime tool that installs another sidecar*; the product's
   installation entrance is the standalone setup application at
   `packaging/installer/` — see the Charter, `SIDECAR:SETUP-DISTRIBUTION`. T1's
   evidence stands as history; the claim that it exercised the product's install
   entrance does not.

9. **The gate is not the whole of verification.** A passing gate closes step 8
   (`re-verify`). It does not close step 6 (`verify and review critically`), which
   also requires the **discovery pass** in §3.4.

   The gate answers *did this do what was claimed*. Only the discovery pass can
   answer *what else is now true*, because a gate can only contain what its author
   already suspected.

### 3.3 What a gate is not

Not a unit test suite. Tests prove code behaves; a gate proves the *tranche
outcome* holds. A tranche will usually have both, and the gate may invoke the
tests as one of its assertions.

---

## 3.4 The Discovery Pass

The gate proves the tranche did what it claimed. **It cannot find anything else**,
because every assertion in it encodes what was expected — and the defects that have
actually escaped were all in the gap between expectation and truth.

So a second, different activity runs at every close. Its question is not *"did this
work"* but **"what else is true?"**

The distinguishing property of everything below is that **none of it encodes the
builder's expectations.**

1. **Run the harness.** `_harness/harness.py run <target>` and `seam`. It was
   written by someone else, scores against the charter rather than the
   implementation, takes sha256 manifests before and after — catching *any* trace
   rather than a predicted one — exercises **every** mounted tool with default
   arguments, and carries **planted false-positive bait**. That last one detects
   tools that *lie*, a category no correctness assertion can reach, because a lying
   tool returns successfully.

2. **Differential.** Compare two things that should agree; the disagreement carries
   the information. Fresh clone against working tree found a repository that could
   not pass its own suite. Generation 1 against generation 2 proved self-hosting.
   Windows against Linux found a two-error lint backlog and a decode bug.

3. **Perturbation.** Delete the store, kill the parent, wipe the state root. Three
   defects came from asking *what if the world is hostile* rather than *does this
   work*.

4. **Mutation.** Break the fix and confirm the check fails. This validates the
   **check**, not the code. An assertion never seen to fail is a hypothesis.

5. **Census.** Enumerate every instance of a pattern, not the instances just
   touched. Seven of eight call sites were unattributed, and the check written to
   catch that missed a ninth because it scanned where the problem was expected.

6. **Cross-environment.** CI on Windows and Linux. Different platform, different
   assumptions violated.

### Why this is separate from the gate

Conflating them is why four fixes had partner effects that went unseen: a memo that
outlived its file, a clear that ran per process, a process group that gained reach
and lost cascade, and a gate that inherited the blind spot of the bug it was
written to catch. Each was correct in isolation. Each was caught — when it was
caught — by measuring rather than asserting.

**A green gate means the assertions passed. It does not mean the code is correct.**

---

## 4. Declaration

Before implementation, record in the journal — this is BCC steps 2–7, and the
journal entry is opened *here*, not at the end:

- tranche number and name
- the outcome in one sentence
- **current state, as measured** — not as remembered
- explicit non-goals: what this tranche is not for
- the completion condition and stop conditions, expressed as the gate: its path
  and what it asserts
- **the ordered plan**, including the consolidation pass — this is what step 12 is
  reviewed against, and work outside it is either a recorded discovery or refused
  scope creep
- expected changed surfaces
- known risks — and a risk named here becomes a gate assertion, not scheduled work

If the tranche boundary is unclear, clarify before starting. Conservative
inference is permitted; guessing is not.

---

## 5. Parking

A tranche is parked when **all** of the following are true:

- **the operator has approved it** at BCC step 12
- its gate passes
- the full gate suite passes, from a fresh clone, with no environment variables set
- changed files are listed in the journal
- unresolved risks are recorded
- generated debris is cleaned or staged in `_trash/`
- **staleness is resolved** — no superseded plan, competing numbering, outdated
  architecture note, closed backlog item, or current-state surface still describing
  a former state
- **the synopsis of the next tranche is declared**
- the journal entry is closed
- **the shipped documentation matches what the sidecar now is**
- **the discovery pass has been run** (§3.4) and its findings recorded — including
  a finding of "nothing", which is itself worth writing down

The first is the one the builder cannot satisfy alone, and it comes first for that
reason. Everything below it is the builder's own account of its own work. T1, T2, T3
and T4 were each closed on that account and nothing else.

The documentation criterion is not a courtesy either. `docs/` and `AGENTS.md` are
**deliverables**: they travel to every target the sidecar is installed into, and
`AGENTS.md` is the first thing an arriving agent reads. Three tranches were parked
before anyone noticed the shipped architecture document still described the sidecar
as it stood before T1 — no ledger, no presence, no attribution — so a vended sidecar
was documenting a version of itself that no longer existed.

Catching up at the end is a rewrite. Updating at each close is a paragraph.

If the gate does not pass, the tranche is **blocked**, not parked. A blocked
tranche records what blocks it and stops. Blocked is a legitimate, honest
outcome. Claiming completion is not.

### 5.0 Awaiting approval

Between the builder finishing and the operator accepting, the tranche is **awaiting
approval**. In that state the builder does not document, does not park, and does not
start the next tranche. It waits.

What is submitted at BCC step 12:

- what was **declared** — outcome, non-goals, stop conditions, plan
- what was **done**, measured against that plan, with any deviation named as such
- what the **checks** show, and the configuration they ran under
- what the **discovery pass** found that nobody was looking for
- what is **carried forward** — risks, backlog, unverified claims

If the operator does not approve, the builder returns to consolidation, addresses
what was raised, and submits again. There is no limit on that cycle, and a tranche
may be declared blocked from inside it.

**Consolidation on a resubmission is not the polish prohibited by §5.1.** §5.1
concerns work already parked, which is work the operator has already accepted.

### 5.1 Supersession

Rule 6 says every prior gate must still pass. That is right while the architecture
holds. It is wrong when the operator deliberately retires a premise — and the
protocol previously had no answer, so a superseded invariant would have had to keep
passing forever, or be silently disabled.

The resolution is a distinction the project already had but never named:

| | What it is | Mutability |
| --- | --- | --- |
| **Historical evidence** | what a tranche proved *when it closed* — its journal entry, its recorded output | **Immutable.** Never rewritten |
| **Active cumulative proof** | what the *current* architecture still requires to remain true — the live gate suite | Surgically replaceable |

A parked tranche's history is closed. Its **active assertions** are not the same
object, and an operator-approved architectural correction may replace them.

**A supersession is only valid when the superseding tranche records all five.** It
**names the exact** old assertion — nothing here may be described in general terms:

1. the **old assertion**, named exactly — file, check text, and the premise it rests on
2. **why** it is no longer desired
3. the **replacement** invariant, or an explicit statement that the replacement is
   owed by a named later tranche
4. the **superseding authority** — the operator decision and the tranche carrying it
5. the historical **evidence** location, where the retired assertion is preserved

Then, and only then, the assertion is removed from the active cumulative proof set
**atomically, in the superseding tranche**. Retired assertions are preserved as
source under `gates/_superseded/`, with the `.superseded` suffix, never deleted.

A tranche in this state is recorded as **SUPERSEDED** — distinct from *withdrawn*,
which describes a tranche that was declared and never implemented, and whose
material is preserved under `gates/_deferred/` instead. Withdrawn material never
entered the active suite; **SUPERSEDED** material did, and was removed from it.

**No silent disabling. No rewriting the old journal. No old gate continuing to claim
current authority after its premise has been intentionally retired.**

And the contradiction is not deferred: a superseding tranche that leaves the active
suite asserting the retired premise has knowingly shipped two normative surfaces
claiming opposite things, which is the defect the one-authority rule exists to
prevent. **Census the whole gate, not the assertions you expect to find.**

### 5.1a A note on what a failing gate proves at declaration

A newly written check that claims to detect an **absent** condition must be
demonstrated to fail while that condition is absent. Otherwise it is a hypothesis,
and a gate full of hypotheses is decoration.

But it is **not** true that every assertion in a gate must fail at declaration. A
tranche may legitimately assert a **pre-existing invariant it must preserve**, and
such a check passes before and after. Both belong in a gate, and the declaration
should say which is which:

- **pre-existing invariant** — already passes; the tranche must not break it
- **completion claim** — currently fails; the tranche must make it pass

Do not engineer artificial red to make the initial count look better. The purpose is
proving the checks **discriminate**, not maximising failures.

### 5.2 Closure

After parking, the tranche is closed. Reopening requires a correctness,
security, containment, data-loss, or maintainability justification, stated in
the journal before work begins.

Polish after parking is prohibited. So is expanding scope mid-tranche: new work
discovered during a tranche is recorded in the backlog and becomes a candidate
tranche, not an extension of the current one.

---

## 6. Journal

One entry per tranche, numbered from `0001`, in `_docs/AppJOURNAL/`.

Records: date, tranche, what changed and why, files changed, gate result with
the actual command and output, checks performed, unresolved risks, next action.

Prior entries are never rewritten. Corrections are made in a later entry that
names what it corrects.

Historical test counts, tranche numbers, and completion claims inherited from
other projects are never reported as this project's status. The archive at
`.plans-and-parts_FOR-REFERENCE-ONLY/_ARCHIVE-PRE-RESET-2026-08-06/` holds the
predecessor material; it is evidence, not authority.

---

## 7. Evidence

Where a gate's result depends on a measurement, the measurement is preserved in
`.bcc/evidence/` with the date and what produced it. Evidence is referenced from
the journal entry by filename.

Claims in documents carry their standing: **verified** means executed with the
output recorded; anything else says so plainly.
