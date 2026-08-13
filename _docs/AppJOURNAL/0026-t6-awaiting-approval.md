# 0026 — T6 Complete: Instance Identity and the Installation Core

- **Date:** 2026-08-13
- **Tranche:** T6 — Instance Identity and the Installation Core
- **Status:** **AWAITING APPROVAL** (BCC §2.8 step 12). Not parked.
- **Declared in:** 0024, amended in 0025

---

## 1. Outcome

Given a valid payload, the standalone setup application installs **one canonical
instance** into one chosen target. It has durable self-contained identity, resolves
its target structurally without basename, marker or environment guessing, survives
relocation, preserves continuity across update, supplies canonical roots to every
runtime consumer, and **the installed runtime no longer exposes installing another
sidecar as a product capability.**

**Prototype walk (Charter §3.3): steps 3, 5, 13 and 14 are materially more true.**
Steps 6, 7, 8, 10, 11 and 12 are untouched by design — those are the awareness and
operation tranches.

---

## 2. The architecture, entire

```
SOURCE       payload.materialise → standalone setup → instance.create → instance
RUNTIME      instance.resolve → InstanceContext → config → invoke
                              → transported context → _toolkit → tools / attach
```

No marker. No basename discovery. No cwd inference. No second runtime installer. No
harness installer. No tool rediscovering the project. **Four surfaces answered "what
is the sidecar" at declaration; one answers now.**

---

## 3. Initial and final gate state

```
declaration   7 assertions, 0 pass       (0024)
final        24 assertions, all pass, both platforms
```

The four initial passes recorded in 0024 were pre-existing invariants, not completion
claims (protocol §5.1a).

---

## 4. Certification

| | Linux | Windows |
| --- | --- | --- |
| `ruff check .` | clean | clean |
| `smoke_test.py` | 84 OK (7 skipped) | 84 OK (1 skipped) |
| `gates/run.py` | t00–t06 PASS | t00–t06 PASS |
| real installer / identity / update / move | executed | executed |
| discovery pass (`harness run`) | 6/6 PASS | — |
| `SUITE_DISABLE_CONTAINMENT=1` mutation | inert (POSIX) | RED, as required |

**Platform evidence is separate on purpose.** A Linux green certifies Linux. The
Windows column is what proves the install path users actually get.

---

## 5. What the closeout audit found — six seams, all T6's own

Reported by the operator against a fresh snapshot, after the gate was already green.
None indicated T6 had gone wrong; they surfaced *because* the identity model finally
became concrete enough to challenge.

**1 — an installed instance could be rebound by an environment variable.**
`config.py` read `SUITE_PROJECT_ROOT` *before* `instance.resolve()`, so an instance
whose manifest said "I belong to A" would accept `SUITE_PROJECT_ROOT=B`. Identity now
resolves first, and a conflicting variable **raises** with the instance UUID in the
message. The variable still governs the uninstalled case — environment for
development, identity for installation.

**2 — `attach` was a second target authority.** It preferred an arbitrary `target`
argument over the canonical root. Now it consumes `project_root()`.

*And the first fix was too strict:* requiring exact equality broke `genesis`, which
scaffolds a project in a subdirectory and orients on it. That surfaced a distinction
worth naming — **scope is not rebinding.** A path *inside* the bound target is a
narrower view of the same reality; a path *outside* is asking this instance to be a
different instance. The rule is containment.

**3 — the relationship was under-validated.** Rejecting absolute paths was not
enough: any relative path landing on a real directory could become `TARGET_ROOT`. The
setup application creates `INSTANCE_ROOT` as a direct child of `TARGET_ROOT`, so that
is now enforced. Schema gained a floor — 0 and negative are malformed, not "older" —
and `bool` no longer passes `isinstance(int)`.

**4 — `STATE_ROOT` had three answers.** `InstanceContext`, `config.Paths` and
`_toolkit` each interpreted `SUITE_STATE_ROOT` independently. Where an instance
exists, identity decides; the variable governs only the uninstalled case. Same rule
as the target root, applied to the same class of defect.

**5 — two assertions were weaker than their names.**

- *"malformed identity fails loudly"* was checked as `_target_of(...) is None` — and
  a **silent** None satisfies that exactly as well as a raised error. Split into two
  assertions, with the probe's exception text carried out of the subprocess instead
  of discarded. **Mutation-tested:** making `resolve()` return `None` instead of
  raising now turns it red. The old check would have passed.
- *"target-owned content unchanged"* read one file and asserted another existed. Now
  a **whole-target sha256 manifest**, including a deep nested file, reporting added,
  removed and differing paths.

**6 — authority surfaces were stale.** The Plan still said "T6 next", still carried
the pre-renumber *"T6 — Contracts for Uncontracted Daily Drivers"*, and still owed
payload work to T6. `config.py` cited journal 0026 — which did not exist until this
entry. All corrected.

---

## 6. The red→green sequence, preserved

Recorded because it shows the tranche was corrected **before** implementation rather
than having its tests retrofitted around finished code.

| | |
| --- | --- |
| the first gate **could not run** | it assumed a payload that does not exist in the source repo — a circular dependency in my own plan |
| it invented a **nonexistent installer option** | `--folder`, added so a test could prove identity is not the basename. Product surface grown to suit a gate |
| it parsed `file_tree` with **guessed keys** | `paths`/`files`; the tool returns `rows` |
| its identity census found only **writers** | `suite_home()` writes nothing and was the other half of the same guess |
| its installer census was **incomplete** | 3 named, 9 found, of which 3 were docstrings |
| the amended gate then **exercised the real installer successfully** | `rc=0` |
| and the installed product **failed target resolution** | the finding the tranche exists for, demonstrated rather than read |

---

## 7. Verifier defects found in T6 — seven, all the same family

Each one *passed or failed for a reason unrelated to the product*:

1. the installer's module loader never registered in `sys.modules`, so `@dataclass`
   raised inside `dataclasses.py` and read as a stdlib bug
2. the gate's probe was **not valid Python** — `try:` after a semicolon in a `-c`
   one-liner. It died every run; three assertions failed for nothing
3. `update preserves identity` passed by comparing `None` to `None`
4. `_code_only` joined tokens with newlines, destroying every multi-token pattern —
   the census fell 9 → 1 **by blinding itself**
5. the census then flagged `packaging/installer` for having an install mode
6. `artifact_cleaner` substituted for `sidecar_install` **with no root**, pointing a
   destructive cleanup at the live repository under `apply: true`
7. `_is_test_scope` covered `_harness/`, so the harness vanished from the identity
   census **because it was excluded, not because it stopped manufacturing identity**

Number 7 was named as a hazard by the operator two turns before it happened.

---

## 8. What only the discovery pass caught

After all seven gates were green, `harness run` reported:

```
FRONT DOOR   FAIL  domain=None  mounted=0
TOOL HEALTH  0/0
TRUTHFULNESS missed=1
```

The harness had **two installers of its own** — a copytree with a hand-written
`.suite_sidecar`, and a mode dispatching the deleted `sidecar_install`. It was
installing a sidecar that could not find its own target, so every subsequent
measurement was hollow. The gate suite could not see this, because no gate runs the
harness.

Both are now one call to `packaging/installer/`. The harness stages fixtures; it does
not create instances. **A verifier that reimplements the thing it verifies is not
observing it.**

Protocol §3.4's claim — that the gate answers *did this do what was claimed* and only
the discovery pass answers *what else is true* — is now demonstrated rather than
argued.

---

## 9. Carried

- **E8 and E11 remain NOT MET.** T6 supplies the install row of E8's phase matrix;
  update, uninstall, startup and self-maintenance are unproven. E11 awaits the
  lineage scrub.
- `t01` retains two assertions of **declared partial coverage**, printed by the runner.
- The payload is produced by subtracting exclusions from a source tree — a fixture,
  not the canonical positive assembler.
- `docs-refresh` prints `_docs/TOOLS.md` while writing `docs/` — a leftover of the
  collapse.
- `docs/ARCHITECTURE.md` §4 and `AGENTS.md` still describe marker-based resolution.
- Three docstrings (`genesis`, `scaffold_project`, `payload.py`) still describe the
  retired `sidecar_install` chain. **Not census violations — documentation staleness
  created by T6**, and behaviour must not change to fix them.

---

## 10. Next

**T7 — Project Awareness**, sketched but **not declared**. No Charter amendment while
T6 is open.

The operator's four corrections to the sketch are recorded as planning material:
Project Mapper is an **observation/snapshot** layer and `attach` a **derived
awareness** layer — not two answers to one fact; target kinds share an awareness
**envelope and provenance contract**, not identical domain fields; coarse
signature-based staleness already exists and must not be regressed to honour a
tranche boundary; and awareness belongs to **instance identity**, not to an absolute
target path — which is precisely what T6's UUID makes possible.

T7 advances walk steps 6, 7, 8 and the awareness half of 13. It stops before target
mutation and before change-driven selective refresh.
