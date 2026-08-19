"""
FILE:       gates/t08_governed_loop.py
ROLE:       Gate for T8 - Governed Work Loop Prototype.
DOMAIN:     factory
DOES:       Asserts three safety preconditions, then the whole change loop, through the
            product's own entrances against three representative targets.
NOTES:      Written at declaration, BEFORE implementation (protocol 3.2 rule 1), and
            BLACK-BOX like t07: no module, no class, no file is named.

            EVERY INTERFACE HERE WAS READ FROM THE CODE, NOT ASSUMED. That sentence is
            not boilerplate. The T8 sketch previously claimed `edit` preview returns the
            original text under `source` and proposed `diff(source, result)`. It does
            not: `tools/edit/cli.py` sets `content, source = path.read_text(...),
            "path"`, so `source` is the source KIND. A gate built on that would have
            diffed the word "path" against the new content and gone green against a
            product that never worked that way. The real review path uses one more
            existing tool:

                read_file  ->  edit preview  ->  diff(read.content, preview.result)

            THREE PRECONDITIONS, NOT FEATURES. Each is a live safety defect, and the
            loop is not trustworthy until all three are closed:

              1. `patch` has NO `writes` field, so an Apply tool that writes target
                 files is inferred `toolkit` - the precept guard skips it and the
                 declaration misdescribes it.
              2. Malformed governance fails OPEN. A broken config may keep permitting
                 Observe; it must not silently grant Apply.
              3. Malformed tool output fails OPEN. Empty stdout, invalid JSON, and valid
                 JSON that is not an object ALL yield ok=True. Charter 7.4 named this on
                 2026-08-06 and it is still live.

            THE STALE-PREVIEW WITNESS IS THE LOAD-BEARING NEW INVARIANT. An approved
            diff must land against the state that was approved. Today `apply_with`
            carries only {"apply": true}, so a review of state A can mutate state B.

            AND THE MUTATION MUST BE DISCRIMINATING. The interfering edit deliberately
            PRESERVES the pattern's match count, so `expected_replacements` cannot
            masquerade as the safety mechanism. If the witness is absent the Apply
            succeeds against changed bytes; only a real source witness refuses.

            TWO CLAIMS, KEPT APART, because conflating them would overstate the seam.

              changed_paths   a COARSE measured mutation signal. The seam's manifest is
                              mtime+size, bounded, with pruned directories - useful for
                              staleness and orientation, NOT proof of "only these bytes
                              changed". It must carry completeness/basis, and an
                              exceeded bound must remain an explicit state rather than
                              an empty list.
              hash proof      the GATE independently sha256s the fixture to assert that
                              only the approved content changed.

            VERIFICATION MEANS `test` OR `lint`. `setup` and `run` are runnable, not
            correctness checks, and a target supplying neither is an honest success -
            `_theCELL` detects only run/setup and that is a true answer, not a failure.

            RULE 8: exercised through the CLI and the real MCP entrance.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

OUTCOME = ("a reviewed, attributable, verifiable change against shared awareness, "
           "without losing the evidence of what was approved")

INSTALLER = "packaging/installer/install.py"
DEFAULT_HOME = ".useful-helpers"

# Verification-capable kinds. `setup` prepares and `run` executes; neither answers
# "is it still correct". A target offering only those supplies NO verification, and
# saying so is the correct outcome.
VERIFY_KINDS = ("test", "lint")


def check(r, root: Path) -> None:
    if not r.filesystem_permits_unlink(root):
        r.skip("the governed loop runs end to end",
               "this filesystem denies unlink; an install cannot be performed here")
        return

    payload = _materialise_payload(root)
    r.check("a payload fixture can be materialised", payload is not None,
            "the gate installs real instances")
    if payload is None:
        return

    # ---- PRECONDITIONS ----------------------------------------------------
    _precondition_patch_declares_target(r, root)
    _precondition_governance_denies_apply(r, root, payload)
    _precondition_malformed_output_fails(r, root, payload)

    # ---- THE LOOP ---------------------------------------------------------
    _loop(r, root, payload)

    # ---- DEGRADATION ------------------------------------------------------
    _degradation(r, root, payload)

    # ---- NO NEW SUBSYSTEM -------------------------------------------------
    _no_new_machinery(r, root)


# --------------------------------------------------------------------------
# Preconditions
# --------------------------------------------------------------------------
def _precondition_patch_declares_target(r, root: Path) -> None:
    """`patch` writes target files. Its manifest must SAY so.

    Not merely wrong - ABSENT. `tools/patch/tool.json` carries no `writes` field at all,
    so the registry infers `toolkit` for an Apply tool. Two consequences: the precept
    guard skips it, and the ledger records a write domain that does not match reality.
    """
    manifest = json.loads((root / "tools" / "patch" / "tool.json").read_text(encoding="utf-8"))
    r.check("`patch` declares its write domain explicitly",
            manifest.get("writes") == "target",
            f"tool.json writes={manifest.get('writes', '<absent>')!r} - an Apply tool with "
            "no `writes` field is inferred `toolkit`, and this one writes target files")
    reg = json.loads((root / "config" / "registry.json").read_text(encoding="utf-8"))
    entry = next((t for t in reg["tools"] if t["id"] == "patch"), {})
    r.check("the derived registry agrees that `patch` writes the target",
            entry.get("writes") == "target",
            f"registry writes={entry.get('writes')!r} - the generated catalog is derived, "
            "so it must be regenerated after the manifest is corrected")


def _precondition_governance_denies_apply(r, root: Path, payload: Path) -> None:
    """A broken governance file may keep permitting Observe. It must not grant Apply.

    Today it fails OPEN: malformed JSON and out-of-range values both fall back to the
    permissive default, warning loudly but granting everything. For a bench that can
    modify arbitrary target files, the safe posture is to keep diagnosis available and
    withhold mutation.
    """
    tgt = _target_software()
    if _install(root, tgt, payload).returncode != 0:
        r.skip("malformed governance denies Apply but permits Observe", "install failed")
        return
    home = tgt / DEFAULT_HOME
    (home / "config" / "governance.json").write_text('{ "max_authority": "Observe"',
                                                     encoding="utf-8")
    observe = _output(_cli(home, "read_file", {"path": "src/backend.py"}))
    applied = _output(_cli(home, "write_file",
                           {"path": "src/should_not_exist.py", "content": "x\n",
                            "apply": True}))
    r.check("malformed governance still permits Observe",
            bool(observe) and observe.get("ok") is not False,
            f"a broken config must remain diagnosable: {observe!r}")
    r.check("malformed governance denies Apply",
            (not applied) or applied.get("ok") is False,
            f"an Apply succeeded under a governance file that could not be read: "
            f"{applied!r} - failing open on a mutation control is the one direction a "
            "safety default must not fail")
    r.check("the denied Apply did not reach the filesystem",
            not (tgt / "src" / "should_not_exist.py").exists(),
            "the refusal must precede the write, not report it afterwards")


def _precondition_malformed_output_fails(r, root: Path, payload: Path) -> None:
    """Uninterpretable tool output must be a seam FAILURE, not a default success.

    Charter 7.4 recorded this in 2026-08-06 and it is still live: empty stdout, invalid
    JSON, and valid JSON that is not an object all yield `ok=True`, because `invoke`
    wraps unparseable output as `raw_stdout` and defaults `output.get("ok", True)`.

    THE FIXTURE WRITES FIRST, THEN EMITS GARBAGE. That is the whole point. A probe that
    merely prints nonsense proves only that the seam dislikes bad stdout; a probe that
    MUTATES THE TARGET and then becomes uninterpretable proves the seam refuses to call
    an ambiguous mutation outcome a success. That is the case T8 actually cares about.
    """
    tgt = _target_software()
    if _install(root, tgt, payload).returncode != 0:
        r.skip("uninterpretable tool output fails at the seam", "install failed")
        return
    home = tgt / DEFAULT_HOME

    cases = {
        "empty stdout": "",
        "invalid JSON": 'print("not json at all")',
        "valid JSON, not an object": 'import json; print(json.dumps([1, 2, 3]))',
    }
    for label, emit in cases.items():
        tool = _plant_tool(home, "t08probe", emit, writes_first=True)
        out = _cli(home, "t08probe", {"apply": True})
        env = _envelope(out)
        r.check(f"seam fails on {label} from a tool that already wrote",
                env.get("ok") is False,
                f"envelope reported ok={env.get('ok')!r} for {label!r}. The tool mutated "
                "the target and then produced output the seam cannot interpret; "
                "reporting that as success is a governed loop describing an outcome it "
                "does not know")
        shutil.rmtree(tool, ignore_errors=True)


# --------------------------------------------------------------------------
# The loop
# --------------------------------------------------------------------------
def _loop(r, root: Path, payload: Path) -> None:
    tgt = _target_software()
    if _install(root, tgt, payload).returncode != 0:
        r.check("an instance installs into the software target", False, "install failed")
        return
    home = tgt / DEFAULT_HOME
    rel = "src/backend.py"
    live = tgt / rel

    # --- start from a real awareness revision --------------------------
    aw_before = _awareness(home, refresh=True)
    rev_x = aw_before.get("revision")
    r.check("the loop starts from an awareness revision",
            bool(rev_x) and bool(aw_before.get("provenance")),
            f"revision={rev_x!r} - T8 begins from revision X + evidence X, not from a "
            "fresh look at the target")

    # --- impact, from a canonical handle -------------------------------
    handles = aw_before.get("handles") or []
    impact = {}
    if handles:
        h = handles[0]
        impact = _output(_cli(home, h.get("tool", "symbol_graph"),
                              dict(h.get("resolve_with") or {})))
    r.check("a canonical handle from awareness resolves to impact",
            bool(impact) and impact.get("ok") is not False,
            f"handles={[h.get('id') for h in handles][:3]} - impact inspection starts "
            "from an identifier awareness promoted, not a name reconstructed from prose")

    # --- read_file captures the ACTUAL before-state --------------------
    before = _output(_cli(home, "read_file", {"path": rel}))
    before_text = before.get("content")
    r.check("`read_file` captures the before-state",
            isinstance(before_text, str) and bool(before_text),
            f"got {type(before_text).__name__} - `edit` does NOT return the original "
            "content; `source` is the source KIND. The before-state comes from here")

    # --- preview -------------------------------------------------------
    pattern, replacement = "task list runner", "task list executor"
    prev = _output(_cli(home, "edit", {"path": rel, "pattern": pattern,
                                       "replacement": replacement, "literal": True}))
    proposed = prev.get("result")
    r.check("the preview proposes a result without writing",
            prev.get("written") is False and isinstance(proposed, str),
            f"written={prev.get('written')!r} result={type(proposed).__name__}")

    # --- diff, from the existing tool ----------------------------------
    d = _output(_cli(home, "diff", {"a_text": before_text or "", "b_text": proposed or "",
                                    "from_label": rel, "to_label": "proposed"}))
    r.check("the existing `diff` tool renders the reviewable change",
            bool(d.get("diff")) and d.get("identical") is False,
            f"identical={d.get('identical')!r} - approving a `replacements` count is not "
            "approving a change; the diff is what a human actually reviews")

    # --- THE WITNESS ---------------------------------------------------
    witness = (prev.get("apply_with") or {})
    r.check("the preview binds Apply to the reviewed source state",
            bool(witness.get("expected_source_sha256")),
            f"apply_with={witness!r} - without a source witness an approved diff can "
            "land against a state nobody reviewed")

    # DISCRIMINATING INTERFERENCE: change the file while PRESERVING the pattern's match
    # count, so `expected_replacements` cannot stand in for the witness. Only a real
    # source-state check can refuse this.
    if isinstance(before_text, str):
        live.write_text(before_text.replace("class Backend:",
                                            "class Backend:  # touched externally"),
                        encoding="utf-8")
    interfered = _sha(live)
    stale = _output(_cli(home, "edit", {"path": rel, "pattern": pattern,
                                        "replacement": replacement, "literal": True,
                                        **witness}))
    r.check("Apply refuses when the source changed after the preview",
            stale.get("ok") is False and stale.get("written") is not True,
            f"{stale!r} - the pattern still matches, so a replacement-count check cannot "
            "be what refuses this. Only the source witness can")
    r.check("the refused Apply left the file untouched",
            _sha(live) == interfered,
            "a refusal must not write")

    # --- re-preview against the new reality, then apply ----------------
    prev2 = _output(_cli(home, "edit", {"path": rel, "pattern": pattern,
                                        "replacement": replacement, "literal": True}))
    proposed2 = prev2.get("result")
    digest_before = _tree_digest(tgt)
    applied = _output(_cli(home, "edit", {"path": rel, "pattern": pattern,
                                          "replacement": replacement, "literal": True,
                                          **(prev2.get("apply_with") or {})}))
    r.check("an approved, unstale Apply writes",
            applied.get("written") is True,
            f"{applied!r}")
    r.check("the file now equals exactly what the preview proposed",
            live.read_text(encoding="utf-8") == proposed2,
            "the bytes on disk must be the bytes that were reviewed")

    # --- INDEPENDENT hash proof ----------------------------------------
    digest_after = _tree_digest(tgt)
    changed = sorted(k for k in set(digest_before) | set(digest_after)
                     if digest_before.get(k) != digest_after.get(k))
    r.check("only the approved file changed, proven by hash",
            changed == [rel],
            f"changed={changed} - the seam's mtime+size manifest is a coarse signal; "
            "this assertion is owned by an independent sha256 of the fixture")

    # --- attribution ----------------------------------------------------
    ledger = _output(_cli(home, "event_log", {"action": "read", "limit": 50}))
    events = ledger.get("events") or []
    r.check("the ledger attributes the Apply",
            any(e.get("tool_id") == "edit" and e.get("client") for e in events),
            f"no attributed `edit` entry in {len(events)} events")

    # --- changed_paths, as a COARSE signal with stated completeness -----
    signal = applied.get("changed_paths")
    basis = applied.get("measurement")
    r.check("the seam reports a measured mutation signal",
            signal is not None,
            "a governed Apply should say what it observed changing, measured rather "
            "than taken from the tool's own claim")
    r.check("the mutation signal states its basis and completeness",
            isinstance(basis, dict) and basis.get("basis") and "complete" in basis,
            f"measurement={basis!r} - mtime+size over a pruned, bounded walk is NOT "
            "byte-exact. An exceeded bound must be an explicit incomplete state, never "
            "an empty changed_paths")

    # --- verification, selected mechanically ----------------------------
    prof = _output(_cli(home, "command_profile", {"root": "."}))
    kinds = {c.get("kind") for c in (prof.get("commands") or [])}
    verify = sorted(kinds & set(VERIFY_KINDS))
    r.check("verification selection considers only meaningful kinds",
            not (kinds & {"setup", "run"} and verify == [] and applied.get("verification")),
            f"detected kinds={sorted(kinds)} - `setup` prepares and `run` executes; "
            "neither answers 'is it still correct'")
    r.check("a target with no verification says so honestly",
            bool(verify) or applied.get("verification", {}).get("available") is False,
            "no test or lint command is a truthful answer, not a failure to report")

    # --- awareness transition -------------------------------------------
    reeng = _output(_cli(home, "attach", {}))
    aw_stale = reeng.get("awareness") or {}
    r.check("the Apply made current awareness stale",
            (aw_stale.get("freshness") or {}).get("stale") is True,
            f"freshness={aw_stale.get('freshness')!r}")
    aw_after = _awareness(home, refresh=True)
    rev_y = aw_after.get("revision")
    r.check("refresh produces a new revision", bool(rev_y) and rev_y != rev_x,
            f"X={rev_x!r} Y={rev_y!r}")
    r.check("revision X is unchanged after Y exists",
            _revision_record(home, rev_x).get("evidence_fingerprint")
            == aw_before.get("evidence_fingerprint"),
            "the record of what was known BEFORE the change must survive the change")
    old_ev = ((aw_before.get("provenance") or {}).get("report") or {}).get("evidence_id")
    if old_ev:
        got = _output(_cli(home, "evidence", {"action": "get", "evidence_id": old_ev}))
        r.check("X still drills into its pre-change evidence",
                bool(got) and got.get("ok") is not False,
                f"evidence {old_ev!r} unreachable after the change")


def _degradation(r, root: Path, payload: Path) -> None:
    """Records and empty targets. The loop must degrade truthfully, not error."""
    for name, builder in (("records", _target_records), ("empty", _target_empty)):
        tgt = builder()
        if _install(root, tgt, payload).returncode != 0:
            r.check(f"an instance installs into the {name} target", False, "install failed")
            continue
        home = tgt / DEFAULT_HOME
        aw = _awareness(home, refresh=True)
        prof = _output(_cli(home, "command_profile", {"root": "."}))
        kinds = {c.get("kind") for c in (prof.get("commands") or [])}
        r.check(f"the {name} target still produces an awareness revision",
                bool(aw.get("revision")), f"got {sorted(aw) if aw else aw!r}")
        r.check(f"the {name} target reports no verification rather than inventing one",
                not (kinds & set(VERIFY_KINDS)),
                f"detected {sorted(kinds)} - if a thin target really does supply a test "
                "command that is fine, but it must be detected, not assumed")


def _no_new_machinery(r, root: Path) -> None:
    """T8 composes. A new diff/approval/verification/runner tool would mean it did not."""
    reg = json.loads((root / "config" / "registry.json").read_text(encoding="utf-8"))
    ids = {t["id"] for t in reg["tools"]}
    forbidden = sorted(i for i in ids if any(
        w in i for w in ("approval", "reviewer", "change_review", "verifier",
                         "verification", "differ", "runner_v2", "workloop")))
    r.check("no new diff/approval/verification/runner tool was created",
            not forbidden, f"new machinery: {forbidden}")
    r.check("no new application was added",
            {p.name for p in (root / "apps").iterdir() if p.is_dir()} <= {"projectmapper"},
            "the loop is chains over the bench; `apps/` is transitional and T8 does not "
            "add to it")


# --------------------------------------------------------------------------
# Fixtures and entrances
# --------------------------------------------------------------------------
def _target_software() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t08-soft-")) / "proj"
    (t / "src").mkdir(parents=True)
    (t / "requirements.txt").write_text("requests\n", encoding="utf-8")
    (t / "README.md").write_text("# Demo\n", encoding="utf-8")
    (t / "src" / "__init__.py").write_text("", encoding="utf-8")
    (t / "src" / "backend.py").write_text(
        '"""Hub."""\n\n\nclass Backend:\n'
        '    """ROLE: Orchestration hub - pure downstream task list runner."""\n\n'
        "    def start(self):\n        return 1\n", encoding="utf-8")
    for i in range(12):
        (t / "src" / f"svc_{i:02d}.py").write_text(
            f"from src.backend import Backend\n\n\nclass Svc{i:02d}:\n"
            f'    """Service {i}."""\n\n    def go(self):\n        return Backend()\n',
            encoding="utf-8")
    return t


def _target_records() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t08-rec-")) / "records"
    (t / "2025").mkdir(parents=True)
    (t / "index.csv").write_text("id,name\n1,Deed\n", encoding="utf-8")
    for i in range(5):
        (t / "2025" / f"f{i}.txt").write_text(f"Record {i}.\n", encoding="utf-8")
    return t


def _target_empty() -> Path:
    t = Path(tempfile.mkdtemp(prefix="t08-empty-")) / "blank"
    t.mkdir(parents=True)
    return t


def _plant_tool(home: Path, tool_id: str, emit: str, *, writes_first: bool) -> Path:
    """A registered tool that MUTATES the target and then emits `emit` verbatim.

    Writing first is what makes the malformed-output assertions mean anything: the
    question is not "does the seam dislike bad stdout" but "can the seam report an
    uninterpretable MUTATION as success".
    """
    d = home / "tools" / tool_id
    d.mkdir(parents=True, exist_ok=True)
    body = ["import os, sys"]
    if writes_first:
        body += ["from pathlib import Path",
                 "t = Path(os.environ['SUITE_PROJECT_ROOT']) / 'src' / 'probe_wrote.py'",
                 "t.write_text('# written by the probe\\n', encoding='utf-8')"]
    body += [emit] if emit else []
    (d / "cli.py").write_text("\n".join(body) + "\n", encoding="utf-8")
    (d / "tool.json").write_text(json.dumps({
        "id": tool_id, "summary": "gate probe", "category": "test",
        "authority": "Apply", "writes": "target", "operates_on": "project",
        "invocation": {"interpreter": "${ROOT_VENV_PYTHON}",
                       "entry": f"tools/{tool_id}/cli.py"},
        "input_schema": {"type": "object", "properties": {"apply": {"type": "boolean"}}},
        "output_shape": {"type": "object", "properties": {"ok": {"type": "boolean"}}},
    }, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "-m", "src.app", "cli", "registry-refresh"],
                   cwd=home, capture_output=True, text=True, timeout=180, env=_clean_env())
    return d


_LAST_ERR: list = []


def _cli(home: Path, tool: str, args: dict, timeout: int = 300):
    return subprocess.run(
        [sys.executable, "-m", "src.app", "cli", "tool-call",
         "--tool", tool, "--args-json", json.dumps(args)],
        cwd=home, capture_output=True, text=True, timeout=timeout, env=_clean_env())


def _envelope(proc) -> dict:
    """The FULL CLI envelope - `ok` here is the seam's verdict, not the tool's."""
    raw = (proc.stdout or "").strip()
    try:
        return json.loads(raw) if raw else {}
    except ValueError:
        _LAST_ERR.insert(0, raw[-200:])
        return {}


def _output(proc) -> dict:
    doc = _envelope(proc)
    inner = doc.get("output")
    return inner if isinstance(inner, dict) else doc


def _awareness(home: Path, *, refresh: bool = False) -> dict:
    out = _output(_cli(home, "attach", {"refresh": True} if refresh else {}))
    aw = out.get("awareness")
    return aw if isinstance(aw, dict) else {}


def _revision_record(home: Path, revision: "str | None") -> dict:
    if not revision:
        return {}
    p = home / "_state" / "awareness" / f"{revision}.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _sha(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def _tree_digest(target: Path) -> dict:
    """sha256 per target-owned file. The gate's OWN proof, independent of the seam."""
    out = {}
    for p in sorted(target.rglob("*")):
        if p.is_file() and DEFAULT_HOME not in p.parts:
            out[p.relative_to(target).as_posix()] = _sha(p)
    return out


def _materialise_payload(root: Path) -> "Path | None":
    try:
        sys.path.insert(0, str(root))
        from src.core import payload as manifest
        dst = Path(tempfile.mkdtemp(prefix="t08-payload-")) / "toolkit"
        shutil.copytree(root, dst, ignore=shutil.ignore_patterns(*manifest.PAYLOAD_EXCLUDE))
        return dst if (dst / "src").is_dir() else None
    except Exception:
        return None
    finally:
        if str(root) in sys.path:
            sys.path.remove(str(root))


def _install(root: Path, target: Path, payload: Path):
    return subprocess.run(
        [sys.executable, str(root / INSTALLER), "--target", str(target),
         "--payload", str(payload), "--mode", "install"],
        cwd=root, capture_output=True, text=True, timeout=600, env=_clean_env())


def _clean_env() -> dict:
    env = dict(os.environ)
    for k in ("SUITE_HOME", "SUITE_PROJECT_ROOT", "SUITE_STATE_ROOT",
              "SUITE_INSTANCE_UUID", "SUITE_MAX_AUTHORITY"):
        env.pop(k, None)
    return env
