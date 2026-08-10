# 0021 — T5 Parked; T6 Derived

- **Date:** 2026-08-09
- **Tranche:** T5 — Ownership and Distribution Model
- **Status:** **PARKED.** Approved by the operator at BCC §2.8 step 12.
- **Corrects:** 0020 §10 — see §4 below.

First tranche closed under the amended loop, and the first parked by operator
approval rather than by the builder's own account.

---

## 1. Closeout conditions applied

Approval was granted subject to two required changes. Both are executable, not prose.

### 1.1 Narrowed, not deleted

The operator's distinction: **a useful partial detector is not a complete proof of an
end-state condition.** Neither weak assertion was deleted — a tripwire that fires is
information, and a deleted tripwire is nothing. What was removed is each one's claim
to be more than it is.

**`PREDECESSOR_NAMES` → `KNOWN_PREDECESSOR_SENTINELS`**, and the assertion narrowed
from *"no build-machine path or predecessor name ships"* to *"...or **known
predecessor sentinel** ships"*.

**The runtime vend is no longer called a vend.** Checked first against the operator's
test — does any retained assertion state or imply that `sidecar_install` is the
canonical installation entrance? It did so by *framing*, not by assertion: section 4
was titled "a REAL vend, inspected" and the gate's OUTCOME read "the sidecar vends
only itself". Both retired. It is now "materialise a payload **fixture**, and inspect
it", and the outcome is "one declared ship manifest, and a payload containing only
the product". Six assertion names changed with it — *"the vend succeeds"* is now
*"the payload fixture is produced"*.

The section carries an explicit disclaimer, and `gates/t05` asserts the disclaimer's
presence so it cannot quietly erode:

> Its use confers no product authority. Nothing below may be read as evidence about
> canonical installation, installed-instance correctness, or setup lifecycle.

### 1.2 Machine-visible, not just recorded

`gates/t01` declares `KNOWN_LIMITATIONS` — a structured tuple carrying `assertion`,
`coverage`, `limitation`, `contributes_to_E11_completion: False`, and `disposition`.

`gates/run.py` prints them beneath the gate's verdict. Not behind a flag: an
assertion can be honest in its own text and still be misread in a column of green.

```
  [PARTIAL] no build-machine path or known predecessor sentinel ships
            coverage: partial
            does NOT contribute to closing its end-state condition
            disposition: strengthen or replace during the lineage/scrub tranche
  [PARTIAL] the payload fixture is produced
            coverage: transitional
            does NOT contribute to closing its end-state condition
            disposition: eliminated by T6
  => t01_ship_manifest PASS

SUITE: PASS
       - with declared PARTIAL coverage above. A green suite is not evidence
         that every end-state condition is complete.
```

Four new `t05` assertions enforce this: the limitations are declared, the runner
surfaces them, and the legacy path is disclaimed in both required phrasings.

---

## 2. Final state

Fresh clone, **no environment variables set**:

```
ruff check .          ->  All checks passed
python -m unittest    ->  Ran 85 tests, OK (skipped=8)
python gates/run.py   ->  t00 t01 t02 t03 t04 t05  SUITE: PASS
                          133 assertions, + 2 declared PARTIAL
_harness run probe    ->  6/6 sections pass
```

Assertions grew 129 → 133 during closeout. **Two of the six gates now carry declared
partial coverage**, which is the honest reading of the same green suite.

---

## 3. Scoreboard

**E8 NOT MET. E11 NOT MET.** Confirmed by the operator, and not softened because the
count fell from five green to three.

> A smaller truthful scoreboard is preferable to preserving green states whose proofs
> depended on assumptions we have now explicitly rejected.

Three met, four partial, six not started. Both demotions are **corrections, not
regressions** — the conditions were measured against wordings that did not describe
the product, so neither was ever true in the sense now stated.

---

## 4. Correction to 0020 §10

0020 wrote *"the dependency chain has one root: `InstanceContext`"*. That is wrong
if read as making the canonical payload depend on instance identity. The operator's
correction, adopted:

```
SOURCE                            INSTANCE DEFINITION
   |                                     |
   v                                     |
CANONICAL PAYLOAD  (generic,             |
   |                target-neutral)      |
   +------------+  TARGET  +  PARAMS  <--+
                |
                v
        INSTALLATION CORE
          ^           ^
          |           |
      setup app    harness
                |
                v
        INSTALLED INSTANCE  ->  InstanceContext  ->  runtime / tools / UI
```

**Two facts, not one chain.** *Payload definition* — what product content exists — is
generic and target-neutral. *Instance definition* — how one installed copy is
identified and bound — is separate. They meet at the installation core.

This makes the ordering better, not merely different: T6 can consume today's
transitional fixture producer while replacing the duplicated installation and
identity semantics, and the later payload tranche can replace how the product body
is assembled **without also having to invent installation identity at the same
time.**

The installed sidecar does **not** consume the installation core in order to create
another instance.

---

## 5. T6 — derived, pending declaration review

**T6 — Instance Identity and the Installation Core.**

*Derivation, not a declaration.* The gate is written at declaration, not here.

**Expected collapse:**

```
packaging/installer           \
runtime sidecar_install        \      authoritative installed-instance definition
harness manual copy/install     >  ->            |
config instance discovery      /          installation core
tool-level sidecar-name guess /            ^          ^
                                           |          |
                                       setup app   harness
```

**Why it is the foundational slot:** `packaging/installer/install.py` — the product's
install entrance — writes no `.suite_sidecar`, so it produces an instance that
cannot resolve its own target. Two development paths manufacture a working instance;
the shipping one does not. Every green install result to date came from a path that
is not the product's.

**Coupling to One Surface, recorded because it is the part that matters:** by the
time One Surface resumes, `sidecar_install` must no longer appear to the runtime
registry or UI as an ordinary product capability merely because historical
implementation still contains it.

**Likely non-goals:** the positive payload manifest, the payload assembler, the
harness split, the corpus move, contract seed generation.

---

## 6. One Surface — the standing commitment

**Reassess immediately after T6 closes.** Recorded here, in the plan, and in 0020, so
another infrastructure chain cannot quietly grow in front of it.

Salvage is ready at `gates/_deferred/t05a_observe_select.py.deferred`.

---

## 7. Carried

- `packaging/installer/install.py` writes no `.suite_sidecar` — **severe**, T6
- `installer_view` offers two precept-violating options the tool rejects — T6
- `tools/sidecar_install` is registered runtime capability — T6
- `_harness` `LINEAGE` and `t01` `KNOWN_PREDECESSOR_SENTINELS` are both calibrated to
  another project — declared partial; belongs with the E11 scrub
- `_harness/targets/` — 639 committed files, right need, wrong ownership domain
- the two contracts still hand-maintained; the seed still has no renderer
- 20+ unpushed commits; **CI has still never run**, and it is the only path
  exercising the default configuration on Windows
- Windows process-group kill unverified

---

## 8. Note

T5 produced no runtime behaviour and is the second consecutive tranche with nothing
to look at. It also removed two false greens, retired an obsolete invariant without
rewriting history, generalised a rule rather than taking an exception to it, and
found that an entering agent following the documented path could never reach the
product authority.

The next tranche is foundational. **The one after it is looked at.**
