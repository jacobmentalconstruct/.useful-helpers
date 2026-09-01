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


def _t7_substrate_owner() -> str:
    source = (ROOT / "product/core/substrate.py").read_text(encoding="utf-8")
    required = [
        "def _domain_signal(",
        "def _insert_domain_claims(",
        "target_profile_software",
        "target_profile_records_documents",
        "target_has_weak_material",
        "metadata_only",
        "unparsed document body",
        "vendor/dependency-like",
        "large file",
        "domain_signal",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"T7 substrate domain owner terms missing: {missing}")
    return "substrate owns deterministic domain signals, claims, evidence, and relations"


def _t7_awareness_projection() -> str:
    source = (ROOT / "product/core/awareness.py").read_text(encoding="utf-8")
    required = [
        "def _domain_profile(",
        "domain_profile",
        "target_profile_software",
        "target_profile_records_documents",
        "target_has_weak_material",
        "weak material",
        "metadata-only",
        "substrate.current_awareness_basis(context)",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"T7 awareness projection terms missing: {missing}")
    for table in ("resources", "observations", "claims", "epistemic_evidence", "relations"):
        if re.search(rf"\b(?:FROM|JOIN|INTO|UPDATE|DELETE FROM)\s+{table}\b", source, re.I):
            raise AssertionError(f"awareness directly queries T3-owned table: {table}")
    return "awareness projects domain truth through substrate APIs and owns no T3 tables"


def _focused_t7_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t7_domain_truth.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _canonical_product_regression() -> str:
    process = _run([sys.executable, "-m", "pytest", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _dependency_direction() -> str:
    violations: list[str] = []
    for source in sorted((ROOT / "product/tools").glob("*/tool.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        imports = _imports(tree)
        forbidden = [
            item
            for item in imports
            if item.startswith("core.awareness")
            or item.startswith("core.mcp")
            or item.startswith("core.mutation")
            or item.startswith("core.substrate")
            or item.startswith("core.runtime_records")
            or item.startswith("core.app_journal")
        ]
        if forbidden:
            violations.append(f"{source.relative_to(ROOT).as_posix()} imports {forbidden}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "mechanical tools do not depend upward on domain truth, awareness, MCP, mutation, receipts, or journal"


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
    t7_sources = [
        ROOT / "product/core/substrate.py",
        ROOT / "product/core/awareness.py",
    ]
    forbidden = (
        "embedding",
        "vector",
        "cartridge",
        "ocr",
        "symbol_graph",
        "import_graph",
        "rollback",
        "workflow_engine",
        "local_ai",
        "semantic_summary",
    )
    violations: list[str] = []
    for source in t7_sources:
        text = source.read_text(encoding="utf-8").lower()
        for term in forbidden:
            if term in text:
                violations.append(f"{source.relative_to(ROOT).as_posix()} mentions {term}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T7 introduces no AI/vector, cartridge, parser graph, rollback, or workflow-engine surface"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0046-t7-execution-start.md" not in entries:
        raise AssertionError("T7 execution start is not recorded")
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


def _assert_substrate_owner(source: str) -> None:
    for term in (
        "target_profile_software",
        "target_profile_records_documents",
        "target_has_weak_material",
        "domain_signal",
        "metadata_only",
    ):
        if term not in source:
            raise AssertionError(f"substrate owner missing {term}")


def _assert_awareness_projection(source: str) -> None:
    if "substrate.current_awareness_basis(context)" not in source:
        raise AssertionError("awareness does not consume T3 current basis")
    for table in ("resources", "observations", "claims", "epistemic_evidence", "relations"):
        if re.search(rf"\b(?:FROM|JOIN|INTO|UPDATE|DELETE FROM)\s+{table}\b", source, re.I):
            raise AssertionError(f"awareness directly queries T3 table {table}")


def _assert_t7_tests(source: str) -> None:
    required = [
        "test_unobserved_and_observed_empty_are_not_collapsed",
        "test_substantial_software_fixture_produces_traceable_domain_truth",
        "test_mixed_records_documents_fixture_reports_limited_basis",
        "test_weak_material_fixture_does_not_overclaim_or_dominate_orientation",
        "test_current_domain_profile_does_not_leak_historical_software_shape",
        "test_domain_truth_does_not_create_runtime_memory_or_mutation_state",
        "test_cli_and_mcp_read_same_domain_world_without_owning_it",
        "node_modules",
        "large.dat",
        "metadata_only",
        "semantic_summary",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"T7 focused tests omit required witness terms: {missing}")


def _discrimination_witness() -> str:
    substrate_source = (ROOT / "product/core/substrate.py").read_text(encoding="utf-8")
    awareness_source = (ROOT / "product/core/awareness.py").read_text(encoding="utf-8")
    tests_source = (ROOT / "tests/test_t7_domain_truth.py").read_text(encoding="utf-8")
    witnessed: list[str] = []
    mutations: tuple[tuple[str, Callable[[], None]], ...] = (
        (
            "missing software claim",
            lambda: _assert_substrate_owner(substrate_source.replace("target_profile_software", "")),
        ),
        (
            "missing records/documents claim",
            lambda: _assert_substrate_owner(
                substrate_source.replace("target_profile_records_documents", "")
            ),
        ),
        (
            "missing weak-material claim",
            lambda: _assert_substrate_owner(substrate_source.replace("target_has_weak_material", "")),
        ),
        (
            "awareness direct T3 table query",
            lambda: _assert_awareness_projection(awareness_source + "\n# SELECT * FROM claims\n"),
        ),
        (
            "awareness skips substrate basis",
            lambda: _assert_awareness_projection(
                awareness_source.replace("substrate.current_awareness_basis(context)", "{}")
            ),
        ),
        (
            "missing weak-material fixture",
            lambda: _assert_t7_tests(tests_source.replace("node_modules", "ordinary_folder")),
        ),
        (
            "missing overclaim guard",
            lambda: _assert_t7_tests(tests_source.replace("semantic_summary", "summary")),
        ),
        (
            "missing MCP/CLI shared-world witness",
            lambda: _assert_t7_tests(
                tests_source.replace("test_cli_and_mcp_read_same_domain_world_without_owning_it", "")
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
    parser = argparse.ArgumentParser(description="Run the authoritative T7 domain truth gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T7",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("t7_substrate_owner", _t7_substrate_owner),
        _check("t7_awareness_projection", _t7_awareness_projection),
        _check("focused_t7_product_evidence", _focused_t7_product_evidence),
        _check("canonical_product_regression", _canonical_product_regression),
        _check("dependency_direction", _dependency_direction),
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
    evidence_path = evidence_directory / "t7-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T7-domain-truth",
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
