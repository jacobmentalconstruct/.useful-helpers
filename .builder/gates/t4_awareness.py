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
T4_TABLES = {"awareness_revisions", "awareness_items"}
T3_TABLES = {
    "resources",
    "resource_versions",
    "observations",
    "epistemic_evidence",
    "claims",
    "relations",
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
        elif isinstance(node, ast.ImportFrom):
            imported.extend(alias.name for alias in node.names)
    return imported


def _storage_tables(source: str) -> list[str]:
    return re.findall(r"CREATE TABLE\s+([a-z_]+)", source)


def _t4_schema() -> str:
    storage_source = (ROOT / "product/core/storage.py").read_text(encoding="utf-8")
    constants_source = (ROOT / "product/core/constants.py").read_text(encoding="utf-8")
    if "DATABASE_SCHEMA_VERSION = 4" not in constants_source:
        raise AssertionError("database schema version was not advanced to 4")
    tables = _storage_tables(storage_source)
    missing = sorted(T4_TABLES - set(tables))
    if missing:
        raise AssertionError(f"T4 awareness tables missing: {missing}")
    for table in T4_TABLES:
        if tables.count(table) != 1:
            raise AssertionError(f"T4 table is missing or duplicated: {table}")
    return "schema version 4 declares distinct awareness revision and item tables"


def _awareness_owner() -> str:
    source_path = ROOT / "product/core/awareness.py"
    source = source_path.read_text(encoding="utf-8")
    required = [
        "def refresh(",
        "def current(",
        "def list_revisions(",
        "def read_revision(",
        "def drill(",
        "awareness:",
        "current_awareness_basis",
        "target_signature",
        "basis_status",
        "unknown",
        "stale",
        "substrate.",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"awareness owner lacks required behavior: {missing}")
    forbidden = ["operational_artifacts", "app_journal_entries", "operation_receipts"]
    leaked = [term for term in forbidden if term in source]
    if leaked:
        raise AssertionError(f"awareness owner collapsed into T2/App Journal tables: {leaked}")
    for table in T3_TABLES:
        if re.search(rf"\b(?:FROM|JOIN|INTO|UPDATE|DELETE FROM)\s+{table}\b", source, re.I):
            raise AssertionError(f"awareness owner directly queries T3-owned table: {table}")
    tree = ast.parse(source, filename=str(source_path))
    imports = _imports(tree)
    if (
        "substrate" not in imports
        and "core.substrate" not in imports
        and not any(item.startswith("product.core.substrate") for item in imports)
    ):
        raise AssertionError("awareness owner does not consume the substrate owner")
    return "awareness owner projects through substrate APIs and owns only awareness records"


def _cli_entrance() -> str:
    source = (ROOT / "product/core/cli.py").read_text(encoding="utf-8")
    required = [
        'commands.add_parser("awareness")',
        'awareness_commands.add_parser("status")',
        'awareness_commands.add_parser("refresh")',
        'awareness_commands.add_parser("current")',
        'awareness_commands.add_parser("revisions")',
        'awareness_commands.add_parser("drill")',
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"awareness CLI entrance missing: {missing}")
    return "CLI exposes minimal awareness status, refresh, current, revisions, and drill commands"


def _lower_layers_do_not_import_awareness() -> str:
    violations: list[str] = []
    for source in sorted((ROOT / "product").rglob("*.py")):
        if source.name == "awareness.py":
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        imports = _imports(tree)
        if source.name == "cli.py":
            imports = [item for item in imports if item != "core.awareness"]
        leaked = [
            item
            for item in imports
            if item == "core.awareness" or item.startswith("core.awareness.")
        ]
        if leaked:
            violations.append(f"{source.relative_to(ROOT).as_posix()} imports {leaked}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "lower product layers do not depend upward on awareness"


def _focused_t4_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t4_awareness.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _basis_freshness_behavior() -> str:
    tests = [
        "tests/test_t4_awareness.py::"
        "T4AwarenessTests::test_t3_basis_mismatch_is_stale_during_awareness_refresh",
        "tests/test_t4_awareness.py::"
        "T4AwarenessTests::test_latest_empty_basis_does_not_leak_historical_resources_or_claims",
    ]
    process = _run([sys.executable, "-m", "pytest", *tests, "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return "behavioral basis/freshness witnesses passed for mismatch and latest-empty refresh"


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


def _no_out_of_scope_surfaces() -> str:
    forbidden = ("mcp", "gui", "embedding", "vector", "preview", "approve", "verification_workflow")
    violations: list[str] = []
    for source in [ROOT / "product/core/awareness.py", ROOT / "product/core/storage.py"]:
        text = source.read_text(encoding="utf-8").lower()
        for term in forbidden:
            if term in text:
                violations.append(f"{source.relative_to(ROOT).as_posix()} mentions {term}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T4 introduces no MCP, GUI, vector, local-AI, cartridge, or mutation-governance surface"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0028-t4-execution-start.md" not in entries:
        raise AssertionError("T4 execution start is not recorded")
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


def _assert_awareness_owner(source: str) -> None:
    if "UPDATE awareness_revisions" in source:
        raise AssertionError("awareness revisions can be overwritten")
    if "awareness:" not in source or "revision:" in source:
        raise AssertionError("awareness does not use one canonical awareness: handle")
    for table in T3_TABLES:
        if re.search(rf"\b(?:FROM|JOIN|INTO|UPDATE|DELETE FROM)\s+{table}\b", source, re.I):
            raise AssertionError(f"awareness directly queries T3 table {table}")
    if "no substrate observations exist" not in source:
        raise AssertionError("awareness can fabricate rich orientation without substrate basis")
    if '"stale"' not in source:
        raise AssertionError("awareness lacks stale freshness path")


def _discrimination_witness() -> str:
    source = (ROOT / "product/core/awareness.py").read_text(encoding="utf-8")
    witnessed: list[str] = []
    mutations = {
        "mutable awareness revision": source + "\n# UPDATE awareness_revisions\n",
        "direct T3 table query": source + "\n# SELECT * FROM resources\n",
        "generic revision handle": source.replace("awareness:", "revision:"),
        "missing unknown-basis guard": source.replace("no substrate observations exist", "substrate observed rich target"),
        "missing stale freshness": source.replace('"stale"', '"current"'),
    }
    for label, mutated in mutations.items():
        try:
            _assert_awareness_owner(mutated)
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
    parser = argparse.ArgumentParser(description="Run the authoritative T4 awareness gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T4",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("t4_schema", _t4_schema),
        _check("awareness_owner", _awareness_owner),
        _check("cli_entrance", _cli_entrance),
        _check("lower_layers_do_not_import_awareness", _lower_layers_do_not_import_awareness),
        _check("basis_freshness_behavior", _basis_freshness_behavior),
        _check("focused_t4_product_evidence", _focused_t4_product_evidence),
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
    evidence_path = evidence_directory / "t4-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T4-awareness",
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
