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


def _imports(source: str, filename: str) -> list[str]:
    tree = ast.parse(source, filename=filename)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.extend(f"{node.module}.{alias.name}" for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level and node.module is None:
            imported.extend(alias.name for alias in node.names)
    return imported


def _t6_surfaces() -> str:
    cli = (ROOT / "product/core/cli.py").read_text(encoding="utf-8")
    host = (ROOT / "product/core/host.py").read_text(encoding="utf-8")
    mcp = ROOT / "product/core/mcp.py"
    if not mcp.exists():
        raise AssertionError("product/core/mcp.py is missing")
    if 'commands.add_parser("mcp")' not in cli:
        raise AssertionError("CLI does not expose the MCP entrance")
    if "from . import mcp" not in cli:
        raise AssertionError("CLI does not lazy-load the MCP adapter")
    first_import_block = cli.split("def _parser", 1)[0]
    if "mcp" in first_import_block:
        raise AssertionError("CLI imports MCP eagerly, weakening removability")
    if "def status(" not in host:
        raise AssertionError("host status owner is missing")
    return "T6 adds a lazy MCP CLI entrance, MCP adapter, and shared host status owner"


def _mcp_adapter_owner() -> str:
    source = (ROOT / "product/core/mcp.py").read_text(encoding="utf-8")
    required = [
        "def serve(",
        "def _tool_descriptors(",
        "def _tools_call(",
        "registry.discover(context)",
        "ControlPlane(context).invoke",
        "runtime_records.list_receipts",
        "app_journal.list_entries",
        "substrate.status",
        "awareness.current",
        "mutation.status",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"MCP adapter lacks required owner routing: {missing}")
    forbidden = (
        "sqlite3",
        "subprocess",
        "operation_receipts",
        "app_journal_entries",
        "FROM resources",
        "INSERT INTO resources",
        "UPDATE resources",
        "DELETE FROM resources",
        "awareness_revisions",
        "mutation_records",
        "product.tools",
    )
    leaked = [term for term in forbidden if term in source]
    if leaked:
        raise AssertionError(f"MCP adapter owns or bypasses lower state/capabilities: {leaked}")
    return "MCP adapter routes through registry, control plane, and existing state owners"


def _lower_layers_do_not_import_mcp() -> str:
    violations = _mcp_import_violations()
    if violations:
        raise AssertionError("; ".join(violations))
    return "CLI is the only non-MCP product module allowed to mention the MCP adapter"


def _mcp_import_violations(extra: dict[str, str] | None = None) -> list[str]:
    violations: list[str] = []
    for source in sorted((ROOT / "product").rglob("*.py")):
        relative = source.relative_to(ROOT).as_posix()
        if relative == "product/core/mcp.py":
            continue
        text = extra.get(relative) if extra else None
        if text is None:
            text = source.read_text(encoding="utf-8")
        imports = _imports(text, relative)
        if relative == "product/core/cli.py":
            top = text.split("def _parser", 1)[0]
            if "mcp" in top:
                violations.append("product/core/cli.py imports MCP eagerly")
            continue
        for imported in imports:
            if imported in {"mcp", "core.mcp", "product.core.mcp"} or imported.endswith(".mcp"):
                violations.append(f"{relative} imports {imported}")
    return violations


def _focused_t6_product_evidence() -> str:
    process = _run([sys.executable, "-B", "-m", "pytest", "tests/test_t6_mcp_entrance.py", "-q"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    return process.stdout.strip().splitlines()[-1]


def _canonical_product_regression() -> str:
    process = _run([sys.executable, "-B", "-m", "pytest", "-q"])
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
        for imported in _imports(source.read_text(encoding="utf-8"), str(source)):
            if imported.split(".", 1)[0] in blocked_roots:
                raise AssertionError(f"{source.relative_to(ROOT)} imports {imported}")
    return f"{scanned} product modules remain independent of factory, tests, and construction"


def _no_out_of_scope_surfaces() -> str:
    forbidden = (
        "gui",
        "embedding",
        "vector",
        "cartridge",
        "rollback",
        "workflow_engine",
        "planner",
        "local_ai",
    )
    violations: list[str] = []
    for source in sorted((ROOT / "product").rglob("*.py")):
        text = source.read_text(encoding="utf-8").lower()
        for term in forbidden:
            if term in text:
                violations.append(f"{source.relative_to(ROOT).as_posix()} mentions {term}")
    if violations:
        raise AssertionError("; ".join(violations))
    return "T6 introduces no GUI, AI/vector, cartridge, rollback, planner, or workflow-engine surface"


def _journal_continuity() -> str:
    entries = sorted(path.name for path in (ROOT / ".builder/journal").glob("*.md"))
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal sequence is not contiguous: {numbers}")
    if "0041-t6-execution-start.md" not in entries:
        raise AssertionError("T6 execution start is not recorded")
    return f"journal is contiguous through {entries[-1]}"


def _discrimination_witness() -> str:
    mcp_source = (ROOT / "product/core/mcp.py").read_text(encoding="utf-8")
    cli_source = (ROOT / "product/core/cli.py").read_text(encoding="utf-8")
    test_source = (ROOT / "tests/test_t6_mcp_entrance.py").read_text(encoding="utf-8")

    witnessed: list[str] = []
    mutations: tuple[tuple[str, Callable[[], None]], ...] = (
        (
            "hard-coded MCP catalog",
            lambda: _assert_mcp_adapter_owner(
                mcp_source.replace("registry.discover(context).values()", "[]")
            ),
        ),
        (
            "direct mechanical launch bypasses control plane",
            lambda: _assert_mcp_adapter_owner(
                mcp_source.replace("ControlPlane(context).invoke", "direct_tool.invoke")
            ),
        ),
        (
            "MCP-private SQL ownership",
            lambda: _assert_mcp_adapter_owner(mcp_source + "\n# SELECT * FROM operation_receipts\n"),
        ),
        (
            "CLI imports MCP eagerly",
            lambda: _assert_no_mcp_imports(
                {"product/core/cli.py": "from . import mcp\n" + cli_source}
            ),
        ),
        (
            "missing removability witness",
            lambda: _assert_removability_witness(
                test_source.replace("mcp_source.unlink()", "pass")
            ),
        ),
        (
            "missing malformed request witness",
            lambda: _assert_error_witness(test_source.replace("-32700", "-32000")),
        ),
        (
            "missing no automatic memory witness",
            lambda: _assert_no_memory_witness(test_source.replace('"entries"], []', '"entries"], response')),
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


def _assert_mcp_adapter_owner(source: str | None = None) -> None:
    original = ROOT / "product/core/mcp.py"
    text = source if source is not None else original.read_text(encoding="utf-8")
    required = ["registry.discover(context)", "ControlPlane(context).invoke"]
    missing = [term for term in required if term not in text]
    if missing:
        raise AssertionError(f"MCP owner routing missing: {missing}")
    forbidden = ("sqlite3", "subprocess", "operation_receipts", "app_journal_entries")
    leaked = [term for term in forbidden if term in text]
    if leaked:
        raise AssertionError(f"MCP owns or bypasses state: {leaked}")


def _assert_no_mcp_imports(extra: dict[str, str] | None = None) -> None:
    violations = _mcp_import_violations(extra)
    if violations:
        raise AssertionError("; ".join(violations))


def _assert_removability_witness(source: str) -> None:
    required = [
        "mcp_source.unlink()",
        'self.sidecar(target, "status")',
        'self.call(target, "read_file"',
        'self.sidecar(target, "receipts", "list")',
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"removability witness missing: {missing}")


def _assert_error_witness(source: str) -> None:
    for term in ("{not json", "-32700", "-32601"):
        if term not in source:
            raise AssertionError(f"MCP error witness missing: {term}")


def _assert_no_memory_witness(source: str) -> None:
    for term in ("mcp.sqlite3", 'journal["entries"], []', 'mutation_records"],\n            0'):
        if term not in source:
            raise AssertionError(f"MCP no-memory witness missing: {term}")


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
    parser = argparse.ArgumentParser(description="Run the authoritative T6 MCP entrance gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T6",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("t6_surfaces", _t6_surfaces),
        _check("mcp_adapter_owner", _mcp_adapter_owner),
        _check("lower_layers_do_not_import_mcp", _lower_layers_do_not_import_mcp),
        _check("focused_t6_product_evidence", _focused_t6_product_evidence),
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
    evidence_path = evidence_directory / "t6-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T6-mcp-entrance",
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
