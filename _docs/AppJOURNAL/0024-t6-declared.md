# 0024 — T6 Declared: Instance Identity and the Installation Core

- **Date:** 2026-08-11
- **Tranche:** T6 — Instance Identity and the Installation Core
- **Status:** **DECLARED. Gate written and failing — 7 fail, 0 pass.**
  Entry opened before implementation, per BCC §2.8 step 7.
- **Baseline:** 0023, verified on Windows and Linux.

---

## 1. The tranche (step 2)

**Outcome, one sentence.** One authoritative definition of what an installed instance
*is*, one implementation of how one is created, and a product installer that produces
an instance able to resolve its own target.

**Changed surfaces.** `src/core/instance.py` (new), `packaging/installer/install.py`,
`src/core/config.py`, `tools/_toolkit.py`, `tools/sidecar_install/` (retired from the
registry), `_harness/harness.py`, `gates/t06_instance_identity.py`.

---

## 2. Current state, as measured (step 3)

### 2.1 Three implementations, and the shipping one is broken

| Path | Kind | Writes `.suite_sidecar`? |
| --- | --- | --- |
| `packaging/installer/install.py` | **the product's setup application** | **NO** |
| `tools/sidecar_install/cli.py:133` | registered runtime tool | yes |
| `_harness/harness.py:447` | direct `copytree`, marker by hand | yes |

`src/core/config.py:72` recognises an installed instance solely by that marker.

**So the product's own install entrance produces an instance with no target.** Every
green install this project has recorded came from a development path. The shipping
path has never been exercised by any check — which is why T6's gate installs through
it and nothing else.

### 2.2 Identity is a name guessed from an environment variable

```python
tools/_toolkit.py:170
def toolkit_home_names() -> set[str]:
    names = {".useful-helpers"}
    home = os.environ.get("SUITE_HOME")
    if home: names.add(Path(home).name)
```

A **name set**, seeded with a hardcoded default, derived from an env var the seam
exports. Reached outside the seam, or installed under another folder name, and a
sidecar can treat its own home as target content — reading itself as the project.

Charter §5.5 requires durable identity from the instance's actual location plus a
recorded **relative** relationship to its target.

### 2.3 Four surfaces answer "what is the sidecar"

`config.py` (marker), `_toolkit.py` (env + name), `sidecar_install` (`_DEFAULT_FOLDER`),
`install.py` (`SIDECAR_DIR`). Four hand-maintained answers to one fact —
`BCC-ONE-AUTHORITY`, and the sixth instance recorded in this project.

---

## 3. What this tranche is not for (step 4)

- **No positive payload manifest, no payload assembler.** Payload definition and
  instance definition are separate facts that meet at the installation core
  (0021 §4). T6 consumes today's transitional fixture producer.
- **No harness split.** The harness becomes a *client* of the core here; extracting
  its verification primitives is later.
- **No corpus externalisation. No contract seed generation. No lint tranche.**
- **No One Surface work** — but T6 is what makes it declarable.

---

## 4. Completion condition (step 5)

`gates/t06_instance_identity.py` — **failing now**, 7 assertions, 0 passing:

```
[FAIL] an instance definition module exists
[FAIL] the instance module exposes create / resolve / InstanceContext
[FAIL] only the instance core creates an instance
[FAIL] the runtime no longer registers an installer of sidecars
[FAIL] the product installer completes
=> t06_instance_identity BLOCKED
```

**Rule 8, as generalised at T5:** the real consumer entrance for an installed
instance is the **setup application**. The gate installs via
`packaging/installer/install.py` and then interrogates the result — it never uses
`sidecar_install`. That choice is the tranche in miniature.

**Three hazards encoded as assertions:**

**H1 — the third implementation.** Unifying the two paths one remembers and leaving
the third would look finished. Asserted by **census** over every `.py` in the tree,
not by naming the two.

**H2 — identity that breaks when the target moves.** The tempting fix writes an
absolute path at install time. The gate **actually moves the target** and requires
resolution to survive.

**H3 — the namespace still guessed by name.** The gate installs under `.uh-t6`,
deliberately not the default, because the default is the one value that can be
hardcoded and still appear to work.

**Stop conditions.** Stop and report if: making `install.py` produce a resolvable
instance requires deciding what the instance manifest *contains* beyond identity and
target relationship — that is Charter work, not implementation; or if retiring
`sidecar_install` breaks a capability with no replacement, which would mean the
Charter's ownership rule needs amending before code follows it.

---

## 5. The plan (step 6)

1. **`src/core/instance.py`** — `InstanceContext` (identity, instance root, target
   root, state root, schema version) with `create()` and `resolve()`. Identity from
   structural location plus a relative relationship; a UUID for continuity across
   moves, never an absolute path.
2. **`install.py` consumes the core.** The setup application stops copying files and
   hoping; it calls `create()`.
3. **`config.py` consumes the core.** `_resolve_project_root`'s marker branch becomes
   `instance.resolve()`. The four evidence cases stay — the third gains a real
   implementation.
4. **`_toolkit.py` consumes the core.** `toolkit_home_names()` is replaced by the
   resolved instance's own root. No tool rediscovers which directory is the sidecar.
5. **Retire `tools/sidecar_install` from the registry**, preserving it as the
   transitional fixture producer T1 still depends on until the payload tranche.
6. **The harness consumes the core** rather than reimplementing installation.
7. **Consolidate** (step 9): ruff, dead code, no second answer to "what is the
   sidecar".
8. **Verify** (step 10): the T6 gate, the full suite from a fresh clone with no
   environment variables, **both platforms**, and the discovery pass — including
   `SUITE_DISABLE_CONTAINMENT=1` since `proctree` is adjacent.
9. **Resolve staleness** (step 15): `docs/ARCHITECTURE.md` §4 "the four roots" and
   `AGENTS.md`'s four resolution cases both describe marker-based resolution.

---

## 6. Known risks

- **`config.py` is load-bearing for every entrance.** A wrong move here breaks all
  95 tools at once. Mitigated by keeping the four-case structure and replacing only
  case 3's implementation.
- **T1 still depends on `sidecar_install`** to materialise its payload fixture.
  Retiring it from the *registry* must not delete it. Declared in `t01`'s
  `KNOWN_LIMITATIONS` already.
- **Windows install semantics are unexercised.** The gate's central assertions have
  never run on the shipping path on either platform. Expect surprises; that is the
  point.

---

## 7. Next

Implementation — plan steps 1 through 6, then consolidate and verify. Returns at BCC
step 12 for operator review, and is not parked before that.

**Then One Surface is reassessed immediately**, per the commitment recorded in 0020,
0021 and the plan.
