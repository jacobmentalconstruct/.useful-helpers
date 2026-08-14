# 0027 — T6 Parked, and the Development Mode Changes

- **Date:** 2026-08-14
- **Tranche:** T6 — Instance Identity and the Installation Core
- **Status:** **PARKED** (BCC §2.6 / §2.8 step 13). Operator approval granted 2026-08-14.
- **Declared in:** 0024, amended 0025, awaiting approval in 0026

---

## 1. T6's durable result

> One installed instance is structurally bound to one target, knows its identity, root
> and state, survives relocation and update, and supplies canonical context to the
> human, agent and tool runtime.

That is the whole of it, and it is enough. `src/core/instance.py` is the one authority
on what an installed instance *is*; `config`, `_toolkit`, `attach` and the installer
are its consumers. Four surfaces answered *"what is the sidecar"* at declaration; one
answers now.

**Deferred, and recorded rather than carried.** The payload is still defined by
subtracting exclusions from a source tree rather than by the positive install manifest
Charter §5.4 requires. The **canonical payload assembler** is assigned to
`P-install-packaging` in the Plan. It is explicitly **not** carried into T7 or T8; a
convergence tranche that quietly absorbed a distribution deliverable would be the
scope creep this phase exists to prevent.

Also carried, unchanged: E8 and E11 remain **NOT MET**. T6 closed the *install row* of
E8's phase matrix and nothing else.

---

## 2. Closeout verification

| | Linux (sandbox) | Windows |
| --- | --- | --- |
| `ruff check .` | clean | operator/CI |
| `smoke_test.py` | 2 errors, both `PermissionError: unlink` on the development mount — the environment constraint recorded in Charter §7.5, not a product defect | operator/CI (zero-skip authority) |
| `gates/run.py` t00–t06 | **all PASS** | operator/CI |
| discovery pass | run at 0026 | — |

**The two smoke errors are named, not waved away.** `test_c1_hands` and `test_c4_data`
both die at `Path.unlink()` inside `_artifacts/`. The development mount permits create,
write, overwrite and rename but denies delete. Windows is the authority for a zero-skip
run and always has been; this is why.

**Windows re-certification of the front door is the operator's step**, on
`.github/workflows/verify.yml`, against the launcher/app/installer changes now in the
tree. Approval for this closeout was granted conditional on it being green.

---

## 3. What the gates caught in this session's own work

Recorded because it is the mechanism working on the surface that defines the mechanism.

`gates/t05` failed **twice** within an hour of the convergence phase being written:

1. `CHARTER.md` declared `[OWNS: SIDECAR:PROTOTYPE-OBJECTIVE]`, an anchor absent from
   the gate's enumeration. *"A fact worth owning is worth enumerating, or the registry
   stops being a registry."* The anchor was added to `REQUIRED_ANCHORS` — the gate was
   asking for registration, not rejecting the fact.
2. `TRANCHE_PLAN.md` declared two ownership anchors of its own. The Plan owns
   sequencing; a Plan that declares ownership is the second normative surface
   `BCC-ONE-AUTHORITY` exists to prevent. Removed.

Neither would have been visible by reading. Both were found the first time the gate ran
after the edit.

---

## 4. The mode change

The `_theCELL` dogfood run (0026 follow-up, 2026-08-14) is the evidence. Five tool
calls produced a real orientation of an unfamiliar target: domain classification,
subsystem shape, entrypoints, symbol scale, hub modules, dependency structure,
database schemas, and an honest limits list. `symbol_graph refs` resolved inbound
edges to exact call sites. `edit` previewed a change and `apply:true` made it. The
ledger attributed it.

**Finding A holds: the existing toolbox can already understand and operate on a real
target.** What is missing is composition, compact synthesis, shared presentation, and
closing the loop that already has all its parts.

So the question the Plan answers changes:

| Until T6 | From T7 |
| --- | --- |
| *What subsystem should we design next?* | **What prevents the existing toolbox from behaving like one useful product?** |

Charter §1.3 now owns the prototype objective. `TRANCHE_PLAN.md` owns the convergence
rules (C1–C4), the T7/T8 sequence and the **prototype STOP**.

### One correction against the builder

The dogfood run's sharpest reported finding — *"`symbol_graph refs CellBackend` fails;
possibly a real capability gap"* — was **operator error by me**. The class is
`Backend`. I assembled `CellBackend` from the module name plus the project name,
queried a symbol that has never existed, and reported the tool's correct refusal as a
product defect. Querying `Backend` returns two disambiguated matches with exact line
ranges and resolved inbound edges.

Two rules come from that one mistake, and both are now binding:

- **C1 rule 1** — no capability gap is concluded without an end-to-end attempt first.
- **C3** — awareness carries the canonical machine handle beside the readable label,
  so the next call grounds itself in a deterministic identity instead of
  reconstructing a name from a sentence.

A tool that refuses a name the model invented is a tool working correctly.

---

## 5. Documents changed, and why

Only **active claims that would steer future development wrongly** were touched. No
journal was rewritten; no parked tranche's evidence was altered.

| Surface | Change |
| --- | --- |
| `CHARTER.md` §1.2 | the precept governs the sidecar's *footprint*, not the user's work — "never writes to the target" named as a misstatement |
| `CHARTER.md` §1.3 | **new.** The prototype objective, anchored `SIDECAR:PROTOTYPE-OBJECTIVE` |
| `CHARTER.md` §3.5/§3.6 | renumbered from a duplicated §3.1/§3.2; dispositions recorded — live channel BUILT (T3), cancellation BUILT (T4), marker resolution **superseded by T6**, One Surface and chains explicitly post-STOP |
| `CHARTER.md` §5.3 | `sidecar_install` disposed, not "scheduled for disposition" |
| `CHARTER.md` §7.5 | Windows no longer globally unverified; it is the primary CI job |
| `TRANCHE_PLAN.md` | header, scoreboard evidence (E1, E2, E3, E7, E8, E9, E13), the sequence table, and the backlog. **New:** the convergence phase (C1–C4), T7, T8, the prototype STOP. Former T7–T10 demoted to `P-` candidates, retained but unscheduled. The `lint` section's `PRIORITY` heading, which contradicted its own closing paragraph, corrected |
| `gates/t05_ownership_model.py` | `SIDECAR:PROTOTYPE-OBJECTIVE` enumerated |
| `README.md` | product objective stated; the write-nothing absolute corrected; identity-based binding described; `run.sh` added; `_docs/` → `docs/` |
| `AGENTS.md` | marker-resolution table **replaced** with instance identity; scope-is-not-rebinding; the write-boundary table; the canonical-handle rule; launcher front door |
| `docs/ARCHITECTURE.md` | §1 precept corrected; §4 retitled *runtime* roots and made to cite the Charter's ownership roots rather than compete with them; identity-based resolution described |
| `docs/ONBOARDING.md` | `_docs/` → `docs/`; launcher entrances |

**Not changed:** the BCC. It governs the builder, not the product's scope, and nothing
in it steered wrongly. The convergence rules are Plan-level and live there.

---

## 6. The mutation-signal census — asked and answered before designing

The operator required this before any stale-awareness work. Full results in the Plan's
T8 section; the conclusion is what matters:

Eight tools declare `writes: target`, and they report their affected paths in **eight
different shapes** — `path`, `results[].path`, `written[]` relative to `base`, `db`,
`venv`, nested `trail[].base` — while `project_run` reports **no path at all**, because
its scope is an arbitrary shell command. Normalising those would be exactly the bespoke
per-tool architecture the convergence rules forbid, and would still be blind to the one
tool with unbounded scope.

**The seam already computes the answer.** `invoke.py` holds `_target_manifest()` and
`_manifest_diff()`, and today runs them only for **Observe** tools — only for the tools
that must change nothing. Inverting that gate for governed Apply yields `changed_paths`
for every target writer, tool-agnostically, with no per-tool code.

`changed_paths` is therefore a **measurement**, and a tool's own `path` field is a
*claim* to be checked against it. The census's value was showing that trusting the
claims would have been the wrong design.

One defect fell out of it: **`patch` writes to a target path while declaring
`writes: toolkit`.** That is a hole in the precept guard's own gating, found by census
rather than by failure. Assigned to T8.

---

## 7. Next

**T7 — Shared Project Awareness Prototype**, sketched in the Plan, **not declared.**
Declaration follows the BCC loop as usual: gate first, discovery pass at close,
operator approval before parking.

No Charter amendment and no T8 work while T7 is open.
