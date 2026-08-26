from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FIXTURE_ROOT = (ROOT / "tests/.runtime").resolve()
RUNTIME_TABLES = {
    "operation_receipts",
    "operational_artifacts",
    "app_journal_entries",
    "app_journal_links",
}
DEFERRED_TABLE_TERMS = {
    "resources",
    "observations",
    "claims",
    "awareness_revisions",
}


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


def _run(command: list[str]) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
    )


def _git(*arguments: str) -> str:
    process = _run(["git", *arguments])
    if process.returncode:
        raise AssertionError(process.stderr.strip() or process.stdout.strip())
    return process.stdout.strip()


def _imports(tree: ast.AST) -> list[str]:
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return imported


def _storage_tables(source: str) -> list[str]:
    return re.findall(r"CREATE TABLE\s+([a-z_]+)", source)


def _assert_runtime_schema(source: str) -> None:
    tables = _storage_tables(source)
    missing = sorted(RUNTIME_TABLES - set(tables))
    if missing:
        raise AssertionError(f"runtime memory tables missing: {missing}")
    duplicates = sorted(table for table in set(tables) if tables.count(table) > 1)
    if duplicates:
        raise AssertionError(f"runtime memory tables are collapsed or duplicated: {duplicates}")
    leaked = sorted(term for term in DEFERRED_TABLE_TERMS if f"CREATE TABLE {term}" in source)
    if leaked:
        raise AssertionError(f"T2 storage declares deferred epistemic/awareness tables: {leaked}")


def _runtime_schema_separation() -> str:
    source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    _assert_runtime_schema(source)
    return "storage declares distinct T2 receipt, artifact, App Journal, and link tables only"


def _assert_runtime_owner_separation(records_source: str, journal_source: str) -> None:
    if "app_journal" in records_source or "app_journal_entries" in records_source:
        raise AssertionError("runtime receipt owner imports or writes App Journal state")
    if "operation_receipts" in journal_source or "INSERT INTO operation_receipts" in journal_source:
        raise AssertionError("App Journal owner writes operational receipt state")
    if ".builder" in records_source or ".builder" in journal_source:
        raise AssertionError("runtime memory owners reference construction history")


def _runtime_owner_separation() -> str:
    records_source = (ROOT / "product/core/runtime_records.py").read_text(encoding="utf-8")
    journal_source = (ROOT / "product/core/app_journal.py").read_text(encoding="utf-8")
    _assert_runtime_owner_separation(records_source, journal_source)
    return "receipts/artifacts and App Journal have separate runtime owners"


def _assert_receipt_failure_guard(control_source: str) -> None:
    required = [
        "runtime_records.begin_receipt",
        "receipt_persistence_failed",
        "durably_governed=False",
    ]
    missing = [term for term in required if term not in control_source]
    if missing:
        raise AssertionError(f"control plane lacks receipt persistence failure guard: {missing}")
    begin = control_source.index("runtime_records.begin_receipt")
    child = control_source.index("subprocess.run")
    if begin > child:
        raise AssertionError("receipt creation occurs after child process launch")


def _receipt_failure_guard() -> str:
    source = (ROOT / "product/core/control.py").read_text(encoding="utf-8")
    _assert_receipt_failure_guard(source)
    return "state-changing calls cannot be reported durably governed without receipt creation"


def _t1_dependency_boundary() -> str:
    runtime_source = ROOT / "product/core/tool_runtime.py"
    runtime_tree = ast.parse(runtime_source.read_text(encoding="utf-8"), filename=str(runtime_source))
    runtime_imports = [
        module for module in _imports(runtime_tree) if module == "core" or module.startswith("core.")
    ]
    runtime_relative = [
        node for node in ast.walk(runtime_tree) if isinstance(node, ast.ImportFrom) and node.level
    ]
    violations = []
    if runtime_imports or runtime_relative:
        violations.append("core.tool_runtime imports higher core subsystem")
    for source in sorted((ROOT / "product/tools").glob("*/tool.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for imported in _imports(tree):
            if (
                imported == "core"
                or imported.startswith("core.")
                and imported != "core.tool_runtime"
                and not imported.startswith("core.tool_runtime.")
            ):
                violations.append(f"{source.relative_to(ROOT).as_posix()} imports {imported}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T1 mechanical dependency boundary remains intact"


def _focused_t2_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t2_runtime_memory.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _canonical_product_regression() -> str:
    process = _run([sys.executable, "-m", "pytest", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _static_discovery() -> str:
    process = _run([sys.executable, "-m", "ruff", "check", ".", "--no-cache"])
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


def _product_boundary() -> str:
    blocked_roots = {"factory", "tests", ".builder"}
    scanned = 0
    for source in sorted((ROOT / "product").rglob("*.py")):
        scanned += 1
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for imported in _imports(tree):
            if imported.split(".", 1)[0] in blocked_roots:
                raise AssertionError(f"{source.relative_to(ROOT)} imports {imported}")
    return f"{scanned} product modules remain independent of factory, tests, and construction"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0018-t2-execution-start.md" not in entries:
        raise AssertionError("T2 execution start is not recorded")
    return f"journal is contiguous through {entries[-1]}"


def _discrimination_witness() -> str:
    storage_source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    records_source = (ROOT / "product/core/runtime_records.py").read_text(encoding="utf-8")
    journal_source = (ROOT / "product/core/app_journal.py").read_text(encoding="utf-8")
    control_source = (ROOT / "product/core/control.py").read_text(encoding="utf-8")

    collapsed_storage = storage_source.replace("app_journal_entries", "operation_receipts")
    auto_projection_records = records_source + "\n# app_journal_entries automatic projection\n"
    unguarded_control = control_source.replace("receipt_persistence_failed", "receipt_problem")

    witnessed: list[str] = []
    for label, function in (
        ("journal/receipt table collapse", lambda: _assert_runtime_schema(collapsed_storage)),
        (
            "automatic receipt-to-journal projection",
            lambda: _assert_runtime_owner_separation(auto_projection_records, journal_source),
        ),
        ("missing receipt failure guard", lambda: _assert_receipt_failure_guard(unguarded_control)),
    ):
        try:
            function()
        except AssertionError:
            witnessed.append(label)
        else:
            raise AssertionError(f"discrimination accepted {label}")
    return "rejected: " + "; ".join(witnessed)


def _repository_hygiene() -> str:
    forbidden = {"__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist", "release"}
    debris: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".builder/evidence" in path.as_posix():
            continue
        if path.is_dir() and (path.name in forbidden or path.name.endswith(".egg-info")):
            debris.append(path.relative_to(ROOT).as_posix())
    runtime = ROOT / "tests/.runtime"
    if runtime.exists() and any(runtime.iterdir()):
        debris.append("tests/.runtime (non-empty)")
    if debris:
        raise AssertionError(f"generated debris remains: {sorted(debris)}")
    return "no generated cache, bytecode, build, release, or fixture debris remains"


def _check(name: str, function: Callable[[], str]) -> Check:
    try:
        return Check(name, "PASS", function())
    except Exception as exc:
        return Check(name, "FAIL", f"{type(exc).__name__}: {exc}")


def _source_digest() -> str:
    digest = hashlib.sha256()
    paths = [
        Path(__file__).resolve(),
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


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the authoritative T2 runtime-memory gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T2",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("runtime_schema_separation", _runtime_schema_separation),
        _check("runtime_owner_separation", _runtime_owner_separation),
        _check("receipt_failure_guard", _receipt_failure_guard),
        _check("t1_dependency_boundary", _t1_dependency_boundary),
        _check("focused_t2_product_evidence", _focused_t2_product_evidence),
        _check("canonical_product_regression", _canonical_product_regression),
        _check("positive_product_boundary", _product_boundary),
        _check("journal_continuity", _journal_continuity),
        _check("static_discovery", _static_discovery),
        _check("discrimination_witness", _discrimination_witness),
        _check("repository_hygiene", _repository_hygiene),
    ]
    passed = all(check.status == "PASS" for check in checks)
    recorded = datetime.now(timezone.utc)
    run_id = recorded.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence_directory = arguments.evidence_root.resolve() / run_id
    evidence_directory.mkdir(parents=True, exist_ok=False)
    evidence_path = evidence_directory / "t2-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T2-runtime-receipts-work-memory",
        "status": "PASS" if passed else "FAIL",
        "recorded_at": recorded.isoformat(),
        "run_id": run_id,
        "head_commit": _git("rev-parse", "HEAD"),
        "working_tree": _git("status", "--short"),
        "source_digest": _source_digest(),
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
                "source_digest": evidence["source_digest"],
                "failures": [asdict(check) for check in checks if check.status == "FAIL"],
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
