# Tranche Protocol

Status: **DRAFT for operator agreement.**
Date: 2026-08-06.
Authority: subordinate to `CHARTER.md` and `BUILDER-CONSTRAINT-CONTRACT.md`.

This is the repeatable procedure. It is run identically for every tranche, and
it can only end in one of two states: **parked** or **blocked**. There is no
"mostly done".

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

Adopted verbatim from the BCC:

```
read constraints
declare tranche
inspect current state
record start
implement narrowly
verify and review critically
repair required issues
re-verify
document fully
capture evidence
summarize current state
park cleanly
respect closure
```

Two amendments, and only two:

- **Step 2 (declare tranche) must include writing the gate.** The gate is
  written before implementation, not after.
- **Step 12 (park cleanly) requires a passing gate.** Nothing else counts.

---

## 3. The Gate

### 3.1 What it is

A gate is an executable check that exits `0` only when the tranche's stated
outcome is actually true. One gate per tranche, living at:

```
gates/t<NN>_<slug>.py
```

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

### 3.3 What a gate is not

Not a unit test suite. Tests prove code behaves; a gate proves the *tranche
outcome* holds. A tranche will usually have both, and the gate may invoke the
tests as one of its assertions.

---

## 4. Declaration

Before implementation, record in the journal:

- tranche number and name
- the outcome in one sentence
- explicit non-goals
- the gate: path, and what it asserts
- expected changed surfaces
- known risks

If the tranche boundary is unclear, clarify before starting. Conservative
inference is permitted; guessing is not.

---

## 5. Parking

A tranche is parked when **all** of the following are true:

- its gate passes
- the full gate suite passes
- changed files are listed in the journal
- unresolved risks are recorded
- generated debris is cleaned or staged in `_trash/`
- the next action is stated
- the journal entry is closed

If the gate does not pass, the tranche is **blocked**, not parked. A blocked
tranche records what blocks it and stops. Blocked is a legitimate, honest
outcome. Claiming completion is not.

### 5.1 Closure

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
