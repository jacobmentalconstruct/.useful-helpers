# 0002 — Toolkit Safety Gate Executed

- **Date:** 2026-08-05
- **Tranche:** 1 (reopened for verification only)
- **Status:** Complete. Verification gap from entry 0001 closed.
- **Reason for reopening:** Entry 0001 parked with every toolkit claim marked
  provisional because no shell was available. A Linux sandbox became available.
  Executing the recorded gate closes a declared gap; it does not expand scope.

---

## 1. Environment

- Linux 6.8.0 / Ubuntu 22.04, Python 3.10.12, in an isolated VM.
- The project folder is mounted into the VM, so the real toolkit was exercised.
- **Docker is not reachable.** It is installed and running on the operator's
  Windows host, but this sandbox is an isolated VM with no route to that daemon.
  Docker is therefore not usable for this project's verification.
- No Windows shell. Windows-specific behavior (`run.bat`, the Tk UI entrance,
  `.venv\Scripts\python.exe` resolution) remains **unverified**.

---

## 2. Gate Results

| # | Check | Result |
| --- | --- | --- |
| 1 | Toolkit runs; manifest count | **PASS** — 95 tools, VERSION 1.1.0 |
| 2 | `SUITE_PROJECT_ROOT` binds the target | **PASS** |
| 3 | Observe leaves target byte-identical | **PASS** |
| 4 | Precept violation fails the call | **PASS**, with a critical caveat |
| 5 | Invalid `SUITE_PROJECT_ROOT` | **FAIL — confirmed frailty** |
| 6 | Timeout | **PASS** — clean at 120 s |
| 7 | `SUITE_STATE_ROOT` / `SUITE_HOME` redirect | **PASS** |

### 2.1 Commands and evidence

**Check 1.** `python3 -m src.app cli tool-list` → `{"count": 95, ...}`.
Cross-checked against disk: 95 `tools/*/tool.json`; set difference against the
registry is exactly `{_template}`, and the registry contains one id not present
under `tools/`, sourced from `apps/`.

**Check 2.** `SUITE_PROJECT_ROOT=/tmp/scratchHUYg ... --tool file_tree` returned
`"root": "/tmp/scratchHUYg"` and listed only that tree's entries. The override
works, unmodified, exactly as inferred in entry 0001.

**Check 3.** `md5sum` manifest of the scratch target before and after a
`file_tree` call: identical.

**Check 4.** A fixture tool declaring `authority: Observe` / `writes: none` that
writes into the target was added to an **isolated copy** of the toolkit at
`/tmp/tkcopy` — the operator's toolkit was not modified. Result:

```
"ok": false,
"error": "precept violation: 'evil_probe' (writes=none) modified the target
          it may not write to: ['/tmp/victimYlEV/SNEAKY_WRITE.txt']"
```

Control run with `SUITE_STRICT_OBSERVE=0`: `ok=True, error=None`.

**Check 5.** `SUITE_PROJECT_ROOT=/tmp/does-not-exist-NNN` returned `ok: true`
and `"root": "/sessions/.../.useful-helpers-workbench"`.

**Check 6.** A fixture sleeping 125 s: started 09:07:05, returned 09:09:05 with
`"error": "timeout after 120s"`, `exit_code: null`. No orphaned child process.

**Check 7.** With `SUITE_STATE_ROOT` set, `journal add` wrote `journal.sqlite3`
and `event_log.sqlite3` into the override. Isolated re-test confirmed the
**seam's own** event log also honours the override: `toolkit/_state/` mtime was
byte-for-byte unchanged across the call.

---

## 3. Findings That Change the Design

### 3.1 The precept guard detects; it does not prevent

`SNEAKY_WRITE.txt` existed on disk after the call that reported failure. The
seam cannot sandbox a subprocess, so a violating write lands and is then caught.

This reframes it. A precept violation must be surfaced to the user as *"this
tool modified your project when it declared it would not"* — a damage event
requiring attention — not as a generic failed operation.

Further: `SUITE_STRICT_OBSERVE=0` disables the guard silently. The bridge must
set it to `1` explicitly on every invocation rather than inheriting it, or an
unrelated environment setting can switch the guarantee off.

### 3.2 Silent fallback on a bad root is the most dangerous finding

A typo in the target root does not raise. The toolkit resolves to this
repository and reports success. Any bridge that trusts its own request without
verifying the echoed root can operate on the wrong tree and be told it worked.

Mitigation is now mandatory, not advisory: validate before launch, assert the
echoed root equals the requested root, fail hard on mismatch.

### 3.3 SQLite over the mounted filesystem is unreliable

Reading `toolkit/_state/event_log.sqlite3` from the VM raised
`sqlite3.OperationalError: disk I/O error`, and a stale `-journal` file was
present. This is characteristic of SQLite over a host-folder mount.

This empirically supports the blueprint's existing rule that runtime state
belongs in a platform user-data location rather than inside the project. It is
now evidence, not preference.

### 3.4 Inherited runtime state is present in the repository

`toolkit/_state/` holds ~1.1 MB of prior-engagement memory: a 1 MB
`event_log.sqlite3` with a stale journal, `journal.sqlite3` (20 Jul),
`llm_usage.jsonl` (28 Jul), and a `workbench/` directory. `toolkit/logs/` holds
`suite.log`.

This is predecessor operational data, not this project's history. It is covered
by the ignore rules written in Tranche 0. Whether it should be cleared is an
operator decision, recorded in the backlog rather than acted on unilaterally.

### 3.5 The project is not under version control

`git rev-parse` confirms no repository. The `.gitignore` written in Tranche 0 is
currently inert. For a project governed by tranche discipline with a
deletable-reference-zone requirement, the absence of version control is a
material risk: there is no rollback, and the boundary tests that require
deleting reference zones have no safety net.

---

## 4. Changed Files

| File | Change |
| --- | --- |
| `.bcc/CAPABILITY_MATRIX.md` | Second edition: gate results, `[VERIFIED]` tags, corrected tool count, precept-guard caveat, upgraded frailty severity |
| `_docs/AppJOURNAL/0002-*.md` | This entry |

Entry 0001 was **not** rewritten, per BCC 3.4.

### 4.1 Incidental writes to the repository

Running the toolkit caused it to write its own audit trail inside its own home:

- `toolkit/_state/event_log.sqlite3` (+ `-journal`) — appended
- `toolkit/logs/suite.log` — appended

This is the seam behaving as designed: every invocation is recorded. Both paths
are gitignored. Disclosed rather than left for someone to discover.

Checks 4 and 6 used fixtures in an isolated `/tmp` copy; no fixture, and no
`SNEAKY_WRITE.txt`, ever existed inside the project. Verified by search after
cleanup. All `/tmp` fixtures were removed.

---

## 5. Correction to Entry 0001

Entry 0001 and the first edition of the capability matrix stated the toolkit has
**99** tools. That was a miscount of glob output. The correct figure is **95
registered**. Recorded here rather than by editing 0001.

---

## 6. Park Point

**Completed.** The declared verification gap from entry 0001 is closed. Six
checks pass; one confirmed a serious frailty; the mitigations are specified.

**Tranche 6 is no longer gated on verification.** It is gated on the §4.1
mitigations being implemented in the bridge.

**Still unverified.** All Windows-specific behavior: `run.bat`, the Tk UI
entrance, venv interpreter resolution, and Windows path handling. A Windows
shell is required and this environment cannot supply one.

**Next action.** Awaiting an operator decision on the sidecar reorganization
before Tranche 2 begins. The reorganization changes the target layout, so
starting the runtime scaffold first would risk building into a structure about
to move.

**New backlog items.** Decide whether to clear inherited `toolkit/_state/` and
`toolkit/logs/`; decide whether to initialize version control; obtain a Windows
verification path.
