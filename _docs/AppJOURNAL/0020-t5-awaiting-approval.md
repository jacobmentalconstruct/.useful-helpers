# 0020 — T5 Complete: Ownership and Distribution Model

- **Date:** 2026-08-09
- **Tranche:** T5 — Ownership and Distribution Model
- **Status:** **AWAITING APPROVAL** (BCC §2.8 step 12). Not parked.
- **Declared in:** 0019

---

## 1. Declared outcome and non-goals

**Outcome.** One authority per normative fact, and a stated deployment topology — so
every later packaging, installation and boundary decision derives from a single
owned statement rather than being argued case by case.

**Not for:** moving product modules · building a payload assembler · splitting the
harness · splitting the gates · moving the corpus · writing the installation core ·
writing `InstanceContext` · creating a fifth authority document · One Surface work.

**Held.** No product module moved. The only file movements were governance and gate
hygiene needed to make the declaration truthful — quarantining a withdrawn gate and
preserving retired assertions — which the operator classified as in scope.

---

## 2. Initial gate state

```
26 FAIL  /  4 PASS      (at declaration, 0019)
```

The four passes were **pre-existing invariants T5 must preserve**, not completion
claims — protocol §5.1a:

| | Why it already held |
| --- | --- |
| no fifth authority document was created | `.bcc` held exactly the live set |
| `STATE_ROOT` is a distinct named concept | already used in the Charter |
| the withdrawn T5a gate is out of active discovery | done as declared precondition |
| the withdrawn T5a gate is preserved with provenance | same |

No artificial red was engineered. The purpose is proving the checks discriminate,
not maximising failures.

---

## 3. Final gate state

```
t05_ownership_model   44 assertions   PASS
```

---

## 4. Full cumulative suite

Fresh clone, **no environment variables set**:

```
ruff check .                ->  All checks passed
python -m unittest          ->  Ran 85 tests, OK (skipped=8)
python gates/run.py         ->  t00 t01 t02 t03 t04 t05  SUITE: PASS
                                129 assertions
_harness run probe          ->  PRECEPT PASS (install=0 runtime=0)
                                FRONT DOOR PASS · TOOL HEALTH 12/12
                                TRUTHFULNESS 0 false positives (naive 1, policy prevented 1)
                                CLEANLINESS PASS · ENFORCEMENT PASS
```

---

## 5. T1 assertion census

All **22** assertions in `gates/t01_ship_manifest.py` examined — not only the two
expected. Two retired.

### Superseded historical invariants

| Assertion | Premise |
| --- | --- |
| *"the manifest itself ships"* | a vended sidecar must be able to vend |
| *"the payload can reproduce itself exactly (self-hosting)"* | same |

Both rested on `instance → instance`. The corrected chain is
`source → payload → setup → instance`, so a proof that self-vending works proves
something the product no longer promises. Retiring them also removed the
generation-2 install that called `sidecar_install` **from inside an installed
sidecar** — the exact behaviour the Charter now excludes.

No replacement stands in their place **deliberately**. The replacement is owed by T6:
a positive install manifest, a payload assembler, conformance proven against the
built payload. Asserting a weaker version meanwhile would be the silent disabling
§5.1 forbids.

### Retained active invariants

The manifest exists and is single source of truth; consumers derive from it;
categories declared; `packaging/` is INSTALLER_ONLY and intact; foreign distinguished
from unshipped; the vend succeeds and leaks no development zone, no installer, no
nested instance, no `.git`; the payload ships its own minimal ignore file; the
installer ships blank; file count within bound.

### Known-weak retained assertions — recorded, not fixed

Two survive with defects that are **not** supersessions and must not be dressed as
such:

- **`PREDECESSOR_NAMES`** in `t01` is the same wrong list as the harness's `LINEAGE`
  — `mindshard`, `appfoundry`, `bdneural` — none of which are this project's
  predecessors. The blankness check is a false negative.
- **the vend is performed by `tools/sidecar_install`**, a runtime tool, because it
  is the only payload-producing mechanism that exists. Retiring it now would leave
  T1 unable to inspect any payload and would gut the surviving E11 assertions.

Both are why **E11 is now marked NOT MET**. Fixing the check belongs with fixing the
leak, in T6. The claim was withdrawn rather than the evidence quietly patched.

---

## 6. Evidence that no superseded assertion remains active

Asserted, and mutation-tested rather than assumed:

```
[PASS] no superseded assertion remains in the active proof set
[PASS] the retired assertions are preserved with provenance
[PASS] the active suite no longer drives a second-generation vend
```

Mutation — reinstating `r.check("the manifest itself ships", ...)` in `t01`:

```
[FAIL] no superseded assertion remains in the active proof set
       still asserted in t01: ['the manifest itself ships']
```

The check discriminates.

---

## 7. Rule 8, generalised — and T5's own entrance

Rule 8 named only `cli`, `mcp`, and the GUI. T5's outcome is a governance model with
no runtime capability to invoke, and satisfying the rule by locally reinterpreting
"real entrance" for one tranche would have produced *protocol text ≠ actual
practice* — the exact defect T5 formalises. So the abstraction went into the rule:

> **Exercise a real consumer entrance appropriate to the tranche outcome.** A gate
> must exercise the thing under test through the entrance used by its real consumer,
> not only through an internal implementation seam.
>
> runtime capability → `cli`, `mcp`, GUI, setup executable, or other actual caller ·
> governance or authority surface → the documented context-entry read path an
> entering agent is instructed to follow · build or distribution artifact → the
> actual assembler/build/package entrance · any other artifact → its real consuming
> interface.
>
> Direct function-level assertions may supplement this. They do not substitute for
> consumer-path proof where such a path exists.

**T5's entrance, walked rather than asserted:**

```
BCC-CONTEXT-ENTRY  ->  the anchors it names  ->  every one resolves
                   ->  the product authority it names  ->  CHARTER.md
                   ->  its [OWNS: SIDECAR:*] declarations
```

Four assertions. The path must reach the Charter **without already knowing where it
lives** — which required adding the product authority to the entry path, since the
contract had never mentioned it.

**Also corrected:** rule 8 cited T1 as asserting through "a real `sidecar_install`".
That was the project's belief; `sidecar_install` is a runtime tool that installs
another sidecar, and the product's entrance is `packaging/installer/`. History
preserved, current normative prose corrected.

---

## 8. Reclassification of 0018

Appended to 0018 as §7, on **both axes** — 29 findings, each with an ownership domain
and a disposition, plus authority role where it clarifies.

**Every finding fits a domain.** The stop condition — a finding fitting none, meaning
the six domains are wrong — was not triggered.

**Four findings changed severity under the model:**

- `_harness`/`.bcc` names in `.gitignore`, `ruff.toml`, `payload.py`: violation →
  **valid self-knowledge** (§5.5)
- `.github/`: one finding → **two** — valid in the source repository, a
  **distribution leak** in the payload
- `_harness/targets/`: bloat → **correct need, wrong ownership domain** (§5.7)
- `developer_cert.pfx`: severity dropped on measurement — untracked, not committed

---

## 9. Discovery pass

**Harness:** 6/6 sections pass. Its `CLEANLINESS PASS` remains a **known false
negative** — recorded, not trusted.

**Mutation, three probes:**

| Mutation | Result |
| --- | --- |
| remove one `[OWNS: ...]` declaration | `[FAIL] SIDECAR:TARGET-OWNERSHIP has exactly one declared owner` |
| a second surface declares a fact | `[FAIL] … exactly one declared owner` + `[FAIL] the Plan cites the model rather than restating it` |
| reinstate a superseded assertion | `[FAIL] no superseded assertion remains in the active proof set` |

**Found during implementation, by the gate failing:**

1. **My own slice was wrong.** `bcc.split("BCC-ONE-AUTHORITY")` matched the *anchor
   map entry* first, so the check measured a section 400 lines from the rule. Now
   split on `[ANCHOR: ...]`. Second instance today of a text search matching the
   wrong occurrence.
2. **The contract never mentioned the Charter.** An agent following the documented
   entry path would never reach the product authority. Invisible until the entrance
   was walked instead of assumed — which is the whole argument for rule 8.

**Differential:** fresh clone, zero environment variables, all green.

---

## 10. Derived implementation dependencies

Observed, not declared as tranches:

```
positive install manifest ──needs──> a payload BUILD producing an artifact
                                     (nothing produces one today; t01 inspects a
                                      vend made by a runtime tool)

harness split ────────────needs──> ONE INSTALLATION CORE
                                     (the harness currently compensates for the
                                      product installer's missing marker)

installation core ────────needs──> InstanceContext
                                     (what "an installed instance" IS must exist
                                      before something can create one correctly)

corpus externalization ───independent
gates trichotomy ─────────needs──> the verification engine's shape, which follows
                                     from the harness split
contract seed generation ─independent
lifecycle boundary tests ─needs──> installation core + InstanceContext
```

The chain has one root: **`InstanceContext`**. Everything about installation depends
on what an instance is, and today that identity is a basename guess from an
environment variable, created by two development paths and not by the product's.

---

## 11. Recommended next tranche — exactly one

**T6 — Instance Identity and the Installation Core.**

*Sketch, not a declaration.* One authoritative `InstanceContext` — durable identity,
structural location, relative target relationship — and one installation core
consumed by both `packaging/installer/` and the harness. Retire `sidecar_install`
from runtime capability. Every tool resolves context rather than rediscovering it.

Why this and not the payload manifest: the manifest needs a build to inspect, the
build needs to know what it is building *into*, and both need an instance definition.
`InstanceContext` is the only item with no unmet dependency.

Why not corpus or contract generation: both are genuinely independent and genuinely
smaller. They are candidates for interleaving, not for the foundational slot.

---

## 12. One Surface — explicit reassessment point

**Immediately after T6 closes.** Recorded here so it cannot be quietly deferred
again.

At that point One Surface is redeclarable with its boundary settled: the operational
surface of **one already-installed instance working on one bound target** — not a
mixture of runtime workbench and setup application. `installer_view` will have left
the runtime, and *"every registered tool reachable from the shell"* will no longer
imply exposing *install another sidecar*.

Salvage is ready at `gates/_deferred/t05a_observe_select.py.deferred`, with the
survivable assertions separated from the superseded assumptions.

---

## 13. Carried

- **E8 and E11 are now NOT MET** — corrections, not regressions. Both were measured
  against wordings that did not describe the product. Scoreboard: three met, four
  partial, six not started.
- `packaging/installer/install.py` writes no `.suite_sidecar` — **severe**, T6.
- `installer_view` offers two precept-violating options the tool rejects.
- `tools/sidecar_install` is registered runtime capability.
- 17+ unpushed commits; **CI has still never run**, and it is the only path
  exercising the default configuration on Windows.
- Windows process-group kill unverified.
