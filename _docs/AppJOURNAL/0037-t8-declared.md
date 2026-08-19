# 0037 — T8 Declared: Governed Work Loop Prototype

- **Date:** 2026-08-19
- **Tranche:** T8 — Governed Work Loop Prototype
- **Status:** **DECLARED.** Gate written, run, **red: 19 pass, 16 fail.** No implementation.
- **Preceded by:** T7 parked (0036); external review accepted (`5d0dbe5`).

---

## 1. Outcome

> A human or agent moves from **awareness → impact → preview → diff → approval → Apply
> → measured change → verification → refreshed awareness**, composed entirely from
> existing tools and the existing seam.

The property the project gains: *the human and agent not only share the same
understanding of the target — they can make a reviewed, attributable, verifiable change
against that shared understanding **without losing the evidence of what was approved**.*

---

## 2. Every interface in this gate was read from the code

That is not boilerplate, and this tranche's declaration was corrected before it was
written because of it.

The T8 sketch claimed `edit` preview returns the original text under `source`, and
proposed `diff(source, result)`. **It does not.** `tools/edit/cli.py:39` sets
`content, source = path.read_text(...), "path"` — `source` is the source *kind*. The
proposed chain would have diffed the word `"path"` against the new content, and a gate
built on it would have gone green against a product that never worked that way.

This was `CellBackend` again, in a plan rather than a query — an interface asserted from
plausibility instead of read from the code. It survived a closeout, a park and two of my
own reviews before an outside reader opened the file.

**The real review path uses one more existing tool:**

```text
read_file  ->  edit preview  ->  diff(read.content, preview.result)
```

`edit` is *not* expanded to make the imagined chain true. Composition, as declared.

---

## 3. Three preconditions, not features

Each is a live safety defect. The loop is not trustworthy until all three close, and
each was verified against source before being written into the gate.

| | Defect | Evidence |
| --- | --- | --- |
| 1 | **`patch` has no `writes` field at all** — absent, not wrong — so an Apply tool that writes target files is inferred `toolkit`. The precept guard skips it and the ledger misdescribes it | `tools/patch/tool.json` |
| 2 | **Malformed governance fails open.** A config that cannot be read warns loudly and still grants **Apply** | `policy._config_ceiling`, and the gate observed a real `write_file` succeeding under a broken config |
| 3 | **Uninterpretable tool output is reported as success.** Empty stdout, invalid JSON, and valid JSON that is not an object *all* yield `ok=True` | `invoke.py:393-398`; Charter §7.4 named this on 2026-08-06 and it is still live |

---

## 4. The load-bearing new invariant: approval binds to what was reviewed

Today `apply_with` carries only `{"apply": true}`. An approved diff against state A can
land against state B.

**The gate did not merely assert the field's absence — it demonstrated the hazard.** It
previewed a change, altered the file externally, then applied the approved edit:

```text
{'ok': True, 'replacements': 1, 'changed': True, 'written': True}
```

The mutation landed against bytes nobody reviewed.

### The interference is deliberately discriminating

The external edit **preserves the pattern's match count**. That matters: with a naive
fixture, `expected_replacements` could refuse the Apply and masquerade as the safety
mechanism, leaving the real defect green. Because the pattern still matches exactly
once, **only a genuine source-state witness can refuse it.**

Minimal close, and it belongs in `edit` rather than a framework: preview returns a
source SHA-256 carried in `apply_with`; Apply refuses when the current hash differs.

---

## 5. Two claims kept apart

Conflating these would overstate the seam.

**`changed_paths` is a coarse measured mutation signal.** The seam's manifest is
mtime+size over a pruned walk bounded at 20,000 files. Useful for staleness, audit
orientation, and finding what a shell command touched. It must carry `basis` and
`complete`, and **an exceeded bound must remain an explicit incomplete state, never an
empty `changed_paths`.**

**The gate owns the stronger claim.** It independently sha256s the whole fixture to
assert that *only the approved content changed*. Evidence for that assertion does not
come from the thing under test.

---

## 6. Verification means `test` or `lint`

`command_profile` also detects `setup` and `run`. Neither answers *"is it still
correct"* — one prepares, the other executes. A target supplying neither offers **no
verification**, and reporting that honestly is a success. `_theCELL` detects only
`run_bat` and `setup_env`; that is a true answer about that target, not a failure of the
loop.

---

## 7. The awareness transition

T7 made this assertable rather than inferable, because revision records are immutable
and evidence is captured at observation time.

```text
before   revision X + evidence X, awareness fresh
after    exact filesystem change proven by hash; X untouched; awareness reports stale
refresh  revision Y exists, Y != X, evidence Y describes the new target,
         and X still drills down to the OLD evidence
```

That proves history, not merely that `attach` returned a different string.

---

## 8. Non-goals

No new diff, approval, verification or runner subsystem, and the gate asserts none was
registered. No `attach` rewrite. No second chain engine and no speculative enlargement
of the first. No One Surface. No incremental or semantic invalidation — coarse staleness
only. No new tool unless an end-to-end attempt demonstrates no existing tool supplies it.
**`apps/` is not touched** — that belongs to parity. No backlog cleanup, packaging work
or architecture work enters this tranche.

---

## 9. Stop condition

The full loop completes on the software target, degrades truthfully on the records and
empty targets, all three preconditions are closed and mutation-tested, `certify.py`
reports **PASS on Windows** (the zero-skip authority), the discovery pass is clean, and
the operator approves.

---

## 10. Declaration state

**19 pass, 16 fail.** The passes are pre-existing invariants under protocol §5.1a — the
payload materialises, instances install, awareness still works, no forbidden machinery
exists yet. The 16 failures are the tranche.

Implementation proceeds by the smallest increment each failing cluster demands, and
every load-bearing assertion is mutation-tested before it is believed. Five assertions
escaped mutation during T7; the family is always the same — satisfied by reading back a
stored value, or by a fixture that cannot tell two implementations apart.
