from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_TOOLS = {"hash_file", "inventory", "read_file", "search_text", "write_file"}


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


def _manifest_contracts() -> str:
    discovered: set[str] = set()
    weak_outputs: list[str] = []
    for source in sorted((ROOT / "product/tools").glob("*/manifest.json")):
        document = json.loads(source.read_text(encoding="utf-8"))
        tool_id = document["id"]
        discovered.add(tool_id)
        output = document["output_schema"]
        properties = output.get("properties", {})
        if set(properties) <= {"ok"} or output.get("additionalProperties") is not False:
            weak_outputs.append(tool_id)
        required = {
            "id",
            "description",
            "authority",
            "input_schema",
            "output_schema",
            "reads",
            "writes",
            "applicability",
            "path_arguments",
            "invocation",
        }
        missing = sorted(required - document.keys())
        if missing:
            raise AssertionError(f"{tool_id} manifest omits {missing}")
    if discovered != EXPECTED_TOOLS:
        raise AssertionError(f"expected five declared tools, found {sorted(discovered)}")
    if weak_outputs:
        raise AssertionError(f"output schemas do not constrain successful result fields: {weak_outputs}")
    return "five manifests own explicit input/output, authority, domain, and invocation contracts"


def _imports(tree: ast.AST) -> list[str]:
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.extend(f"{node.module}.{alias.name}" for alias in node.names)
    return imported


def _blocked_tool_core_imports(tree: ast.AST) -> list[str]:
    return sorted(
        module
        for module in _imports(tree)
        if (module == "core" or module.startswith("core."))
        and module != "core.tool_runtime"
        and not module.startswith("core.tool_runtime.")
    )


def _assert_core_dependency_direction(
    runtime: tuple[str, ast.AST], tools: list[tuple[str, ast.AST]]
) -> None:
    violations: list[str] = []
    runtime_label, runtime_tree = runtime
    runtime_core_imports = sorted(
        module for module in _imports(runtime_tree) if module == "core" or module.startswith("core.")
    )
    runtime_relative_imports = [
        node for node in ast.walk(runtime_tree) if isinstance(node, ast.ImportFrom) and node.level
    ]
    if runtime_core_imports or runtime_relative_imports:
        blocked = runtime_core_imports + ["relative core import"] * len(runtime_relative_imports)
        violations.append(f"{runtime_label}: {blocked}")

    for label, tree in tools:
        blocked = _blocked_tool_core_imports(tree)
        if blocked:
            violations.append(f"{label}: {blocked}")
    if violations:
        raise AssertionError("mechanical core dependency boundary violated: " + "; ".join(violations))


def _mechanical_dependency_direction() -> str:
    runtime_source = ROOT / "product/core/tool_runtime.py"
    tool_sources = sorted((ROOT / "product/tools").glob("*/tool.py"))
    runtime_tree = ast.parse(runtime_source.read_text(encoding="utf-8"), filename=str(runtime_source))
    tool_trees = [
        (source.relative_to(ROOT).as_posix(), ast.parse(source.read_text(encoding="utf-8"), filename=str(source)))
        for source in tool_sources
    ]
    _assert_core_dependency_direction(
        (runtime_source.relative_to(ROOT).as_posix(), runtime_tree), tool_trees
    )
    identity_terms = [
        source.relative_to(ROOT).as_posix()
        for source in [runtime_source, *tool_sources]
        if any(term in source.read_text(encoding="utf-8") for term in ("instance_uuid", "instance_root"))
    ]
    if identity_terms:
        raise AssertionError(f"mechanical layer contains installed-identity terms: {identity_terms}")
    return "tools import only core.tool_runtime; shared runtime imports no higher core subsystem"


def _dependency_rule_discrimination() -> str:
    runtime_source = ROOT / "product/core/tool_runtime.py"
    runtime_text = runtime_source.read_text(encoding="utf-8")
    runtime_tree = ast.parse(runtime_text, filename=str(runtime_source))
    baseline_tool = ROOT / "product/tools/hash_file/tool.py"
    baseline_text = baseline_tool.read_text(encoding="utf-8")
    baseline_tool_tree = ast.parse(baseline_text, filename=str(baseline_tool))
    witnessed: list[str] = []
    for dependency in ("core.containment", "core.contracts", "core.instance"):
        tool_mutation = ast.parse(
            baseline_text + f"\nimport {dependency}\n", filename=str(baseline_tool)
        )
        runtime_mutation = ast.parse(
            runtime_text + f"\nimport {dependency}\n", filename=str(runtime_source)
        )
        cases = (
            (runtime_tree, tool_mutation, "tool"),
            (runtime_mutation, baseline_tool_tree, "shared runtime"),
        )
        for candidate_runtime, candidate_tool, surface in cases:
            try:
                _assert_core_dependency_direction(
                    (runtime_source.relative_to(ROOT).as_posix(), candidate_runtime),
                    [(baseline_tool.relative_to(ROOT).as_posix(), candidate_tool)],
                )
            except AssertionError as exc:
                if dependency not in str(exc):
                    raise AssertionError(
                        f"{surface} mutation failed without identifying {dependency}: {exc}"
                    ) from exc
            else:
                raise AssertionError(f"dependency assertion accepted {surface} {dependency}")
        witnessed.append(dependency)
    return "positive dependency assertion rejected tool/runtime mutations: " + ", ".join(witnessed)


def _focused_product_evidence() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_t1_mechanical_host.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _consumer_regression() -> str:
    process = _run([sys.executable, "-m", "pytest", "tests/test_phase1.py", "-q"])
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


def _journal_and_authority_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0010-t1-execution-start.md" not in entries:
        raise AssertionError("T1 execution start is not recorded")
    if (ROOT / "tests/gates").exists():
        raise AssertionError("tests/gates competes with the sole .builder/gates authority")
    return f"journal is contiguous through {entries[-1]} and gate authority remains singular"


def _static_discovery() -> str:
    process = _run([sys.executable, "-m", "ruff", "check", ".", "--no-cache"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    parsed = 0
    for source in ROOT.rglob("*.py"):
        if ".git" in source.parts or ".builder/evidence" in source.as_posix():
            continue
        ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
        parsed += 1
    return f"Ruff passed and {parsed} Python sources parsed"


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
    parser = argparse.ArgumentParser(description="Run the authoritative T1 mechanical-host gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T1",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("manifest_contracts", _manifest_contracts),
        _check("mechanical_dependency_direction", _mechanical_dependency_direction),
        _check("dependency_rule_discrimination", _dependency_rule_discrimination),
        _check("focused_product_evidence", _focused_product_evidence),
        _check("consumer_regression", _consumer_regression),
        _check("positive_product_boundary", _product_boundary),
        _check("journal_and_authority_continuity", _journal_and_authority_continuity),
        _check("static_discovery", _static_discovery),
        _check("repository_hygiene", _repository_hygiene),
    ]
    passed = all(check.status == "PASS" for check in checks)
    recorded = datetime.now(timezone.utc)
    run_id = recorded.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence_directory = arguments.evidence_root.resolve() / run_id
    evidence_directory.mkdir(parents=True, exist_ok=False)
    evidence_path = evidence_directory / "t1-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T1-mechanical-host",
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
