# 0038 — T8 Implemented, Gate Green, **Not Parked**

- **Date:** 2026-08-19
- **Tranche:** T8 — Governed Work Loop Prototype
- **Status:** **IMPLEMENTED. Gate 52/52. AWAITING-APPROVAL is not yet reachable** — one
  declared stop condition is unmet, for a reason that predates this tranche.
- **Preceded by:** 0037 (T8 declared, red 19/35 → strengthened to 30/48).

---

## 1. What T8 set out to prove, and what it now proves

> A human or agent moves from **awareness → impact → preview → diff → approval → Apply
> → measured change → verification → refreshed awareness**, composed entirely from
> existing tools and the existing seam.

`t08_governed_loop`: **52 assertions, all passing.** Certification on Windows at
`c728e99`: **262/262 gate assertions across nine gates, zero skips**, 87 unit tests,
lint clean, 418 seconds.

No new diff, approval, verification or runner subsystem was created, and the gate
asserts none was registered. No new application. `apps/` untouched.

---

## 2. The three preconditions, and one correction to 0037

| | Defect | Close |
| --- | --- | --- |
| 1 | `patch` declared no write domain at all | `writes: target` |
| 2 | Unreadable governance granted **Apply** | `DEGRADED_CEILING = "Observe"` |
| 3 | Uninterpretable output reported as success | three named seam failures |

**0037 overstated precondition 1 and the overstatement is corrected rather than left to
stand.** It said the missing `writes` field meant "the precept guard skips it". True, but
not for that reason: `_guard_applies` is gated on Observe authority and skips *every*
Apply tool by design. The real consequence is narrower and still worth the repair — the
declaration was untrue, and the declaration is the **input to measurement**. An
undeclared target writer is invisible to the mechanism built in §4.

**`patch` was not special.** A census found **26 Apply tools with no `writes` field**
against 8 declaring `target`; several plainly write into the target (`git`,
`test_scaffold`, `bd_index`, the `pdf_*` family). Only `patch` was corrected, because
only `patch` is on T8's Apply path. The rest are recorded as a bounded manifest-truth
item and did not enter this tranche.

### Absent is not broken, in three places now

The same distinction settled three separate decisions, and naming it once is cheaper
than re-deriving it each time:

- **governance** — no config, or a config declaring no ceiling, stays permissive. Only
  *present and unreadable* degrades, because only that is a broken control.
- **the source witness** — a caller that sent no witness did not ask for the check; a
  caller whose witness does not match asked and got an answer.
- **measurement** — `changed_paths: []` means "measured, nothing changed"; `null` means
  "not measured". A target too large to walk has no standing to issue a clean bill of
  health.

Degrading to **Observe** rather than Sandbox, because a control in an unknown state must
be safe under *every* value the operator might have intended, and Observe is the only
such value. Choosing Sandbox would assume the operator did not mean Observe — precisely
the assumption there is no evidence for.

---

## 3. The witness: approval bound to what was reviewed

A preview reports the sha256 of the bytes it read and offers it back in `apply_with`.
An Apply carrying that hash rereads the file and refuses if it no longer matches. One
tool, one field. No approval framework, transaction manager, reviewer abstraction or
general mutation protocol.

Both directions are proven, not only the interesting one:

```text
A -> interference -> Apply(witness A)     refuses, file untouched, no unwitnessed retry offered
A -> no change    -> Apply(witness A)     lands, byte-identical to the preview
```

The interference **preserves the pattern's match count**, so `expected_replacements`
cannot stand in for the witness.

### The hash is over raw bytes, and that had to be tested to be true

`read_text` maps CRLF to LF, so a whole-file line-ending rewrite leaves the decoded text
identical while changing every line on disk. A witness over decoded text would hash the
same before and after and apply an approved diff to bytes nobody reviewed.

I wrote the assertion for this case and then implemented the witness the weak way to
check it: **with the hash taken over decoded text, "binds Apply" and "refuses when the
source changed" both still pass.** Only the CRLF assertion catches it. Without that case
I would have shipped a witness that was byte-exact in the docstring and text-exact in
fact.

`TextIOWrapper` rather than `raw.decode()`, because it applies the same universal-newline
translation `read_text` does — decoding directly would leave `\r\n` in the content and
silently change which patterns match on Windows-authored files. A behaviour change
smuggled in under a safety fix is still a behaviour change.

**One read, not two.** Hashing in a separate `read_bytes()` would leave a window in which
the witness describes a file the edit never saw — a check that introduces the race it
exists to close.

### A refusal must not advertise a route around itself

`_toolkit._hint_apply` appends `apply_with: {"apply": true}` to anything reporting
`written: false`, so the refusal was handing back an **unwitnessed retry**. An agent
doing the obvious thing — resend whatever the response suggested — would have gone
straight through the check it had just tripped, and the whole binding would have been
advisory.

Nothing applyable is offered now, because nothing is safely applyable: the approved diff
describes bytes that no longer exist. Offering the *current* witness would be worse than
the original defect — a one-hop path from "refused, unreviewed" to "applied".

---

## 4. Measurement, and attribution that was never missing

**Measurement is the exact complement of the precept guard**, over the same walk and the
same manifest. The guard asks *"did a tool that may NOT write, write?"*; this asks *"what
did a tool that MAY write actually change?"* One is an accusation, the other a record,
and neither is derivable from the tool's own account of itself.

- attached **even when the call failed** — a tool can mutate the target and then fail,
  and "the call failed" is the moment a reader most needs to know what landed anyway
- an exceeded bound is **`null`, never `[]`**
- a **claimed path the walk does not show changing is a finding**, recorded with its
  coarse basis stated, for a human to resolve — not reconciled away

**Attribution was never missing; it was unreadable.** The seam has always recorded who
called: `cli` and `agent` are passed at both entrances and `record` never writes NULL.
Every read projection in the `event_log` tool simply omitted the `client` column, so
attribution was complete in the database and absent at the only interface anyone reads it
through. A ledger you cannot ask *"who did this"* is a log. One column, two queries.

Worth stating plainly: I expected to build a mechanism and found it already there.
"The field is null" and "the query does not select it" look identical from outside and
lead to completely different repairs.

---

## 5. **The stop condition that is not met**

0037 §9 requires, among other things, that **the discovery pass is clean**. It is not.
The certification says `PASS`; the evidence inside the same record says otherwise.

```text
discovery.ok   true        (because the harness process exited 0)
front_door     pass=false  mode=null domain=null mounted=0
enforcement    pass=false  "unparseable envelope: SUITE_PROJECT_ROOT=... conflicts
                            with this instance's canonical target ... (identity ...)"
tool_health    ran=0       of 12 in the last good run
composition    null
truthfulness   null
```

### This predates T8, and the dating is evidence rather than assertion

| harness run | front_door | enforcement | tool_health.ran |
| --- | --- | --- | --- |
| 2026-08-18 07:20 | **True** | **True** | **12** |
| 2026-08-18 10:33 | False | False | 0 |
| 2026-08-19 00:20 | False | False | 0 |
| 2026-08-19 18:17 | False | False | 0 |

The axes went dark between the 07:20 and 10:33 runs on 2026-08-18 — before T8 was
declared. **Three certifications have reported `PASS` since.**

**Root cause, read from the code rather than inferred:** `_harness/ro_probe_inner.py:32`
attaches by setting `SUITE_PROJECT_ROOT=target` in the child's environment. T6 bound an
installed instance to a canonical target and made that override a hard refusal — the
exact inference-versus-transport distinction T6 exists to enforce. `front_door` and
`tool_health` are computed from that same probe's output, so one root cause takes all
three axes down together. The guard is behaving correctly; **the harness is attaching the
way T6 forbade.**

### The certifier was the thing that hid it

`certify.py` set the discovery step's verdict from the harness exit code alone, while
holding the contradicting scores in the very record it wrote. Its own docstring promised:

> IT NEVER LIES BY OMISSION. A step that could not run is recorded as `"ok": false` with
> a reason — never skipped silently. **An absent result and a passing result must not
> look alike.**

**A certifier that collects evidence it does not consult is worse than one that collects
none, because the record looks thorough.** Now: any axis reporting `pass: false` fails the
step, axes producing no verdict are listed separately as `not_scored` (checked-and-failed
and never-ran are different findings with different repairs), and both are printed under
the verdict where the eye lands.

**The same defect appeared twice in the same file.** `--skip-discovery` produced
`skipped: true`, which the verdict counted as a `PASS` — while the flag's own help text
read "recorded as skipped, never as passing". A skip is now `INCOMPLETE`, borrowing
`gates/run.py`'s existing word rather than inventing a second vocabulary for the same
idea, and kept distinct from `FAIL` because "we did not look" and "we looked and it was
wrong" are different things to tell an operator.

Re-scored against the new rule, the `c728e99` record is **FAIL**, not PASS.

---

## 6. Defects of mine, and how each was found

| Defect | Found by |
| --- | --- |
| Catalog assertion read off disk — asserted only that someone had run a command, and raised `FileNotFoundError` on a fresh clone | mutation testing |
| My first mutation was invalid: I corrupted the catalog's *content*, making it the newest file on disk — a state mtime cannot detect and never claimed to | the mutation passing when it should not have |
| Staleness guards measured the fixture: awareness was first composed *during* case 1, after that case's own probe had written | reading why one case disagreed with two others |
| "States its basis and completeness" checked only that a key existed, while its failure text promised the `null`-not-`[]` behaviour | re-reading the assertion against its own message |
| Refusal advertised an unwitnessed retry | reading the refusal envelope |
| The unwitnessed-retry assertion was **vacuously green** — with no refusal there is no `apply_with` and nothing to bypass | mutation testing |
| `registry_view` read `output if not None else error`; I had just made failed writes carry an output, so the failure reason vanished from the screen | grepping for what depends on the shape I changed |
| Unimported `Path` — 46 pass to 41, three preconditions reporting `ok=None` | a green suite one commit earlier |

**A mutation fixture must reproduce the defect's causal sequence, not merely construct a
superficially similar final state.** The invalid catalog mutation is the clearest example
this project has produced: it "proved" something outside the mechanism's stated sensing
ability, and the mechanism was right to miss it.

---

## 7. Honest accounting of the movement

```text
30  red baseline (48 assertions)
+7  product progress: preconditions 1-3, witness, measurement, attribution
+1  VERIFIER REPAIR - the staleness fixture, not the product
38  ... then 52/52 after two mechanisms and four further assertions were added
```

One green came from the verifier becoming able to ask the right question. That is progress
in the factory, not evidence the product already satisfied the question, and it is not
narrated as eight product improvements.

Assertions added during implementation, each for a property discovered while building:
unwitnessed-retry, CRLF sensitivity, unmeasurable-target degradation, and the write still
landing on an unmeasurable target.

---

## 8. Everything load-bearing was mutation-tested

| Mutation | Expected red | Result |
| --- | --- | --- |
| revert `writes: target` | manifest assertion | red |
| revert `ensure_manifest` mtime refresh (manifest newer than catalog) | derived-catalog assertion | red |
| `DEGRADED_CEILING = "Apply"` | governance denies Apply; unit test | both red |
| always clamp (would satisfy the two interesting cases) | benign cases; `assertNoLogs` | red, and the gate 13 → 21 failures |
| witness offered but unchecked | refusal assertions only | red, "binds" stays green |
| witness checked but not offered | binds, refusal, approved-apply | all red |
| witness over decoded text | **only** the CRLF assertion | red |
| `changed_paths` from the tool's self-report | `project_run` and the liar | both red |
| `[]` instead of `null` on an exceeded bound | unmeasurable-target degradation | red |

---

## 9. What T8 did not do

No ProjectMapper work; both parity findings remain deferred, including the "small"
manifest half. No manifest census beyond `patch`. No harness repair. No scaffold work.
No generalized framework. `apps/` untouched.

---

## 10. Disposition

T8's own outcome is achieved and its gate is green and adversarial. It is **not parked**,
because a stop condition it declared for itself is unmet.

The unmet condition is not a T8 defect. It is a **factory** defect with a precise date and
a read-from-source root cause, and it is exactly the kind of thing that must not be
waved through on the strength of a green number elsewhere in the same file. Two items for
the operator:

1. **Repair the harness's attach path** so it binds rather than overriding
   `SUITE_PROJECT_ROOT` — restoring `front_door`, `tool_health` and `enforcement`.
   Factory work, not product work, and it is what "the discovery pass is clean" means.
2. **Re-certify** on Windows with the corrected `certify.py`, and park T8 on that record.

Until then the truthful statement is: *T8 is implemented, its gate is green, and the
acceptance walk that was supposed to corroborate it has not been running.*
