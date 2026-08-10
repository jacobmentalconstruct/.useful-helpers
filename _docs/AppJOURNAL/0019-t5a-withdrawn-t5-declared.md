# 0019 — T5a Withdrawn; T5 Declared: Ownership and Distribution Model

- **Date:** 2026-08-09
- **Tranche:** T5 — Ownership and Distribution Model
- **Status:** **DECLARED. Gate written and failing — 26 fail, 4 pass.**
  Entry opened before implementation, per BCC §2.8 step 7.
- **Supersedes:** the T5a declaration in 0017.

---

## 1. Why T5a was withdrawn

The operator's deployment-topology correction established that what a user receives
is an **OS-specific setup application** carrying a **canonical payload**, which
installs **one instance** into **one target**. There is no central sidecar that opens
many projects.

T5a was declared against a model where the installed runtime and the setup
application were the same product. Two of its commitments are wrong under the
corrected topology:

- it named `installer_view` as part of the regression set for the runtime shell —
  setup UI belongs to the setup deliverable
- it inherited T5b's *"every registered tool reachable from the shell"*, which with
  `sidecar_install` registered would **force the installed sidecar to expose
  "install another sidecar" as runtime functionality**

T5a was declared, never implemented, never parked. This is a **withdrawal**, not a
§5.1 reopening.

**Its gate is quarantined, not deleted.** `gates/_deferred/t05a_observe_select.py.deferred`
with a README recording which assertions survive and which encode the superseded
architecture. Left in active discovery it would be competing project state — a plan
saying *withdrawn* while the runner still executes the gate.

---

## 2. Current state, as measured (step 3)

Verified in a fresh clone. Every operator claim checked before acceptance.

### 2.1 Three installation implementations, and only one is the product's

| Path | Kind | Creates `.suite_sidecar`? |
| --- | --- | --- |
| `packaging/installer/install.py` | standalone setup application — **the product entrance** | **NO** |
| `tools/sidecar_install/cli.py` | registered runtime tool that installs another sidecar | yes (`:133`) |
| `_harness/harness.py` | direct `copytree`, plus a mode staging and calling the tool | yes, manually (`:447`) |

### 2.2 The severe consequence

`src/core/config.py:72` recognises an installed instance by the `.suite_sidecar`
marker and binds the work target to its parent. `install.py:134` copies the payload
and writes no marker — confirmed by reading the whole `install()` body.

**The actual product installer produces an instance that cannot resolve its own
target.** The two development paths manufacture a working instance; the shipping one
does not. Every green install result to date came from a path that is not the
product's.

This is the strongest possible argument for the operator's ordering: an installation
core must exist before the harness is split, because the harness is currently
compensating for the real installer's gap.

### 2.3 `installer_view` is independently stale

It renders checkboxes for *"Host AGENTS.md pointer (if absent)"* and *"Add to host
`.gitignore` (git repos)"*, passes `host_agents`/`gitignore`, and reads back
`wrote_host_agents`/`gitignore_updated`. `sidecar_install`'s schema is
`{confirm, dry_run, folder, overwrite, target, update}` — none of those exist.

The tool removed the behaviour because the precept forbids it. **The GUI still
offers the operator two precept-violating options that silently do nothing.**

### 2.4 The reserved namespace has no durable identity

```python
def toolkit_home_names() -> set[str]:
    names = {".useful-helpers"}
    home = os.environ.get("SUITE_HOME")
    if home: names.add(Path(home).name)
```

Name-based, environment-derived, hardcoded fallback, not recorded in the instance.
Under a model where the reserved namespace is the load-bearing concept, this cannot
stand. The operator's direction — structural location plus durable instance identity
plus a *relative* target relationship, not a frozen absolute path — is recorded as
the constraint on the derived work, not built here.

### 2.5 Two meanings of "sidecar"

`SIDECAR_ROOT` means `.bcc/` in the contract and `<target>/.useful-helpers/` in
architecture prose. Different abstractions, one word.

### 2.6 Authority surfaces describing a project that no longer exists

```
CHARTER.md   Status: **DRAFT for operator agreement.** Nothing is built against this yet.
TRANCHE_PLAN Status: **DRAFT for operator agreement.**
```

T1–T4 are implemented; the scoreboard marks five conditions met.

---

## 3. The governance hole this exposed

T1 proved **self-hosting**: generation 1 installs generation 2, counts equal. Valid
under the architecture in force when it closed. `payload.py` still justifies shipping
itself on that premise.

The corrected chain is `source → payload → setup → instance`, not
`instance → instance`. So an invariant proven by a **parked** tranche is now
intentionally unwanted — and the protocol has no mechanism for that. Cumulative
gates (rule 6) say every prior gate must still pass; nothing says what happens when
the operator retires a premise.

**T5 defines that mechanism narrowly.** No silent disabling, no rewriting the old
journal, no old gate continuing to claim authority after its premise is retired.

---

## 4. The tranche (step 2)

**Outcome.** One authority per normative fact, and a stated deployment topology —
so that every later packaging, installation and boundary decision is derived from a
single owned statement rather than argued case by case.

**Changed surfaces.** `.bcc/BUILDER-CONSTRAINT-CONTRACT.md` (the general rule),
`.bcc/CHARTER.md` (§5 becomes the anchored model), `.bcc/TRANCHE_PROTOCOL.md`
(supersession), `.bcc/TRANCHE_PLAN.md` (renumbering, withdrawal, scoreboard,
status header), `_docs/AppJOURNAL/0018-project-audit.md` (reclassification),
`gates/t05_ownership_model.py`.

---

## 5. What this tranche is not for (step 4)

- **No product module moves.** Not one file relocated.
- **No payload builder.** The positive install manifest is *designed* here only in
  so far as the Charter states who owns membership; it is *implemented* later.
- **No harness split, no gates split, no corpus move.**
- **No installation core.** Named as the derived work; not written.
- **No `InstanceContext`.** Its constraints are recorded; its code is not.
- **No fifth authority document.** The Charter already owns product architecture.
- **No One Surface work.**

---

## 6. Completion condition (step 5)

`gates/t05_ownership_model.py` — written first, **failing now**:

```
26 [FAIL] · 4 [PASS] · => t05_ownership_model BLOCKED
```

The four passes are things already true: no fifth `.bcc` document, `STATE_ROOT`
already exists, and the two T5a-withdrawal assertions satisfied above.

**A first draft of this gate passed three checks it should not have.** "Permits
verifiers" matched the word *verification* 300 lines away in an unrelated rule;
"defines supersession" matched *superseded* inside the staleness criterion; "T1 self-
hosting superseded" matched *Superseded* in T0's prose. All three now scope to the
rule's own anchored section or require an explicit marker. **A check that passes
before the work exists cannot detect the work being done.**

**The operator's amendment is encoded at check 4.** Not *"no document states a
boundary rule the model does not own"* — the BCC legitimately owns generic builder
boundaries while the Charter owns product topology, at the same time. The invariant
is **no two live normative surfaces claim ownership of the same fact.**

**Rule 8, for a definitional tranche.** There is no runtime entrance to a definition.
The equivalent is the **entering agent's read path**: the anchors an agent is told to
resolve must actually resolve, and the facts must be reachable from the documented
entry point rather than merely present somewhere in the tree.

**Stop conditions.** Stop and report if: stating the model requires a decision the
operator has not made (the model is recorded, not invented); or the reclassification
of 0018 reveals a finding that fits no domain, which would mean the six domains are
wrong and the model needs amending before it is written down.

---

## 7. The plan (step 6)

1. **BCC** — the scoped one-normative-authority rule, at its own anchor
   `BCC-ONE-AUTHORITY`, permitting consumers, generated surfaces and verifiers.
2. **Charter §5** — evolve the zone table into the anchored Ownership and
   Distribution Model: six domains, six `SIDECAR:` anchors, the four distinct root
   terms, the topology end to end, the installed runtime explicitly not an installer
   of sidecars, `packaging/installer` named as the product entrance.
3. **Charter §3** — restate **E8** as a phase × authority matrix and **E11** as
   development blankness. Record the governance-cartridge invariant: enabling it does
   not expand sidecar ownership into target-owned content.
4. **Protocol** — the supersession mechanism as its own numbered section.
5. **Plan** — mark T1's self-hosting proof `SUPERSEDED` with its replacement; record
   T5a withdrawn; renumber the undeclared sequence; correct the scoreboard and the
   status headers.
6. **Reclassify 0018** on both axes — ownership domain × disposition, plus authority
   role where useful.
7. **Record nonconformities** for derived disposition: `tools/sidecar_install` as
   runtime capability, `installer_view`'s dead precept-violating options, the
   harness's own install implementation, `install.py`'s missing marker.
8. **Consolidate**, then **verify**: the T5 gate, the full suite from a fresh clone
   with no environment variables, and the discovery pass.
9. **Derive** the next implementation tranche from the corrected inventory — and
   **reassess One Surface immediately after it**, per operator instruction.

---

## 8. Renumbering

T5 is the Ownership and Distribution Model. Everything after it is **undeclared and
provisional** until T5's reclassification establishes the dependency order. The
operator's expectation — recorded, not committed — is that the first derived
implementation tranche centres on some combination of canonical `InstanceContext`,
one installation core, the positive payload manifest, and retiring sidecar
self-installation from the runtime.

One Surface returns after that, knowing what it is: **the operational surface of one
already-installed sidecar working on one bound target.**

---

## 9. Known risks

- **T5 is prose, and prose gates are weak.** Every assertion is a text search.
  Mitigated by anchoring and by scoping searches to their own sections — the three
  false passes above are exactly this risk, caught before declaration rather than
  after.
- **The six domains may not partition cleanly.** That is a stop condition, not a
  thing to force.
- **Momentum.** This is the second consecutive tranche producing no visible product.
  The operator has already ruled: derive one foundational implementation tranche,
  then reassess One Surface immediately.
