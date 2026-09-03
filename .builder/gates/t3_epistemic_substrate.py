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
T3_TABLES = {
    "resources",
    "resource_versions",
    "observations",
    "epistemic_evidence",
    "claims",
    "relations",
}
FORBIDDEN_T3_TERMS = {
    "awareness_revisions",
    "embeddings",
    "vector_index",
    "mcp",
    "gui",
    "cartridges",
}
POST_T3_TERMS_ALLOWED_BY_PARKED_TRANCHES = {
    "awareness_revisions",  # introduced by parked T4 Awareness
}
POST_T3_MCP_ALLOWED_FILES = {
    "product/core/cli.py",  # CLI gained an MCP entrance in parked T6
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


def _assert_t3_schema(source: str, *, t4_has_started: bool = False) -> None:
    tables = _storage_tables(source)
    missing = sorted(T3_TABLES - set(tables))
    if missing:
        raise AssertionError(f"T3 substrate tables missing: {missing}")
    duplicates = sorted(table for table in set(tables) if tables.count(table) > 1)
    if duplicates:
        raise AssertionError(f"substrate tables are collapsed or duplicated: {duplicates}")
    forbidden = sorted(term for term in FORBIDDEN_T3_TERMS if f"CREATE TABLE {term}" in source)
    if t4_has_started:
        forbidden = [term for term in forbidden if term != "awareness_revisions"]
    if forbidden:
        raise AssertionError(f"T3 storage declares deferred projection/domain tables: {forbidden}")


def _t3_schema() -> str:
    storage_source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    constants_source = (ROOT / "product/core/constants.py").read_text(encoding="utf-8")
    match = re.search(r"DATABASE_SCHEMA_VERSION\s*=\s*(\d+)", constants_source)
    if not match or int(match.group(1)) < 3:
        raise AssertionError("database schema version no longer includes T3 schema")
    _assert_t3_schema(
        storage_source,
        t4_has_started="awareness_revisions" in POST_T3_TERMS_ALLOWED_BY_PARKED_TRANCHES,
    )
    return "current schema includes distinct T3 resource, evidence, claim, and relation tables"


def _assert_substrate_owner(source: str) -> None:
    required = [
        "def refresh(",
        "def list_resources(",
        "def read_resource(",
        "def list_versions(",
        "def list_observations(",
        "def read_evidence(",
        "def list_claims(",
        "def trace(",
        "epistemic_evidence",
        "resource_versions",
        "derived_from",
        "supported_by",
        "concerns",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"substrate owner lacks required operations/relations: {missing}")
    forbidden = [term for term in ("operational_artifacts", "app_journal_entries", ".builder")]
    leaked = [term for term in forbidden if term in source]
    if leaked:
        raise AssertionError(f"substrate owner writes or references non-epistemic owners: {leaked}")


def _substrate_owner() -> str:
    source = (ROOT / "product/core/substrate.py").read_text(encoding="utf-8")
    _assert_substrate_owner(source)
    return "substrate owner exposes refresh, lookup, immutable evidence, claims, and trace"


def _cli_entrance() -> str:
    source = (ROOT / "product/core/cli.py").read_text(encoding="utf-8")
    required = [
        'commands.add_parser("substrate")',
        'substrate_commands.add_parser("refresh")',
        'substrate_commands.add_parser("resources")',
        'substrate_commands.add_parser("versions")',
        'substrate_commands.add_parser("observations")',
        'substrate_commands.add_parser("evidence")',
        'substrate_commands.add_parser("claims")',
        'substrate_commands.add_parser("trace")',
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"substrate CLI entrance missing: {missing}")
    return "CLI exposes minimal substrate refresh and inspection commands"


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


def _focused_t3_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t3_epistemic_substrate.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _canonical_product_regression() -> str:
    process = _run([sys.executable, "-m", "pytest", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


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


def _no_t4_or_out_of_scope_surfaces() -> str:
    source_paths = [
        ROOT / "product/core/storage.py",
        ROOT / "product/core/substrate.py",
        ROOT / "product/core/cli.py",
    ]
    violations: list[str] = []
    for source in source_paths:
        text = source.read_text(encoding="utf-8").lower()
        for term in FORBIDDEN_T3_TERMS:
            if term in POST_T3_TERMS_ALLOWED_BY_PARKED_TRANCHES:
                continue
            if term == "mcp" and source.relative_to(ROOT).as_posix() in POST_T3_MCP_ALLOWED_FILES:
                continue
            if term in text:
                violations.append(f"{source.relative_to(ROOT).as_posix()} mentions {term}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T3 introduces no awareness, vector, MCP, GUI, or cartridge authority"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0023-t3-execution-start.md" not in entries:
        raise AssertionError("T3 execution start is not recorded")
    return f"journal is contiguous through {entries[-1]}"


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


def _assert_no_receipt_journal_collapse(substrate_source: str) -> None:
    forbidden = ("operational_artifacts", "operation_receipts", "app_journal_entries")
    leaked = [term for term in forbidden if term in substrate_source]
    if leaked:
        raise AssertionError(f"substrate collapsed into non-epistemic tables: {leaked}")


def _assert_claim_provenance(substrate_source: str) -> None:
    claim_index = substrate_source.index("INSERT INTO claims")
    derived_index = substrate_source.find('predicate="derived_from"', claim_index)
    if derived_index == -1:
        raise AssertionError("claims can be inserted without derived_from provenance")


def _assert_version_immutability(substrate_source: str) -> None:
    if "INSERT OR IGNORE INTO resource_versions" not in substrate_source:
        raise AssertionError("resource versions are not immutable append/ignore records")
    if "UPDATE resource_versions" in substrate_source:
        raise AssertionError("resource versions can be overwritten")


def _discrimination_witness() -> str:
    storage_source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    substrate_source = (ROOT / "product/core/substrate.py").read_text(encoding="utf-8")

    collapsed_storage = storage_source.replace("resource_versions", "resources")
    operational_evidence = substrate_source.replace("epistemic_evidence", "operational_artifacts")
    no_derived_claim = substrate_source.replace('predicate="derived_from"', 'predicate="related_to"')
    mutable_versions = substrate_source.replace("INSERT OR IGNORE INTO resource_versions", "UPDATE resource_versions")
    awareness_storage = storage_source + "\nCREATE TABLE awareness_revisions (id TEXT)\n"

    witnessed: list[str] = []
    for label, function in (
        ("resource/version table collapse", lambda: _assert_t3_schema(collapsed_storage)),
        (
            "epistemic evidence stored as operational artifact",
            lambda: _assert_no_receipt_journal_collapse(operational_evidence),
        ),
        ("claim without derived_from provenance", lambda: _assert_claim_provenance(no_derived_claim)),
        ("mutable resource versions", lambda: _assert_version_immutability(mutable_versions)),
        ("awareness table introduced in T3", lambda: _assert_t3_schema(awareness_storage)),
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
    parser = argparse.ArgumentParser(description="Run the authoritative T3 substrate gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T3",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("t3_schema", _t3_schema),
        _check("substrate_owner", _substrate_owner),
        _check("cli_entrance", _cli_entrance),
        _check("t1_dependency_boundary", _t1_dependency_boundary),
        _check("focused_t3_product_evidence", _focused_t3_product_evidence),
        _check("canonical_product_regression", _canonical_product_regression),
        _check("positive_product_boundary", _product_boundary),
        _check("no_t4_or_out_of_scope_surfaces", _no_t4_or_out_of_scope_surfaces),
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
    evidence_path = evidence_directory / "t3-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T3-epistemic-substrate",
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
