# 0008 — T1 Closed: One Ship Manifest

- **Date:** 2026-08-06
- **Tranche:** T1 — One Ship Manifest
- **Status:** **PARKED. Both gates green from a fresh clone.**

---

## 1. Result

```
fresh clone -> 85 tests in 21.2s -> OK (skipped=9)
fresh clone -> t00_foundation    -> PASS
fresh clone -> t01_ship_manifest -> PASS
                                    47 assertions, 0 fail, 0 skip
vended file count: 276  (bound 500; a leak once shipped 4,009)
```

Windows remains the authority for a zero-skip run — `ollama` and `ruff` are absent
from the sandbox.

---

## 2. What Was Built

`src/core/payload.py` is the single source of truth. Five copies of one rule —
`vendor_export`, the harness, `ruff.toml`, and two test scopes — now derive from it.

**Categories, not a flat list.** This is the substance of the tranche. A flat set
cannot distinguish four different reasons for exclusion, and under one, `packaging/`
sat beside `_trash`:

| Category | Reason |
| --- | --- |
| `REGENERABLE`, `VCS` | universal — excluded from **any** export, including a user's own project |
| `NEVER_SHIP` | the sidecar's scaffolding and history |
| `INSTALLER_ONLY` | `packaging/` — deliverable #1, ships **beside** the payload |
| `EXPORT_SUBSTITUTED` | templates swapped in at export |
| `FOREIGN` | not our code at all |

### 2.1 Two distinctions that had to be preserved

**Universal versus sidecar-only.** `CLEAN_APP_STRIP` applies only when exporting the
sidecar itself. Applying it to a target export would strip a user's own `_docs/` or
`gates/` — the sidecar quietly editing the target's shape. Collapsing the categories
into one set would have caused exactly that.

**Lint scope is not ship scope.** `gates/` does not ship but is ours and should meet
our bar; the parts bin is neither shipped nor ours. Asserting the ship set against
`ruff.toml` would have excluded our own gates from linting. Hence `FOREIGN`, a
proper subset of `NEVER_SHIP` on a different axis.

---

## 3. Two More Collapse Leftovers

Found while wiring, both invisible until something derived from a shared source:

- `CLEAN_APP_DOC_OVERRIDES` still wrote `ONBOARDING.md` into `_docs/`, which is now
  the journal and is stripped from every export. The substituted document was
  landing in a directory that does not ship.
- The payload had **no ignore file of its own** and would have shipped the
  development one — naming the parts bin, harness, gates and trash. Build-time shape
  leaking into a delivered artifact. It now gets a minimal one through the existing
  substitution mechanism, which `sidecar_install` already applies.

---

## 4. Seven Wrong Assertions

Two more this tranche, both false positives, neither a defect:

- `"evidence"` matched `tools/evidence/` — the shipped evidence **tool** — and
  reported a legitimate capability as leaked history. The sidecar ships tools *named*
  for the concepts it records; the record is what must not travel.
- The `.gitignore` check grepped for `gates` and hit **its own comment** explaining
  what the payload file deliberately omits. It now reads rules, not prose.

That is seven across T0 and T1. Every one was found by running the gate, none by
reading it. The recurring shape: **an assertion written from expectation is a
hypothesis; only execution separates it from a fact.** Both of today's came from
matching a bare word where a structured check was needed.

---

## 5. Park Point

**T1 is closed.** One manifest, declared by category, with every consumer deriving
from it; the payload vends at 276 files carrying no history, no installer, and its
own ignore file; and the installer — a shipped artifact no check had previously
examined — passes the same blank test.

**Next.** T2 — Ledger and Presence. Not declared.

**Carried:** Windows zero-skip verification, and the standing gaps from 0004 —
`test_d1_p1` slow until the parts bin goes, `VERSION` not moving with tool changes.
