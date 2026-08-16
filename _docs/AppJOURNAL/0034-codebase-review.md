# 0034 — Codebase Review: Two Silent Degradations in the Safety Path

- **Date:** 2026-08-16
- **Status:** review complete. **Two defects repaired**, one documentation invariant
  corrected, one regression added and mutation-tested, four items to backlog.
- **Constraint honoured:** T7 is open, so this repaired **defects** and refactored
  **nothing**. Charter §4 forbids polish; both code repairs are invisibility fixes with
  no behaviour change.

---

## 1. Method

**Dogfooded.** The toolkit's own analysers, pointed at the toolkit, through the seam:
`complexity_score`, `dead_code`, `blocking_call_scan`, `secret_audit`,
`domain_boundary_audit`, `import_graph`. Plus targeted pattern scans for the classic
Python defect families, and boundary checks derived from the architecture's own stated
rules.

Every finding was **verified by reading the code** before being called a defect.
`AGENTS.md` warns that these tools have flagged live code as dead, and that warning
earned itself again — see §5.

---

## 2. Defect 1 — a broken governance ceiling failed **open and invisibly**

`src/core/policy.py`. The highest-stakes instance of this project's signature failure:
**a wrong state indistinguishable from a right one.**

```python
def _config_ceiling(paths) -> str | None:
    try:
        ...
        if m in _RANK:
            return m
    except Exception:
        pass          # <- and an out-of-range value fell through here too
    return None
```

`None` → `effective_ceiling` falls back to `DEFAULT_CEILING = "Apply"`, the **most
permissive** setting.

So an operator who clamps a sensitive target to `Observe` and

- mistypes the JSON, or
- writes `"observe"` instead of `"Observe"`,

gets **full Apply authority and no indication whatever.** Two distinct silent paths,
one outcome: a governance control that is not in force and looks exactly like one that
is. The module docstring even says *"a broken config never blocks"* — true, and
dangerous when the config's whole purpose is to block.

**Repaired by making the degradation audible, not by changing the posture.** Malformed
JSON and out-of-range values each warn at `WARNING`, naming the file, the reason, and
the fact that no ceiling is in force. The fail-open default is **unchanged** — a
security posture is the operator's decision, not a review's, and it is recorded in the
backlog as a question rather than answered here.

### Verified, in both directions

```text
1. no config            -> Apply,   silent    (correct: no ceiling was asked for)
2. malformed JSON       -> Apply,   WARNS
3. "observe" (typo)     -> Apply,   WARNS  "not one of ['Observe','Sandbox','Apply']"
4. valid "Observe"      -> Observe, SILENT, and Apply is refused: (False, 'Observe')
```

Case 4 is the one that matters: without it, the warning could be made unconditional and
still pass cases 2 and 3 while meaning nothing.

### A regression that did not exist

**No test covered a malformed `governance.json`.** One added, and
**mutation-tested**: green with the fix, and red against the restored pre-fix function —

```text
AssertionError: no logs of level WARNING or higher triggered on suite.core.policy
```

It also asserts the silent cases stay silent, so it cannot be satisfied by logging on
every read.

*The test needed one repair of its own:* it originally called `cfg.unlink()`, which
fails on the development mount and would have made the assertion fail for a reason
unrelated to governance. It now uses a separate empty root. **A test must not need a
capability it is not testing.**

---

## 3. Defect 2 — the precept guard's kill-switch was silent

`src/core/invoke.py`. Charter §7.3 recorded this on 2026-08-06 —
*"`SUITE_STRICT_OBSERVE=0` disables the guard entirely and silently — verified, the same
fixture returned `ok: true`"* — and it was **still silent** ten tranches later.

The guard is what catches an Observe tool writing to the target, and a precept violation
is a **damage event**: the write lands, then gets reported. So a run with the detector
off can do real harm and leave no trace that detection was even attempted.

Now warns **once per process** — once, not per dispatch, because a warning on every
invocation trains the reader to ignore it. Verified: silent by default, exactly one
warning when disabled.

---

## 4. Domain boundary — a documented invariant the code does not keep

`docs/ARCHITECTURE.md` §2 asserted:

> Tools never import each other.

**It is not true.** `tools/dev_server_manager/cli.py` imports
`tools.command_profile.cli` directly — and says so openly in its own `DEPENDS ON`
header, so the code is deliberate and the *documentation* is the defect. That is E10:
a documented claim with nothing behind it.

Three sanctioned routes exist and this uses none of them: `_toolkit`, a `*_shared`
module, or `seam_call` (which `delegate`, `plan` and `genesis` all use). The direct
import couples to another tool's implementation, and the call produces **no ledger
entry** — a capability exercised without attribution.

**Corrected the documentation, not the code.** The paragraph now states the rule as it
holds, names the exception, and records the design decision — route through `seam_call`,
or extract a shared module — as a backlog item rather than settling it silently
mid-tranche.

One dependency runs the other way and is correct: `tools/vendor_export` imports
`src.core.payload` because the ship manifest is the **single authority** on what ships
(T1), and a consumer that restated it would be the second copy `BCC-ONE-AUTHORITY`
forbids. Now documented rather than merely tolerated.

---

## 5. My own gate broke another gate, and the census caught it

`gates/t07_shared_awareness.py`, written hours earlier, contained a helper that read
`instance.json` and parsed the uuid. `gates/t06` failed immediately:

> *only the instance core knows the identity format — active product code still defines
> or interprets identity: `['gates/t07_shared_awareness.py']`*

**The fix was not to add t07 to the census exclusion list.** Excluding a surface so a
census stops seeing it is exactly how the harness once vanished from the identity
census — it disappeared *because it was excluded*, not because it stopped manufacturing
identity (0026, defect 7). A gate that blinds the check it trips is worth less than no
gate.

t07 now **consumes the identity API** in a subprocess against the installed instance,
which is precisely what t06's sibling assertion asks of a verifier: *a test may inspect
the persisted representation; it may not become a second producer of it.* t06 is back to
27/27.

---

## 6. What came back clean

Recorded because a review that only lists problems overstates them.

| Check | Result |
| --- | --- |
| bare `except:` | none in product source |
| mutable default arguments | none |
| `open()` outside a context manager | none |
| unparseable modules | none in product or factory source |
| `blocking_call_scan` on `src/` | **0 findings**, 7 informational |
| `shell=True` | only `project_run`, where it is the documented purpose and governed |
| seam imports tool code | none — `src/core/` imports no tool |
| `secret_audit` on product source | one hit, `web_search` reading an env var. False positive |
| `domain_boundary_audit` | 0 crossings; no layering policy declared, so reported as neutral facts |

**`dead_code` on `src/` returned 20 candidates. Nineteen are false positives** —
`materialise`, `record_decision`, `cursor`, `poll` and the rest are consumed by gates,
tests and the UI, which the scan did not traverse. Exactly one, `cartridge_conflicts`,
is referenced only in its own defining file: built in T5 for a tranche
(`P-install-packaging`) that has not run. **Mild pre-built bloat, recorded not
deleted** — removing work already done for a scheduled tranche is not a review's call.

This is the AGENTS.md warning demonstrated: *low confidence means a lead, not a
verdict.* A 95% false-positive rate on this codebase is the honest number.

---

## 7. Structure — measured, and deliberately left alone

138 modules, 18,108 lines of product source. **Two modules over 600 lines.**

| lines | module | |
| --- | --- | --- |
| 1051 | `tools/attach/cli.py` | already sized by C1b — T7 discharges **one** responsibility, not a rewrite |
| 851 | `tools/bd_graph_shared.py` | shared engine, single domain |
| 449 | `src/core/invoke.py` | the seam. `_dispatch` scores 57 (106 lines, complexity 25) |

**No god objects found.** The largest classes are UI views; `src/core` holds 4 classes
across 27 files. `invoke._dispatch`'s complexity is 8 return paths in one place, which
is its stated design — *"all the failure/success return paths live here"* — and
splitting it would scatter the seam's failure handling, not concentrate it.

**Nothing here was restructured.** T7 is open; C1b already decided how much of `attach`
moves and when. Recording a measurement is not a licence to act on it mid-tranche.

---

## 8. To the backlog

| Item | Why it is not fixed here |
| --- | --- |
| **Should the governance ceiling fail open or closed?** Currently open-and-audible | a security posture is the operator's decision |
| **`dev_server_manager` → `command_profile` direct import** — route via `seam_call`, or extract `command_profile_shared`? | changes behaviour (a subprocess, ledger entries) in a tool unrelated to T7 |
| **`cartridge_conflicts` is unreferenced** | built for `P-install-packaging`; delete when that tranche decides |
| **No layering policy declared** — `domain_boundary_audit` can only report neutral facts | a `.uh-policy.json` would turn crossings into pass/fail. Real value, but it is new architecture |

---

## 9. Verification

From a **clean clone**, not the working tree:

```text
ruff check .        clean
smoke_test.py       85 tests, OK (7 skipped)   <- 84 before; the new regression is the 85th
gates t00-t05       PASS
gates t06           PASS (27)
gates t07           RED as declared (3 pass, 30 fail) - T7 is not implemented
```

Errors on the development mount — `test_c1_hands`, `test_c4_data`,
`test_domain_boundary_policy_profiles`, `test_e4_recovery_lifecycle`,
`test_e5_formation_provenance` — are the constraints in Charter §7.5 (unlink denial,
SQLite-over-mount `disk I/O error`). They reproduce with and without these changes and
vanish on real disk. **Named rather than folded away.**
