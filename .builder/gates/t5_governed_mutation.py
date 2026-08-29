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
T5_TABLES = {
    "mutation_previews",
    "mutation_approvals",
    "mutation_records",
    "mutation_verifications",
    "mutation_links",
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


def _assert_t5_schema(source: str, constants: str) -> None:
    if "DATABASE_SCHEMA_VERSION = 5" not in constants:
        raise AssertionError("database schema version was not advanced to 5")
    if "target_version: int = DATABASE_SCHEMA_VERSION" not in source:
        raise AssertionError("migration cannot be staged by materialized target version")
    tables = _storage_tables(source)
    missing = sorted(T5_TABLES - set(tables))
    if missing:
        raise AssertionError(f"T5 mutation tables missing: {missing}")
    duplicates = sorted(table for table in T5_TABLES if tables.count(table) != 1)
    if duplicates:
        raise AssertionError(f"T5 tables are missing or duplicated: {duplicates}")
    for version in (3, 4, 5):
        if f"PRAGMA user_version = {version}" not in source:
            raise AssertionError(f"migration branch does not stamp materialized v{version}")


def _t5_schema() -> str:
    _assert_t5_schema(
        (ROOT / "product/core/storage.py").read_text(encoding="utf-8"),
        (ROOT / "product/core/constants.py").read_text(encoding="utf-8"),
    )
    return "schema version 5 adds distinct governed mutation tables with staged migration"


def _assert_mutation_owner(source: str) -> None:
    required = [
        "def preview_write(",
        "def approve(",
        "def apply(",
        "def list_history(",
        "def links(",
        "ControlPlane(context).invoke",
        "substrate.refresh(context)",
        "awareness.refresh(context)",
        "independent_target_snapshot",
        "No target-native verification mechanism is available.",
        "stale_target",
        "stale_basis",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"mutation owner lacks required loop behavior: {missing}")
    forbidden_sql = (
        "FROM resources",
        "FROM observations",
        "FROM claims",
        "FROM awareness_revisions",
        "INSERT INTO resources",
        "INSERT INTO awareness_revisions",
        "INSERT INTO operation_receipts",
        "INSERT INTO app_journal_entries",
    )
    leaked = [term for term in forbidden_sql if term in source]
    if leaked:
        raise AssertionError(f"mutation owner writes or queries another owner directly: {leaked}")


def _mutation_owner() -> str:
    _assert_mutation_owner((ROOT / "product/core/mutation.py").read_text(encoding="utf-8"))
    return "mutation owner orchestrates preview, approval, apply, measurement, verification, and refresh"


def _cli_entrance() -> str:
    source = (ROOT / "product/core/cli.py").read_text(encoding="utf-8")
    required = [
        'commands.add_parser("mutation")',
        'mutation_commands.add_parser("status")',
        'mutation_commands.add_parser("preview-write")',
        'mutation_commands.add_parser("approve")',
        'mutation_commands.add_parser("apply")',
        'mutation_commands.add_parser("history")',
        'mutation_commands.add_parser("links")',
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"mutation CLI entrance missing: {missing}")
    return "CLI exposes mutation status, preview, approve, apply, history, and links"


def _lower_layers_do_not_import_mutation() -> str:
    violations: list[str] = []
    for source in sorted((ROOT / "product").rglob("*.py")):
        if source.name in {"mutation.py", "cli.py"}:
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        for imported in _imports(tree):
            if imported == "core.mutation" or imported.startswith("core.mutation."):
                violations.append(f"{source.relative_to(ROOT).as_posix()} imports {imported}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "lower product layers do not depend upward on mutation governance"


def _environment_containment() -> str:
    source = (ROOT / "product/core/control.py").read_text(encoding="utf-8")
    required = [
        "def _child_environment(",
        "PYTHONPATH",
        "PYTHONDONTWRITEBYTECODE",
        "not name.startswith(\"SIDECAR_IDENTITY_\")",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"control-plane child environment lacks containment terms: {missing}")
    invoke = source[source.index("def invoke(") :]
    if "environment = dict(os.environ)" in invoke:
        raise AssertionError("invoke still gives child processes broad ambient environment")
    if "OPERATOR_TOKEN" in source:
        raise AssertionError("control-plane environment explicitly transports operator token")
    return "child process environment is allowlisted around explicit installed runtime context"


def _focused_t5_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t5_governed_mutation.py", "-q"])
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


def _no_out_of_scope_surfaces() -> str:
    forbidden = (
        "mcp",
        "gui",
        "embedding",
        "vector",
        "cartridge",
        "rollback",
        "workflow_engine",
        "planner",
    )
    violations: list[str] = []
    for source in sorted((ROOT / "product").rglob("*.py")):
        text = source.read_text(encoding="utf-8").lower()
        for term in forbidden:
            if term in text:
                violations.append(f"{source.relative_to(ROOT).as_posix()} mentions {term}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T5 introduces no MCP, GUI, AI/vector, cartridge, rollback, planner, or workflow-engine surface"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0037-t5-execution-start.md" not in entries:
        raise AssertionError("T5 execution start is not recorded")
    return f"journal is contiguous through {entries[-1]}"


def _assert_no_premature_apply(test_source: str) -> None:
    if "self.assertFalse((target / \"docs\" / \"note.txt\").exists())" not in test_source:
        raise AssertionError("preview fixture does not prove preview avoids mutation")


def _assert_binding(test_source: str) -> None:
    for term in ("approval_preview_mismatch", "preview_digest", "stale_target", "stale_basis"):
        if term not in test_source:
            raise AssertionError(f"tests do not discriminate approval/stale binding term: {term}")


def _assert_independent_measurement(mutation_source: str) -> None:
    if "independent_target_snapshot" not in mutation_source:
        raise AssertionError("mutation record lacks independent measurement source")
    if "result_handle" in mutation_source and "changed_paths" not in mutation_source:
        raise AssertionError("mutation appears to rely on tool self-report instead of measurement")


def _assert_honest_verification(mutation_source: str) -> None:
    if '"unavailable"' not in mutation_source:
        raise AssertionError("verification unavailable state is missing")
    if "No target-native verification mechanism is available." not in mutation_source:
        raise AssertionError("unavailable verification lacks honest detail")


def _discrimination_witness() -> str:
    storage_source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    constants_source = (ROOT / "product/core/constants.py").read_text(encoding="utf-8")
    mutation_source = (ROOT / "product/core/mutation.py").read_text(encoding="utf-8")
    tests_source = (ROOT / "tests/test_t5_governed_mutation.py").read_text(encoding="utf-8")
    control_source = (ROOT / "product/core/control.py").read_text(encoding="utf-8")

    missing_v5_table = storage_source.replace("CREATE TABLE mutation_previews", "CREATE TABLE missing_previews")
    bad_stamp = storage_source.replace("PRAGMA user_version = 3", "PRAGMA user_version = 5", 1)
    direct_t3_write = mutation_source + "\n# INSERT INTO resources\n"
    no_preview_witness = tests_source.replace(
        'self.assertFalse((target / "docs" / "note.txt").exists())',
        "self.assertTrue(True)",
    )
    weak_binding = tests_source.replace("approval_preview_mismatch", "some_other_error")
    self_report_measurement = mutation_source.replace("independent_target_snapshot", "tool_result")
    fake_pass_verification = mutation_source.replace('"unavailable"', '"passed"')
    broad_environment = control_source.replace(
        "environment = _child_environment(self.context)",
        "environment = dict(os.environ)",
    )

    witnessed: list[str] = []
    mutations: tuple[tuple[str, Callable[[], None]], ...] = (
        ("missing T5 table", lambda: _assert_t5_schema(missing_v5_table, constants_source)),
        ("migration branch stamps future version", lambda: _assert_t5_schema(bad_stamp, constants_source)),
        ("mutation owner writes T3 table", lambda: _assert_mutation_owner(direct_t3_write)),
        ("preview applies during preview witness absent", lambda: _assert_no_premature_apply(no_preview_witness)),
        ("weak approval/stale binding witness", lambda: _assert_binding(weak_binding)),
        ("tool self-report used as measurement", lambda: _assert_independent_measurement(self_report_measurement)),
        ("verification unavailable converted to pass", lambda: _assert_honest_verification(fake_pass_verification)),
        ("broad child process environment", lambda: _assert_child_environment_source(broad_environment)),
    )
    for label, function in mutations:
        try:
            function()
        except AssertionError:
            witnessed.append(label)
        else:
            raise AssertionError(f"discrimination accepted {label}")
    return "rejected: " + "; ".join(witnessed)


def _assert_child_environment_source(source: str) -> None:
    if "environment = dict(os.environ)" in source[source.index("def invoke(") :]:
        raise AssertionError("child launch inherits ambient environment")


def _repository_hygiene() -> str:
    forbidden = {"__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist", "release"}
    debris: list[str] = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".builder/evidence" in path.as_posix():
            continue
        if "_projectmapper" in path.parts:
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
    parser = argparse.ArgumentParser(description="Run the authoritative T5 mutation gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T5",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("t5_schema", _t5_schema),
        _check("mutation_owner", _mutation_owner),
        _check("cli_entrance", _cli_entrance),
        _check("lower_layers_do_not_import_mutation", _lower_layers_do_not_import_mutation),
        _check("environment_containment", _environment_containment),
        _check("focused_t5_product_evidence", _focused_t5_product_evidence),
        _check("canonical_product_regression", _canonical_product_regression),
        _check("positive_product_boundary", _product_boundary),
        _check("no_out_of_scope_surfaces", _no_out_of_scope_surfaces),
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
    evidence_path = evidence_directory / "t5-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T5-governed-mutation",
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
