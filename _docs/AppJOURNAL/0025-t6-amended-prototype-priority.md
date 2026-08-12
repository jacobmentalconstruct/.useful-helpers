# 0025 — T6 Amended; Near-Term Priority Reset to the Prototype Loop

- **Date:** 2026-08-11
- **Amends:** 0024 (T6 declaration), before implementation
- **Authority:** operator direction, 2026-08-11

---

## 1. The reset

> The danger is no longer "there is no architecture." The danger now is that we
> continue perfecting the substrate while the product-level loop remains incomplete.
> The project has enough organs. Now make it into the animal.

Recorded as **Charter §3.3 — the prototype acceptance walk**: fifteen steps a new
user must be able to take. E1–E13 are the invariants; §3.3 is the experience they
exist to make possible. **Every tranche now states which of the fifteen becomes
materially more true when it parks.**

Placed in the Charter because it is product topology, and added as a section under
end-state conditions rather than a new owned fact — so `t05`'s ownership registry is
untouched and still passes.

**Near-term sequence, agreed:** finish T6 → **Project Awareness** → **Operate with
awareness** → One Surface → canonical payload and lifecycle hardening.

**One Surface follows awareness, not identity.** Removing the installer coupling
makes it *declarable*; it should not be *built* until the panels have real APIs
beneath them, or a second generation of temporary architecture gets encoded into
Tkinter.

---

## 2. What T6 advances

Walk steps **3, 5, 13, 14** — install into any chosen folder; the sidecar identifies
itself and its target; restarting destroys neither identity nor durable state; moving
target and sidecar together does not break the relationship.

It does **not** advance 6, 7, 8, 10 or 12. Those are the awareness and operation
tranches, and T6 is deliberately the smallest complete vertical slice beneath them.

---

## 3. Four corrections to 0024

### 3.1 No `--folder`, and the reason matters

0024's plan added a `--folder` option to the installer so the gate could install
under a non-default name and prove identity is not the basename.

**That would have created an unsupported "custom sidecar folder" product contract to
satisfy a test.** The operator's alternative proves the property more directly:
install canonically, then **rename the instance and move the target**, strip every
environment hint, and require structural resolution to survive.

> The gate should test the architecture we want, not force the architecture to grow
> around the gate.

I had it backwards, and would have shipped a public option nobody asked for.

### 3.2 The payload is a fixture, and the circularity is resolved

0024 deferred the payload build out of T6 and then required an installer that needs a
payload — a circular dependency in my own plan, found by inspection rather than by
running it.

`install.py` already accepts `--payload <dir>`. The gate materialises a payload from
today's manifest authority and hands it over. **No architectural authority is
conferred on the legacy producer**; the future pipeline stays `source factory →
canonical assembler → payload → setup application → instance`, and the canonical
payload remains target-neutral. Installation is what binds payload + target into an
instance.

### 3.3 The census was half-blind

0024 censused sites that **write** identity. `suite_home()` — env-or-cwd — writes
nothing, is used far more widely, and is the other half of the same guess. I could
have fixed `toolkit_home_names()`, passed the census, and left the defect alive.

Now both directions, with the operator's distinction encoded:

> Passing a resolved `INSTANCE_ROOT` to a subprocess through `SUITE_HOME` is
> **transport**. A subprocess deciding "maybe `SUITE_HOME`, maybe cwd, maybe the
> folder named `.useful-helpers`" is **inference**.
>
> One component resolves identity. Other components consume resolved identity.

### 3.4 Retirement must be complete, not cosmetic

Not just the tool manifest: CLI routes, the GUI installer view, probes, run scripts,
tests, and T1's fixture generation. Censused as a set, over **code** rather than
prose — an accurate comment recording that a runtime installer once existed is
history, and a gate demanding its deletion would be the §3.1 mistake again.

**Also added:** update must preserve the instance UUID (a wipe-and-recopy update
mints a new identity silently, orphaning every durable record keyed to the old one);
malformed identity must fail loudly rather than falling back to a plausible guess.

**Legacy marker:** treated as a migration question, not dual authority. First
establish whether `.suite_sidecar` instances are a real supported population or only
development fixtures. If fixtures — migrate and delete the old interpretation. The
destination is **one** identity mechanism either way.

---

## 4. What the amended gate found, live

It now runs end to end, and demonstrates the central finding rather than asserting it
from reading:

```
[PASS] a payload fixture can be materialised for the installer
[PASS] the product installer completes            rc=0
[FAIL] the installed instance resolves its own target
```

**The installer works. It produces an instance with no target.**

And both censuses found roughly three times the surface I would have repaired:

```
inference sites (8):  tests/test_smoke.py · tools/_toolkit.py · tools/attach/cli.py
                      tools/code_intel_shared.py · tools/file_tree/cli.py
                      tools/glob/cli.py · tools/repo_search/cli.py · tools/report/cli.py

install entrances (9): _harness/harness.py · src/app.py · src/core/payload.py
                       src/ui/app_ui.py · src/ui/installer_view.py
                       tests/test_smoke.py · tools/genesis/cli.py
                       tools/scaffold_project/cli.py · tools/sidecar_install/cli.py
```

I had named **three** of those nine, and **one** of those eight. `attach` — the
tool the operator wants to become the agent's front door to project awareness — is
among the eight guessing its own location.

---

## 5. Standing note

Two corrections in this entry are the same mistake in opposite directions: **adding
product surface to satisfy a check**, and **writing a check narrow enough to be
satisfied without fixing the defect**. Both produce a green gate over an unfixed
system.

The test is the one Charter §3.3 now supplies: *which of the fifteen steps becomes
materially more true?* A `--folder` option makes none of them truer. A census that
finds one site of eight makes step 5 look true while it is not.

---

## 6. Next

Implement T6, plan steps 1–6 as amended, then consolidate and verify on **both
platforms** — installation is the most platform-divergent code in the product, and
Linux green proves only Linux. Hard stop at BCC step 12.

**Then reassess against the prototype loop before touching more infrastructure**, and
expect the next objective to be whole-target awareness built from the mapper, attach
and introspection machinery that already exists.
