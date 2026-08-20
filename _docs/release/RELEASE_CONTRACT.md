# Closure Gate 2 — Release Certification: the contract

- **Declared:** 2026-08-20
- **Preceded by:** Closure gate 1 (parity) certified at `3b2ecdb` (0042)
- **Verifier:** `_docs/release/release_check.py`
- **Not a tranche.** No T9. This is the second and last closure gate.

---

## The question, as narrowly as it can be put

> **Can this repository become an artifact another machine installs and uses without the
> development checkout?**

Shippable does **not** mean signed, MSI-packaged, auto-updating or app-store polished. It
means a genuine distributable product rather than *"run this from my dev checkout."*

---

## Use the existing mechanism first

`payload.materialise()` → `packaging/installer/install.py` → `.useful-helpers/run.{bat,sh}`.

**A new assembler becomes permitted only if this proof demonstrates a concrete omission,
leak or reproducibility failure that the existing owner cannot satisfy cleanly.** Not
because an earlier plan imagined one. `materialise` says of itself that it is not the
canonical positive assembler; that is a statement about its design, not a licence to
replace it before it has failed at something.

---

## C4 coverage is part of Release, not a side obligation

*Operator ruling, 2026-08-20.* Release cannot PASS until all five run:

| | required |
| --- | --- |
| **A** | a nontrivial software target exercised |
| **B** | a mixed records / data / documents target exercised |
| **C** | an empty / nascent target exercised |
| **composite oracle** | executed, and composition **actually scored and passing** |
| **bait oracle** | executed, and truthfulness discrimination **actually scored and passing** |

On A/B/C a missing oracle stays explicitly **`UNSCORED`, never `PASS`**. The oracle
controls supply known-answer correctness beside the ordinary walk. **A/B/C are not seeded
with bait to obtain scores** — doing so would destroy the reason they exist. Real targets
prove usefulness under uncertainty; controlled targets prove correctness where truth is
knowable.

---

## The walk

### 1. Clean-clone manufacture

From a **clean clone** of the certified source, using no file or state from the
development working tree:

```text
clean clone  ->  payload.materialise()  ->  release artifact
```

### 2. Inspect the artifact itself

Both directions. **"Forbidden names not found" is not sufficient on its own** — an empty
directory would pass that test. Required launch, runtime and product material must be
proven present.

**Forbidden:** parts/reference corpus · `_harness` · `_docs/AppJOURNAL` and development
history · certification evidence · accumulated `_state` · `_projectmapper` generated
inspection state · source git history · factory-only tranche material (`.bcc`, `gates`) ·
build-machine absolute paths.

**Required:** the launcher, the seam, the registry, the tool bodies the registry names,
and the installer's own identity module.

### 3. Fresh Windows and fresh Linux

The release artifact — **not the development repository** — is the only product input.
On each platform: choose a target → run the real Setup → one `.useful-helpers/` instance →
execute the documented launcher **from the installed product** → correct instance/target
identity → `attach` → the real MCP entrance with an external client → retained parity
products **from the installed artifact** → the T8 loop:

```text
awareness X -> drill/impact -> preview/diff -> approval -> Apply
            -> verification where available -> X stale -> refresh -> Y
```

→ update preserves instance UUID and product-owned state → target-owned content stays
correctly separate.

### 4. Removal test — on its own target

On a target where **no deliberate Apply has occurred**: capture content before install →
install and use the sidecar without target mutation → remove `.useful-helpers/` → prove
target-owned content is **byte-for-byte unchanged**.

Deliberately **not** the T8 target: T8 changes target content on purpose, and those
changes are supposed to persist. Running both on one target would make the removal proof
meaningless.

---

## Repair rule

Repair **only** failures this verifier demonstrates, at the smallest existing owner.

The standing debts are **not** Release work unless Release makes one load-bearing: the
26-tool manifest-truth sweep, a generic `tool_health` threshold, `secret_audit` exceeding
120s on this repository, `domain_boundary_audit` without a policy, ProjectMapper
dot-directory semantics.

---

## Stop condition

The **same** release artifact passes the complete required acceptance on fresh Windows
**and** fresh Linux. Then the release certification and the STOP record are written.

No T9. No post-release architecture cleanup inside this project. No scaffold-kit
extraction. No knowledge-graph integration.
