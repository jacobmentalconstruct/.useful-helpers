# 0028 — T6 Reopened: Two Updater Correctness Defects

- **Date:** 2026-08-14
- **Tranche:** T6 — Instance Identity and the Installation Core
- **Status:** **REOPENED** (protocol §5.2). Parked in 0027 the same day; that park was
  premature and 0027 is **not** amended.
- **Justification class:** correctness **and** data-loss. Both are permitted grounds.

---

## 1. Why this entry exists rather than an edit to 0027

0027 recorded T6 parked and the mode change to convergence. Evidence found **after**
it was written shows T6's own outcome claim is not yet true:

> "…survives relocation **and update**…"

The update path does not reliably preserve identity, and does not reliably preserve
the memory it promises to preserve. **The claim outran the mechanism**, which is
precisely the failure class this project keeps recording, and this time it is in the
tranche whose subject *is* identity continuity.

Protocol §5.1 governs the shape of the correction: **historical evidence is
immutable.** 0027 stands unedited. It was true as an account of what was believed at
the time it was written, and rewriting it would destroy the only record that the park
happened and was wrong. This entry supersedes its *status*, not its text.

The reopening is **bounded to these two defects.** Nothing else in T6 is reopened. No
new scope enters. The convergence phase, the T7/T8 sequence and the prototype STOP
adopted in 0027 are unaffected — T7 remains **sketched, not declared**.

---

## 2. Defect 1 — a corrupt manifest silently mints a new identity

`packaging/installer/install.py`:

```python
def _read_identity(dest: Path) -> "str | None":
    """The existing UUID, or None. Never invents one."""
    try:
        return _instance_module(dest).read_identity(dest)
    except Exception:
        return None
```

…consumed by:

```python
carried_identity = None
if mode == "update" and exists:
    carried_identity = _read_identity(dest)
...
ctx = _instance_module(dest).create(dest, target, identity=carried_identity)
```

`instance.read_identity()` is written to **raise** `InstanceError` when a manifest is
present but broken. Its module docstring names the reason in as many words:

> **ABSENT IS NOT MALFORMED.** … Falling through from corrupt canonical identity into
> a legacy heuristic is how a new mechanism fails while an old one masks it.

The installer catches `Exception` and returns `None`. `create()` then reads `None` as
*"no identity supplied"* and mints a fresh UUID. **The authority's loud failure is
converted into a silent success by its own caller.**

Consequence: an update over a corrupt or partially-written manifest reports
`ok: true`, and every durable record keyed to the old UUID is orphaned — silently, on
the first upgrade. That is the exact scenario `instance.py` was written to prevent.

The docstring `"""The existing UUID, or None. Never invents one."""` is accurate about
`_read_identity` and misleading about the pipeline: the function does not invent one,
and the function it feeds does.

**Same family as T6's own defect #5**, recorded in 0026: *"malformed identity fails
loudly" was satisfied by a silent `None`.* That was found in the **gate**. This is the
same substitution in the **product**, and no assertion caught it because no gate
exercises update-over-a-broken-manifest.

---

## 3. Defect 2 — a failed update destroys the memory it preserves

```python
preserved = None
try:
    if mode == "update" and (dest / _STATE).is_dir():
        preserved = Path(tempfile.mkdtemp(prefix="uh-state-"))
        shutil.move(str(dest / _STATE), str(preserved / _STATE))
    if exists and mode in ("reinstall", "update"):
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(payload, dest, ignore=_ignore)
    if preserved is not None:
        ...
        shutil.move(str(preserved / _STATE), str(dest / _STATE))
finally:
    if preserved is not None:
        shutil.rmtree(preserved, ignore_errors=True)
```

Between the first `move` and the last, `preserved` holds the **only** copy of
`_state` — the journal, the evidence, the event log, the workbench — and the old
`dest` has already been deleted. If `copytree` raises for any reason (disk full,
permission, a payload that vanished, an interrupted run), the `finally` clause
unconditionally deletes it.

**A crash mid-update destroys both the instance and its durable memory.** The
`finally` was written to clean up a temp directory and does not distinguish *"cleanup
after success"* from *"this is the last copy."*

Compounding it, the result reports:

```python
"memory_preserved": mode == "update",
```

That is a **restatement of the requested mode, not an observation of the outcome**. It
returns `true` when there was no `_state` to preserve, and it would return `true` on
the run where the memory was lost — if that run reached the return at all. The one
field a user would check to find out whether their journal survived cannot answer the
question.

---

## 4. What is in scope, and what is not

**In scope — these two defects only:**

- identity continuity across update must not be silently breakable; a broken manifest
  must fail loudly at the installer boundary, not be absorbed
- durable memory must survive a failed update, and `memory_preserved` must report an
  **observation** rather than the requested mode
- gate assertions for both, written before the fix (BCC §2.8), each **mutation-tested**
  so it is seen to fail against the current behaviour — protocol §5.1a: a check
  claiming to detect an absent condition must be seen to fail

**Explicitly out of scope**, recorded in the backlog rather than absorbed:

- the canonical payload assembler (still `P-install-packaging`)
- uninstall, startup and self-maintenance rows of E8's phase matrix
- `_instance_module`'s docstring says the identity authority is loaded *"FROM THE
  PAYLOAD JUST INSTALLED"*, while the update path calls it before the copy and
  therefore loads the **old** tree's copy. That may be the correct behaviour — reading
  an old manifest with the code that wrote it — but the comment and the call order
  disagree, and one of them is wrong. **Recorded, not fixed here**: it is a third
  finding, and this reopening is bounded to two.
- `patch` declaring `writes: toolkit` while writing to a target path (T8 owns it)

---

## 5. Status of everything else

| | |
| --- | --- |
| T6 | **REOPENED**, bounded to §4 |
| T7 | **sketched, not declared** — unchanged by this entry |
| convergence phase, C1–C4, prototype STOP | adopted in 0027, **unaffected** |
| 0027 | **unedited.** Its status line is superseded here, its text is not |
| gates t00–t06 | green on Linux at the time of writing; no gate covers either defect, which is why neither was found by one |

**Neither defect was found by a failing check.** Both were found by reading the update
path while correcting stale documentation. A tranche that parks with a green suite and
an unexercised lifecycle path has been verified for what it was asked, not for what it
claimed.

---

## 6. Also corrected in this pass — active staleness only

Truth-alignment on active surfaces. No archived material touched, no BCC change.

| Surface | Was | Now |
| --- | --- | --- |
| `CHARTER.md` §0 | *"`installer_view` is the first"* | that file is deleted; the setup application is `packaging/installer/install.py` |
| `CHARTER.md` §3.5 | *"95 registered tools"* | **94**, the live registry count, dated |
| `CHARTER.md` §3.5 | GUI-crosses-seam cited `installer_view.py:131` | cites a live surface, and notes that `gates/t02` proves it by census — which is why deleting the cited file cost no assertion |
| `CHARTER.md` §6.6 | *"the count moves from 95 to 94 when `apps/` goes"* | stale arithmetic: the count is already 94 with `apps/` still contributing. Re-derive at `P-retire-apps` |
| `CHARTER.md` §7.2 | read as a current defect | banner: **HISTORICAL, SUPERSEDED BY T6.** Text retained unedited — the defect class it names is the one this project keeps rediscovering |
| `README.md` | claimed one compact understanding shared by human and agent | that is T7's outcome. Now states what `attach` does **today** and names shared awareness and diff-before-approve as **not yet** |
| `README.md` | *"delete the sidecar folder and the project is exactly as it was"* | split into two rows: removing the **instrument** leaves no trace; a governed **Apply** changes target files and those changes are yours and persist |
| `docs/ONBOARDING.md`, `AGENTS.md`, `README.md` | launchers *"run from anywhere"* | accurate: they are **not on `PATH`** and must be invoked by path; each resolves its own directory, so the *working directory* does not matter |

The launcher phrasing was introduced earlier the same day, in all three files at once.
Correcting all three is one repair, not a widened sweep.

---

## 7. Next

Discharge §4 under the ordinary tranche loop — gate first, mutation-tested, discovery
pass at close, operator approval before parking. **T6 does not park again until both
defects have an assertion behind them.**

T7 is not declared while T6 is open.
