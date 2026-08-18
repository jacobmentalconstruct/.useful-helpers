# 0035 — T7 Closeout: Shared Project Awareness Prototype

- **Date:** 2026-08-18
- **Tranche:** T7 — Shared Project Awareness Prototype
- **Status:** **AWAITING APPROVAL** (BCC §2.8 step 12). Not parked. One certification
  gap is named in §7 and it is the operator's to close.
- **Declared in:** 0033. **Sized by:** C1b (0032).

---

## 1. Outcome

> Existing deterministic tools are composed into **one compact, evidence-backed current
> orientation** of the bound target, persisted against the instance, and exposed as the
> **same revision** to human and MCP agent.

Delivered as **one shared module and two call sites**. No awareness engine, no database,
no schema framework, no private orchestration. Every contributor runs through
`seam_call`; every raw observation is stored in the existing content-addressed
`evidence` tool; the envelope persists under the existing state root.

**Charter §3.3 walk steps advanced:** 6 (it maps the target), 7 (the user can inspect
that map), 8 (an agent receives the *same* awareness), and the awareness half of 13
(restart destroys neither identity nor durable awareness). Step 14 — relocation — was
advanced as well, unplanned, because proving it exposed a defect.

---

## 2. Why the tranche was shaped this way

C1b (0032) had already reduced T7 before it existed. Of `attach`'s 24 responsibilities
T7 touched 8, discharged **one** duplication, and depended on no live `apps/` member.
That is why this reads as an increment log rather than a subsystem build.

The gate was written **black-box on purpose**: no module, no class, no file named. T7's
nouns invite an `AwarenessManager`, an `AwarenessStore`, an `AwarenessEngine`. Naming
none of them meant the failing assertions had to say what machinery was actually
absent — and what they said was *one connective mechanism*, not a subsystem.

**Four semantics were locked before implementation**, and one of them made the gate
stricter than it had been declared:

| | |
| --- | --- |
| 1 | only semantically selected observation data enters evidence identity |
| 2 | revision identity is content-anchored to instance + scope + evidence, never sequential |
| 3 | handles are identifiers owned by existing tools — no handle framework |
| 4 | drill-down recovers the evidence **actually used** for revision X, never a rerun |

Semantic 4 retired an allowance the gate had granted: provenance may no longer point at
a re-runnable invocation. Re-running answers *"what did revision X know?"* with *"what
would I know today?"* — a plausible answer substituted for the true one, and it makes a
persisted revision unfalsifiable.

---

## 3. What transpired, in four increments

**Increment 1 — `.git*` prune, and identity transport.** `attach._probe` filtered with
`not d.startswith(".git")`, written for `.git` — which `PRUNE` already contained — and
silently swallowing `.github` and `.gitlab`. CI configuration was invisible to the map.
Removed rather than narrowed: a prefix test beside a named exclusion set is a second,
weaker rule nobody declared.

Then the first genuinely missing mechanism. Awareness must belong to an *instance*, so a
tool has to know which instance it serves — and it could not. Proving that exposed a
seam: `InstanceContext.as_env()` is the **declared** transport surface, but
`invoke._dispatch` hand-builds the child environment and never consults it. Two
descriptions of one fact, so adding a field to `as_env()` alone would have reached
nothing. Closed where identity is already resolved.

**Increment 2 — the vertical slice.** Observations → fingerprint → content-addressed
evidence → compact envelope → revision → persistence. 4/33 to 34/34.

**Increment 3 — the two semantic seals**, after operator review. Detailed in §4.

**Increment 4 — hub purposes.** The dogfood asked whether the envelope was *useful* or
merely *schema-correct*. The evidence answered: awareness said *"41 files, `src.backend`
is the hub"* while the observation it had just captured said `src.backend` is the
*"Orchestration / Logic Hub — pure downstream task list runner"* wiring sixteen
microservices. `report` had computed per-module structure, rendered it to prose, and
discarded it — while its own manifest declared a `modules` field. Honouring that
contract made the purpose selectable without parsing markdown back out of a rendering.

---

## 4. The defects this tranche found

Seven, of which **five were in the verifier rather than the product** — which is the
pattern this project keeps recording and the reason the gate is trusted only after it
has been seen to fail.

| | Defect | Where |
| --- | --- | --- |
| 1 | `.git*` prefix prune hid CI configuration | product |
| 2 | identity was not transported; `as_env()` and `_dispatch` disagreed | product |
| 3 | **blanket key-name denylist discarded real evidence** — `path`, `created`, `db` stripped recursively, so a finding moving from `a.txt` to `b.txt` produced the same fingerprint | product |
| 4 | **absolute location inside the identity** — moving a target and its instance together changed the revision, reintroducing the absolute-path identity T6 removed | product |
| 5 | the workbench profile bound by stored absolute path, so `attach` refused after a legitimate move | product |
| 6 | `_output` scanned for single-line JSON while the CLI pretty-prints — **every call returned `{}`** | gate |
| 7 | the digest baseline was taken before the gate's own write, charging the product with the gate's edit | gate |

Plus two of my own selections that were wrong and caught by measurement: preferring the
module docstring returned `FILE: src/core/invoke.py` as the purpose of five hub modules,
and `_findings` and `canonical_observation` selected purpose *separately*, so findings
came back empty on exactly the codebases the class-preference was written for.

### Four mutations escaped before they were closed

Every one had the same shape — an assertion satisfied by **reading back a stored value**,
or a fixture that could not tell two implementations apart.

- a **timestamp counter** passed all 33 assertions, because each read the revision back
  from persistence and a counter round-trips as well as a hash
- the **move assertion passed with absolute identity restored**, because a plain
  re-engage returns the persisted revision without recomputing
- the **helper test passed with the denylist restored**, because the fixture held only
  fields both implementations agreed on
- removing the **volatile-key exclusion** passed the black-box gate, because no current
  contributor emits a timestamp

The first three are closed and confirmed red against their mutations. The fourth is
closed at the helper level with a discriminating fixture, because the black-box gate
genuinely cannot reach it — recorded rather than papered over.

---

## 5. How the outcome satisfies the stop condition

T7's declared stop condition (0033):

> Both projections resolve the same revision id on all three acceptance targets, with no
> application-layer dependency, and the gate suite green on both platforms.

| Clause | Evidence |
| --- | --- |
| **both projections resolve the same revision** | assertion 21 compares the CLI and the real MCP entrance mechanically, not by similarity. PASS |
| **all three acceptance targets** | software, records, empty. All three produce a truthful envelope, declare their limitations, and the thin ones invent no software findings. 9 assertions. PASS |
| **no application-layer dependency** | assertion 30 reads the ledger and asserts no invoked tool resolves under `apps/`. PASS |
| **gate suite green** | 35/35 on Linux; **SUITE: PASS** across t00–t07 on Windows |
| **both platforms** | **partially — see §7** |

### The four mechanical properties, measured rather than asserted

**Context reduction.** Ratio `0.018` on a real 254-file target: **133,477 B of
contributor evidence → 2,343 B of projection.** The threshold is `≤0.25` with an
absolute ceiling of 8,192 B. This is the product's core reason to exist made
falsifiable: the machine absorbs rich evidence locally, the model receives a compact
projection.

**Revision identity.** Same target re-observed → same fingerprint. One file added →
different fingerprint. **Target reverted → the earlier revision returns.** That last one
is the only assertion that distinguishes a revision from a counter, and it exists
because a counter passed everything else.

**Canonical handles.** Every promoted handle carries its owning tool and resolves
through it. Hand-verified on `_theCELL`: `symbol_graph refs src.backend` →
`match_count: 20`, with `Backend.__init__` resolving to sixteen microservice
constructors at exact line numbers. This is the anti-hallucination property, and it
exists because a model in this project invented `CellBackend` from a module name and
reported the correct refusal as a capability gap.

**Drill-down.** Hand-verified: `evidence get evd_c244220f7a` returned the stored
observation, hash `43f82f46…`, intact — the evidence captured when revision `084d4b5c`
was formed, not a rerun.

### The discovery pass

Protocol §3.4, run on Windows against the real consumer entrances:

```text
PRECEPT      PASS  (install=0 runtime=0)
FRONT DOOR   PASS  domain=python-app  mounted=24
TOOL HEALTH  12/12 ok
CLEANLINESS  PASS  (0 lineage hits)
ENFORCEMENT  PASS  (seam rejected a target-writing Observe tool, write detected)
```

---

## 6. What T7 did not do

No target mutation — that is T8. No `attach` rewrite: the reduction pass was **one**
responsibility, the tree probe, discharged only where T7 touched it. No second chain
engine and no speculative enlargement of the first. No One Surface. No awareness
ontology. **No tool for `newest_mtime`** — *"no canonical tool reports it"* is not *"we
need one"*, and the existing staleness mechanism remains front-door logic until a second
consumer independently needs it.

`apps/` was not deleted. Nothing has been demonstrated that would justify it.

---

## 7. The one gap, and it is the operator's

**Windows certification covers commit `46dcc4f`. Increment 4 (`df67fec`) has been
verified on Linux only, and is unpushed.**

That increment touches `tools/report/cli.py` and `tools/awareness_shared.py` — no
platform-specific code — so the risk is low. **Low risk is not evidence.** Windows is
this project's zero-skip authority precisely because it has twice caught defects no
Linux run could see, and the stop condition says *both platforms* without qualification.

To close it:

```bat
cd C:\Jacob\_AppDesign\_SANDBOX\.useful-helpers-workbench
git push origin main
python -m ruff check .
python smoke_test.py
python gates\run.py
```

Expected: 86 tests with 1 skip, and `SUITE: PASS`.

---

## 8. Carried

- E8 and E11 remain **NOT MET**. T7 advanced no lifecycle row.
- The **canonical payload assembler** remains deferred to `P-install-packaging`.
- `report` now returns `modules` **and** `markdown` — the same information twice,
  measured at 30,577 B on `src/` against ~14,800 B before. Both are declared and both
  are consumed, so it is the cost of honouring the contract rather than a defect.
  Backlogged.
- `dev_server_manager`'s direct import of `tools.command_profile.cli`, the governance
  fail-open posture, and the absent layering policy all remain open from 0034.

---

## 9. What T7 hands to T8

This is the substrate T8 was waiting for. It no longer begins with *"understand the
project"*; it begins with a concrete object:

```text
revision X + evidence X   ->  canonical handle  ->  impact  ->  preview  ->  diff
   ->  approval  ->  Apply  ->  changed paths  ->  target-native verify
   ->  awareness stale  ->  refresh  ->  revision Y + evidence Y
```

Because evidence is captured at observation time and revisions are content-anchored,
attribution across that loop is a comparison of two immutable records rather than an
inference.

**T8 is not declared. No T8 work begins before T7 parks.**
