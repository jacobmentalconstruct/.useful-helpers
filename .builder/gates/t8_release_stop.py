from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

# The gate imports and executes product/factory code while also enforcing repository
# hygiene, so it must not create bytecode in the source tree it measures.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FIXTURE_ROOT = (ROOT / "tests/.runtime").resolve()


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _run(command: list[str], *, cwd: Path = ROOT, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
        timeout=timeout,
    )


def _git(*arguments: str) -> str:
    process = _run(["git", *arguments])
    if process.returncode:
        raise AssertionError(process.stderr.strip() or process.stdout.strip())
    return process.stdout.strip()


def _imports(source: str, filename: str) -> list[str]:
    tree = ast.parse(source, filename=filename)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.extend(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.extend(alias.name for alias in node.names)
    return imported


def _build_release(output: Path) -> dict:
    process = _run([sys.executable, "-m", "factory", "release", "build", "--output", str(output)])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return json.loads(process.stdout)


def _temporary_directory(prefix: str) -> tempfile.TemporaryDirectory:
    RUNTIME_FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix=prefix, dir=RUNTIME_FIXTURE_ROOT)


def _release_artifact_boundary() -> str:
    with _temporary_directory(prefix="t8-release-") as scratch:
        built = _build_release(Path(scratch))
        artifact = Path(built["artifact"])
        manifest = json.loads(Path(built["manifest"]).read_text(encoding="utf-8"))
        with zipfile.ZipFile(artifact) as bundle:
            names = sorted(bundle.namelist())
            embedded = json.loads(bundle.read("RELEASE_MANIFEST.json").decode("utf-8"))
        required = {
            "factory/__main__.py",
            "factory/cli.py",
            "factory/installer.py",
            "factory/release.py",
            "product/bin/sidecar.py",
            "product/core/mcp.py",
            "product/core/mutation.py",
            "RELEASE_MANIFEST.json",
        }
        missing = sorted(required - set(names))
        if missing:
            raise AssertionError(f"release artifact missing required members: {missing}")
        forbidden_fragments = (
            ".builder/",
            "tests/",
            ".git/",
            "release/",
            "_projectmapper/",
            "_exports/",
            "__pycache__",
            ".pytest_cache",
            ".ruff_cache",
        )
        leaked = sorted(name for name in names if any(fragment in name for fragment in forbidden_fragments))
        if leaked:
            raise AssertionError(f"release artifact contains forbidden construction material: {leaked[:10]}")
        serialized = json.dumps({"names": names, "manifest": embedded, "outer": manifest}, sort_keys=True)
        if str(ROOT) in serialized or "C:\\" in serialized:
            raise AssertionError("release metadata leaks sandbox/local absolute paths")
        if manifest["artifact"]["sha256"] != _sha256_file(artifact):
            raise AssertionError("release manifest artifact digest does not match archive bytes")
        if embedded["artifact"]["install_command"] != "python -m factory attach <target>":
            raise AssertionError("embedded release manifest does not expose install command")
    return f"positive zip boundary contains {len(names)} files and no construction material"


def _focused_t8_product_evidence() -> str:
    process = _run([sys.executable, "-B", "-m", "pytest", "tests/test_t8_release_stop.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _canonical_product_regression() -> str:
    process = _run([sys.executable, "-B", "-m", "pytest", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _windows_release_lifecycle() -> str:
    process = _run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_install_blank_state_relocation_update_and_removal",
            "tests/test_t8_release_stop.py::T8ReleaseStopTests::test_sealed_cli_and_mcp_complete_the_same_governed_mutation_walk",
            "-q",
        ],
        timeout=120,
    )
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return "sealed artifact passed Windows lifecycle and CLI/MCP mutation walk"


def _linux_release_smoke() -> str:
    with _temporary_directory(prefix="t8-linux-release-") as scratch:
        built = _build_release(Path(scratch))
        artifact = Path(built["artifact"])
        artifact_wsl = _wsl_path(artifact)
        script = r"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import zipfile

artifact = pathlib.Path(sys.argv[1])
root = pathlib.Path(tempfile.mkdtemp(prefix="sidecar-t8-linux-"))
try:
    release_root = root / "release"
    target = root / "target"
    target.mkdir()
    (target / "pyproject.toml").write_text("[project]\nname='linux-smoke'\n", encoding="utf-8")
    (target / "README.md").write_text("# linux smoke\n", encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    with zipfile.ZipFile(artifact) as bundle:
        bundle.extractall(release_root)
    attach = subprocess.run(
        [sys.executable, "-m", "factory", "attach", str(target)],
        cwd=release_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if attach.returncode:
        raise SystemExit(attach.stdout + attach.stderr)
    front = target / ".sidecar" / "bin" / "sidecar.py"

    def sidecar(*args):
        process = subprocess.run(
            [sys.executable, str(front), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
        if process.returncode:
            raise SystemExit(process.stdout + process.stderr)
        return json.loads(process.stdout)

    status = sidecar("status")
    sidecar("substrate", "refresh")
    revision = sidecar("awareness", "refresh")["revision"]
    current = sidecar("awareness", "current")["revision"]
    if current["awareness_id"] != revision["awareness_id"] or current["freshness"] != "current":
        raise SystemExit("linux awareness current did not match refreshed revision")
    if revision["summary"]["domain_profile"] != "software":
        raise SystemExit(f"linux sealed artifact reported {revision['summary']['domain_profile']!r}")
    sidecar("awareness", "drill", revision["findings"][0]["item_id"])
    preview = sidecar(
        "mutation",
        "preview-write",
        "--path",
        "src/app.py",
        "--content",
        "def main():\n    return 2\n",
        "--overwrite",
    )["preview"]
    approval = sidecar("mutation", "approve", preview["preview_id"])["approval"]
    applied = sidecar("mutation", "apply", approval["approval_id"])
    if applied["mutation"]["measurement"]["changed_paths"] != ["src/app.py"]:
        raise SystemExit("linux mutation changed-path measurement was not durable or exact")
    receipts = sidecar("receipts", "list")["receipts"]
    if not any(item["receipt_id"] == applied["mutation"]["receipt_id"] for item in receipts):
        raise SystemExit("linux mutation receipt is not visible through durable receipt list")
    history = sidecar("mutation", "history")["mutations"]
    if not history:
        raise SystemExit("linux mutation history is empty after apply")
    after_mutation_awareness = sidecar("awareness", "current")["revision"]
    if after_mutation_awareness["awareness_id"] != applied["mutation"]["post_awareness_id"]:
        raise SystemExit("linux awareness was not refreshed after mutation")
    update = subprocess.run(
        [sys.executable, "-m", "factory", "update", str(target)],
        cwd=release_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if update.returncode:
        raise SystemExit(update.stdout + update.stderr)
    remove = subprocess.run(
        [sys.executable, "-m", "factory", "uninstall", str(target)],
        cwd=release_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if remove.returncode:
        raise SystemExit(remove.stdout + remove.stderr)
    print(json.dumps({"ok": True, "uuid": status["instance_uuid"], "removed": not (target / ".sidecar").exists()}))
finally:
    shutil.rmtree(root, ignore_errors=True)
"""
        process = _run(["wsl", "python3", "-c", script, artifact_wsl], timeout=120)
        if process.returncode:
            raise AssertionError(process.stdout.strip() or process.stderr.strip())
        result = json.loads(process.stdout.strip().splitlines()[-1])
        if not result.get("ok") or not result.get("removed"):
            raise AssertionError(result)
    return "same release artifact completed Linux observe/orient/drill/mutation/state/update/removal walk"


def _mcp_governed_mutation_parity() -> str:
    source = (ROOT / "product/core/mcp.py").read_text(encoding="utf-8")
    required = [
        '"mutation.preview_write"',
        '"mutation.approve"',
        '"mutation.apply"',
        "mutation.preview_write(",
        "mutation.approve(",
        "mutation.apply(",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"MCP mutation lifecycle terms missing: {missing}")
    forbidden = ("sqlite3", "mutation_previews", "mutation_approvals", "mutation_records")
    leaked = [term for term in forbidden if term in source]
    if leaked:
        raise AssertionError(f"MCP owns mutation persistence directly: {leaked}")
    return "MCP exposes preview/approve/apply through mutation owner APIs"


def _dependency_direction() -> str:
    violations: list[str] = []
    product_blocked_roots = {"factory", "tests", ".builder"}
    for source in sorted((ROOT / "product").rglob("*.py")):
        relative = source.relative_to(ROOT).as_posix()
        imports = _imports(source.read_text(encoding="utf-8"), relative)
        for imported in imports:
            if imported.split(".", 1)[0] in product_blocked_roots:
                violations.append(f"{relative} imports {imported}")
    for source in sorted((ROOT / "product/tools").glob("*/tool.py")):
        relative = source.relative_to(ROOT).as_posix()
        imports = _imports(source.read_text(encoding="utf-8"), relative)
        forbidden = [
            item
            for item in imports
            if item.startswith("core.") and not item.startswith("core.tool_runtime")
        ]
        if forbidden:
            violations.append(f"{relative} imports non-runtime core modules: {forbidden}")
    runtime_source = (ROOT / "product/core/tool_runtime.py").read_text(encoding="utf-8")
    runtime_forbidden = [
        item
        for item in _imports(runtime_source, "product/core/tool_runtime.py")
        if item.startswith("core.")
    ]
    if runtime_forbidden:
        violations.append(f"product/core/tool_runtime.py imports higher core modules: {runtime_forbidden}")
    journal_source = (ROOT / "product/core/app_journal.py").read_text(encoding="utf-8")
    journal_forbidden = ("awareness", "mcp", ".builder", "tests", "factory")
    leaked = [term for term in journal_forbidden if term in journal_source]
    if leaked:
        violations.append(f"app_journal imports or mentions upward/construction owners: {leaked}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "product boundary, mechanical lower layer, and App Journal dependency direction hold"


def _release_discrimination_witness() -> str:
    release_source = (ROOT / "factory/release.py").read_text(encoding="utf-8")
    test_source = (ROOT / "tests/test_t8_release_stop.py").read_text(encoding="utf-8")
    mcp_source = (ROOT / "product/core/mcp.py").read_text(encoding="utf-8")
    witnessed: list[str] = []
    mutations: tuple[tuple[str, Callable[[], None]], ...] = (
        (
            "artifact includes construction root",
            lambda: _assert_release_boundary_source(
                release_source.replace('".builder",', "")
            ),
        ),
        (
            "artifact lacks manifest",
            lambda: _assert_release_boundary_source(
                release_source.replace("RELEASE_MANIFEST.json", "MISSING_MANIFEST.json")
            ),
        ),
        (
            "tests omit update preservation",
            lambda: _assert_t8_tests(test_source.replace('"update"', '"skip-update"')),
        ),
        (
            "tests omit removal witness",
            lambda: _assert_t8_tests(test_source.replace('"uninstall"', '"skip-uninstall"')),
        ),
        (
            "MCP lacks governed apply",
            lambda: _assert_mcp_parity_source(mcp_source.replace('"mutation.apply"', '"mutation.history"')),
        ),
        (
            "tests omit sealed target breadth",
            lambda: _assert_t8_tests(
                test_source.replace("test_sealed_cli_orients_empty_software_and_mixed_document_targets", "")
            ),
        ),
        (
            "tests omit sealed MCP error witness",
            lambda: _assert_t8_tests(
                test_source.replace('"content is required"', '"not checked"')
            ),
        ),
    )
    for label, function in mutations:
        try:
            function()
        except AssertionError:
            witnessed.append(label)
        else:
            raise AssertionError(f"discrimination accepted {label}")
    return "rejected: " + "; ".join(witnessed)


def _assert_release_boundary_source(source: str) -> None:
    for term in ('".builder"', '"tests"', "RELEASE_MANIFEST.json", "_INCLUDED_ROOTS"):
        if term not in source:
            raise AssertionError(f"release boundary source missing {term}")


def _assert_t8_tests(source: str) -> None:
    for term in (
        "test_sealed_cli_orients_empty_software_and_mixed_document_targets",
        "empty_or_nascent",
        "software",
        "mixed",
        '"update"',
        '"uninstall"',
        "mutation.preview_write",
        "stale_target",
        "changed_paths",
        "product/core/mcp.py",
        "content is required",
    ):
        if term not in source:
            raise AssertionError(f"T8 tests missing {term}")


def _assert_mcp_parity_source(source: str) -> None:
    for term in ('"mutation.preview_write"', '"mutation.approve"', '"mutation.apply"'):
        if term not in source:
            raise AssertionError(f"MCP parity missing {term}")


def _static_discovery() -> str:
    process = _run([sys.executable, "-B", "-m", "ruff", "check", ".", "--no-cache"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    parsed = 0
    for source in ROOT.rglob("*.py"):
        if ".git" in source.parts or ".builder/evidence" in source.as_posix():
            continue
        try:
            source.resolve().relative_to(RUNTIME_FIXTURE_ROOT)
            continue
        except ValueError:
            pass
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        parsed += 1
    return f"Ruff passed and {parsed} Python sources parsed"


def _working_tree_provenance() -> str:
    status = _git("status", "--short")
    offending = [
        line
        for line in status.splitlines()
        if not (line.startswith("??") and line[3:].startswith(".builder/evidence/"))
    ]
    if offending:
        raise AssertionError(f"working tree differs from head_commit: {offending[:8]}")
    return "measured source is fully contained in head_commit (untracked evidence receipts only)"


def _repository_hygiene() -> str:
    forbidden = {"__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist"}
    debris: list[str] = []
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT).as_posix()
        if ".git" in path.parts or ".builder/evidence" in relative:
            continue
        if "_projectmapper" in path.parts:
            continue
        if path.is_dir() and (path.name in forbidden or path.name.endswith(".egg-info")):
            debris.append(relative)
    runtime = ROOT / "tests/.runtime"
    if runtime.exists() and any(runtime.iterdir()):
        debris.append("tests/.runtime (non-empty)")
    if debris:
        raise AssertionError(f"generated debris remains: {sorted(debris)}")
    return "no generated cache, bytecode, build, or fixture debris remains"


def _check(name: str, function: Callable[[], str]) -> Check:
    try:
        return Check(name, "PASS", function())
    except Exception as exc:
        return Check(name, "FAIL", f"{type(exc).__name__}: {exc}")


def _source_digest() -> str:
    digest = hashlib.sha256()
    paths = [
        Path(__file__).resolve(),
        *sorted((ROOT / "factory").glob("*.py")),
        *sorted((ROOT / "product").rglob("*.py")),
        *sorted((ROOT / "product").rglob("manifest.json")),
        *sorted((ROOT / "tests").glob("test_*.py")),
    ]
    for source in paths:
        digest.update(source.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(source.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _wsl_path(path: Path) -> str:
    resolved = path.resolve()
    drive = resolved.drive.rstrip(":").lower()
    parts = resolved.parts[1:]
    return "/mnt/" + drive + "/" + "/".join(parts)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the authoritative T8 release and STOP gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T8",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    RUNTIME_FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    arguments = _arguments()
    checks = [
        _check("working_tree_provenance", _working_tree_provenance),
        _check("release_artifact_boundary", _release_artifact_boundary),
        _check("focused_t8_product_evidence", _focused_t8_product_evidence),
        _check("windows_release_lifecycle", _windows_release_lifecycle),
        _check("linux_release_smoke", _linux_release_smoke),
        _check("mcp_governed_mutation_parity", _mcp_governed_mutation_parity),
        _check("dependency_direction", _dependency_direction),
        _check("canonical_product_regression", _canonical_product_regression),
        _check("static_discovery", _static_discovery),
        _check("release_discrimination_witness", _release_discrimination_witness),
        _check("repository_hygiene", _repository_hygiene),
    ]
    passed = all(check.status == "PASS" for check in checks)
    recorded = datetime.now(timezone.utc)
    run_id = recorded.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence_directory = arguments.evidence_root.resolve() / run_id
    evidence_directory.mkdir(parents=True, exist_ok=False)
    release_directory = evidence_directory / "release"
    built = _build_release(release_directory)
    evidence_path = evidence_directory / "t8-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T8-release-stop",
        "status": "PASS" if passed else "FAIL",
        "recorded_at": recorded.isoformat(),
        "run_id": run_id,
        "head_commit": _git("rev-parse", "HEAD"),
        "working_tree": _git("status", "--short"),
        "source_digest": _source_digest(),
        "release_artifact": {
            "path": Path(built["artifact"]).relative_to(ROOT).as_posix(),
            "manifest": Path(built["manifest"]).relative_to(ROOT).as_posix(),
            "sha256": built["artifact_sha256"],
            "file_count": built["file_count"],
        },
        "python": sys.version,
        "platform": platform.platform(),
        "checks": [asdict(check) for check in checks],
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "gate": evidence["gate"],
                "status": evidence["status"],
                "passed": sum(check.status == "PASS" for check in checks),
                "total": len(checks),
                "evidence": evidence_path.relative_to(ROOT).as_posix(),
                "release_artifact": evidence["release_artifact"],
                "source_digest": evidence["source_digest"],
                "failures": [asdict(check) for check in checks if check.status == "FAIL"],
            },
            indent=2,
        )
    )
    shutil.rmtree(RUNTIME_FIXTURE_ROOT, ignore_errors=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
