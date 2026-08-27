from __future__ import annotations

import argparse
import ast
import json
import os
import platform
import re
import subprocess
import sys
import tomllib
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "60174bc93ef4a187a0cc7ff848a03b3d8772b804"


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


def _required_authorities() -> str:
    paths = [
        ".builder/BCC.md",
        ".builder/TRANCHE_PROTOCOL.md",
        ".builder/TRANCHE_PLAN.md",
        ".builder/CURRENT_STATE.md",
        ".builder/journal/0001-t0-declared.md",
        "docs/PRODUCT_CHARTER.md",
        "docs/ARCHITECTURE.md",
        "README.md",
        "pyproject.toml",
    ]
    missing = [path for path in paths if not (ROOT / path).is_file()]
    if missing:
        raise AssertionError(f"missing required authority surfaces: {missing}")
    return f"all {len(paths)} required surfaces exist"


def _authority_ownership() -> str:
    bcc = (ROOT / ".builder/BCC.md").read_text(encoding="utf-8")
    owners = {
        ".builder/BCC.md",
        "docs/PRODUCT_CHARTER.md",
        ".builder/TRANCHE_PROTOCOL.md",
        ".builder/TRANCHE_PLAN.md",
        "docs/ARCHITECTURE.md",
        ".builder/CURRENT_STATE.md",
        ".builder/journal/",
        ".builder/evidence/",
        ".builder/gates/",
        "tests/",
    }
    absent = sorted(owner for owner in owners if owner not in bcc)
    if absent:
        raise AssertionError(f"BCC authority map omits: {absent}")

    charter = (ROOT / "docs/PRODUCT_CHARTER.md").read_text(encoding="utf-8")
    for number in range(1, 9):
        if len(re.findall(rf"\*\*P{number} [^*]+:\*\*", charter)) != 1:
            raise AssertionError(f"P{number} must be defined exactly once in the Charter")

    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    architecture_headings = set(re.findall(r"^##\s+(.+?)\s*$", architecture, re.MULTILINE))
    charter_owned_architecture_sections = {
        "Product identity",
        "Invariants",
        "Product invariants",
        "Product topology",
        "Work loop",
        "Acceptance walk",
        "Product STOP",
        "Anti-goals",
        "Global non-goals",
    }
    duplicated = sorted(architecture_headings & charter_owned_architecture_sections)
    if duplicated:
        raise AssertionError(
            "Architecture declares Charter-owned normative sections: " + ", ".join(duplicated)
        )
    if "## Charter relationship" not in architecture:
        raise AssertionError("Architecture does not identify its Charter dependency")

    protocol = (ROOT / ".builder/TRANCHE_PROTOCOL.md").read_text(encoding="utf-8")
    if re.search(r"^##\s+Required loop\s*$", protocol, re.MULTILINE):
        raise AssertionError("Protocol reproduces the BCC-owned required workflow")
    if "## BCC workflow repository mapping" not in protocol:
        raise AssertionError("Protocol does not map BCC stages to repository mechanisms")

    plan = (ROOT / ".builder/TRANCHE_PLAN.md").read_text(encoding="utf-8")
    if re.search(r"^##\s+T0 declaration\s*$", plan, re.MULTILINE):
        raise AssertionError("Plan duplicates the journal-owned T0 declaration")
    duplicated_declaration_fields = re.findall(
        r"^(?:Outcome|Non-goals|Gate|Review evidence):", plan, re.MULTILINE
    )
    if duplicated_declaration_fields:
        raise AssertionError("Plan contains a duplicate T0 declaration body")
    journal_pointers = ("journal/0001-t0-declared.md", "journal/0002-t0-awaiting-approval.md")
    missing_pointers = [pointer for pointer in journal_pointers if pointer not in plan]
    if missing_pointers:
        raise AssertionError(f"Plan omits T0 journal pointers: {missing_pointers}")

    return "authority owners are singular and dependent documents use mappings or pointers"


def _vision_alignment() -> str:
    charter = (ROOT / "docs/PRODUCT_CHARTER.md").read_text(encoding="utf-8")
    normalized_charter = re.sub(r"\s+", " ", charter)
    charter_markers = (
        "Coherent Development is an independent product-neutral method",
        "host-resolved transported context",
        "mechanical tools",
        "Operational receipts/event ledger",
        "App Journal",
        "MCP is removable",
        "does not require extraction into separate distributions",
        "Runtime state and history ownership",
        "compatible updates preserve engagement-owned state",
    )
    missing_markers = [marker for marker in charter_markers if marker not in normalized_charter]
    if missing_markers:
        raise AssertionError(f"Charter omits vision-alignment markers: {missing_markers}")

    bcc = (ROOT / ".builder/BCC.md").read_text(encoding="utf-8")
    if "Coherent Development is an independent product-neutral method" not in bcc:
        raise AssertionError("BCC does not separate repository governance from the method")

    protocol = (ROOT / ".builder/TRANCHE_PROTOCOL.md").read_text(encoding="utf-8")
    stages = ("ORIENT", "DECLARE", "EXECUTE", "CONSOLIDATE", "VERIFY", "REVIEW", "PARK")
    absent_stages = [stage for stage in stages if f"| {stage} |" not in protocol]
    if absent_stages:
        raise AssertionError(f"Protocol omits Coherent Development stage mappings: {absent_stages}")

    plan = (ROOT / ".builder/TRANCHE_PLAN.md").read_text(encoding="utf-8")
    normalized_plan = re.sub(r"\s+", " ", plan)
    if "T1 Bound Hands" in plan:
        raise AssertionError("Plan retains identity-conflating T1 Bound Hands wording")
    plan_markers = (
        "T1 Mechanical Hands + Governed Host",
        "host-transported context",
        "without importing higher projections",
        "Runtime Receipts + Work Memory",
        "Removable MCP Entrance",
        "portable mechanical capability versus Sidecar-hosted governed use",
    )
    absent_plan_markers = [marker for marker in plan_markers if marker not in normalized_plan]
    if absent_plan_markers:
        raise AssertionError(f"Plan omits aligned tranche boundaries: {absent_plan_markers}")

    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    architecture_states = (
        "## Measured T1 separability debt",
        "## T1 mechanical-host seam realization",
    )
    if not any(marker in architecture for marker in architecture_states):
        raise AssertionError("Architecture records neither the provisional debt nor its T1 realization")

    forbidden_tool_imports = (
        "core.cli",
        "core.control",
        "core.instance",
        "core.registry",
        "core.storage",
        "awareness",
        "mcp",
        "gui",
        "factory",
    )
    tools = 0
    shared_runtime_users = 0
    for tool_path in sorted((ROOT / "product/tools").glob("*/tool.py")):
        tools += 1
        manifest_path = tool_path.with_name("manifest.json")
        if not manifest_path.is_file():
            raise AssertionError(f"tool lacks owning manifest: {tool_path.relative_to(ROOT)}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        required_contract = {
            "id",
            "description",
            "authority",
            "input_schema",
            "output_schema",
            "reads",
            "writes",
            "invocation",
        }
        missing_contract = sorted(required_contract - manifest.keys())
        if missing_contract:
            raise AssertionError(
                f"manifest {manifest_path.relative_to(ROOT)} omits contract fields: "
                f"{missing_contract}"
            )

        tree = ast.parse(tool_path.read_text(encoding="utf-8"), filename=str(tool_path))
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)
        if "core.tool_runtime" in imported_modules:
            shared_runtime_users += 1
        forbidden = sorted(
            module
            for module in imported_modules
            if any(module == prefix or module.startswith(prefix + ".") for prefix in forbidden_tool_imports)
        )
        if forbidden:
            raise AssertionError(
                f"mechanical tool imports higher Sidecar layers in {tool_path.relative_to(ROOT)}: "
                f"{forbidden}"
            )

    if not tools:
        raise AssertionError("no mechanical tools were measured")
    return (
        f"method/product/state boundaries declared; {tools} manifest-owned tools have no "
        f"forbidden upward imports ({shared_runtime_users} use the shared mechanical runtime)"
    )


def _baseline_provenance() -> str:
    _git("cat-file", "-e", f"{BASELINE}^{{commit}}")
    subject = _git("show", "-s", "--format=%s", BASELINE)
    if subject != "Preserve pre-bootstrap provisional prototype":
        raise AssertionError(f"unexpected baseline subject: {subject!r}")
    baseline_paths = _git("ls-tree", "-r", "--name-only", BASELINE).splitlines()
    if any(path.startswith(".builder/") for path in baseline_paths):
        raise AssertionError("pre-bootstrap baseline already contains builder governance")
    ancestor = _run(["git", "merge-base", "--is-ancestor", BASELINE, "HEAD"])
    if ancestor.returncode:
        raise AssertionError("pre-bootstrap baseline is not an ancestor of HEAD")
    tree = _git("rev-parse", f"{BASELINE}^{{tree}}")
    return f"baseline commit and tree preserved ({tree})"


def _journal_origin() -> str:
    journal = ROOT / ".builder/journal"
    entries = sorted(path.name for path in journal.glob("*.md"))
    if not entries or entries[0] != "0001-t0-declared.md":
        raise AssertionError(f"construction journal does not begin at T0: {entries}")
    numbers = [int(name.split("-", 1)[0]) for name in entries]
    if numbers != list(range(1, len(numbers) + 1)):
        raise AssertionError(f"journal numbering is not contiguous: {numbers}")
    return f"fresh construction journal begins at 0001 ({len(entries)} entries)"


def _one_gate_authority() -> str:
    if (ROOT / "tests/gates").exists():
        raise AssertionError("tests/gates exists; .builder/gates must be the sole gate authority")
    gate_files = sorted(
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*.py")
        if "gate" in path.name.lower() or "gates" in path.parts
    )
    if ".builder/gates/t0_bootstrap.py" not in gate_files:
        raise AssertionError("the authoritative T0 gate is missing")
    if any(not path.startswith(".builder/gates/") for path in gate_files):
        raise AssertionError(f"unexpected gate implementation locations: {gate_files}")
    return f"all {len(gate_files)} gate implementations are owned by .builder/gates"


def _product_boundary() -> str:
    forbidden_imports = {"factory", "tests", ".builder"}
    scanned = 0
    for path in sorted((ROOT / "product").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        scanned += 1
        for node in ast.walk(tree):
            imported: str | None = None
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in forbidden_imports:
                        raise AssertionError(f"product imports {alias.name!r} in {path}")
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = node.module.split(".", 1)[0]
            if imported in forbidden_imports:
                raise AssertionError(f"product imports {node.module!r} in {path}")

    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    if "build-system" in configuration or "setuptools" in configuration.get("tool", {}):
        raise AssertionError("T0 must not choose a build backend or setuptools artifact shape")
    if configuration.get("project", {}).get("scripts"):
        raise AssertionError("T0 must not declare artifact-specific installed scripts")
    return f"{scanned} product modules are independent of factory/tests/builder; artifact undecided"


def _journal_separation() -> str:
    charter = (ROOT / "docs/PRODUCT_CHARTER.md").read_text(encoding="utf-8")
    normalized_charter = re.sub(r"\s+", " ", charter)
    required = (
        ".builder/journal/",
        "product journal",
        "begins empty",
        "Neither journal stores or projects the other",
    )
    absent = [phrase for phrase in required if phrase not in normalized_charter]
    if absent:
        raise AssertionError(f"Charter does not establish journal separation: {absent}")
    return "construction and product journals have distinct subjects, stores, and lifecycles"


def _provisional_status() -> str:
    plan = (ROOT / ".builder/TRANCHE_PLAN.md").read_text(encoding="utf-8")
    phase = (ROOT / "docs/PHASE_1.md").read_text(encoding="utf-8")
    architecture = (ROOT / "docs/ARCHITECTURE.md").read_text(encoding="utf-8")
    if "T0 grants no P1-P8 credit" not in plan:
        raise AssertionError("Plan grants or obscures product credit during T0")
    if "PRE-BOOTSTRAP PROVISIONAL REPORT" not in phase:
        raise AssertionError("pre-bootstrap Phase 1 report is not labeled provisional")
    allowed_statuses = (
        "PROVISIONAL UNTIL T1",
        "T1 IMPLEMENTATION REVIEW CANDIDATE",
        "T1 PARKED BY OPERATOR APPROVAL",
        "T2 IMPLEMENTATION REVIEW CANDIDATE",
        "T2 PARKED IMPLEMENTATION MAP",
        "T3 IMPLEMENTATION REVIEW CANDIDATE",
        "T3 PARKED IMPLEMENTATION MAP",
        "T4 IMPLEMENTATION REVIEW CANDIDATE",
        "T4 PARKED IMPLEMENTATION MAP",
    )
    if not any(status in architecture for status in allowed_statuses):
        raise AssertionError("implementation architecture has no recognized lifecycle status")
    return "pre-bootstrap history remains provisional while architecture may advance by tranche"


def _reference_independence() -> str:
    forbidden = (
        ".useful-helpers-sidecar",
        ".useful-helpers-workbench",
        "c:\\jacob\\_appdesign\\_sandbox",
    )
    violations: list[str] = []
    for path in sorted((ROOT / "product").rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".py", ".json", ".md", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace").lower()
        if any(marker in text for marker in forbidden):
            violations.append(path.relative_to(ROOT).as_posix())
    if violations:
        raise AssertionError(f"product contains parent/sandbox lineage: {violations}")
    return "product source contains no parent-project names or sandbox paths"


def _canonical_pytest() -> str:
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pytest_config = configuration.get("tool", {}).get("pytest", {}).get("ini_options", {})
    if pytest_config.get("testpaths") != ["tests"]:
        raise AssertionError("canonical pytest testpaths must be exactly ['tests']")
    if "no:cacheprovider" not in pytest_config.get("addopts", ""):
        raise AssertionError("canonical pytest entrance must not leave cache debris")
    process = _run([sys.executable, "-m", "pytest"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    summary = process.stdout.strip().splitlines()[-1] if process.stdout.strip() else "pytest passed"
    return summary


def _static_discovery() -> str:
    process = _run([sys.executable, "-m", "ruff", "check", ".", "--no-cache"])
    if process.returncode:
        raise AssertionError(process.stdout.strip() or process.stderr.strip())
    parsed = 0
    for path in ROOT.rglob("*.py"):
        if ".git" in path.parts:
            continue
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parsed += 1
    return f"Ruff passed and {parsed} Python files parsed successfully"


def _repository_hygiene() -> str:
    forbidden_directories = {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        "build",
        "dist",
        "release",
    }
    debris = []
    for path in ROOT.rglob("*"):
        if ".git" in path.parts or ".builder/evidence" in path.as_posix():
            continue
        if path.is_dir() and (path.name in forbidden_directories or path.name.endswith(".egg-info")):
            debris.append(path.relative_to(ROOT).as_posix())
    runtime = ROOT / "tests/.runtime"
    if runtime.exists() and any(runtime.iterdir()):
        debris.append("tests/.runtime (non-empty)")
    if debris:
        raise AssertionError(f"generated debris remains: {sorted(debris)}")
    return "no generated build, test-cache, bytecode, release, or non-empty fixture debris"


def _check(name: str, function: Callable[[], str]) -> Check:
    try:
        return Check(name=name, status="PASS", detail=function())
    except Exception as exc:
        return Check(name=name, status="FAIL", detail=f"{type(exc).__name__}: {exc}")


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the authoritative T0 bootstrap gate")
    parser.add_argument(
        "--evidence-root",
        type=Path,
        default=ROOT / ".builder/evidence/T0",
        help="directory beneath which a unique immutable run directory is created",
    )
    return parser.parse_args()


def main() -> int:
    arguments = _arguments()
    checks = [
        _check("required_authorities", _required_authorities),
        _check("authority_ownership", _authority_ownership),
        _check("vision_alignment", _vision_alignment),
        _check("baseline_provenance", _baseline_provenance),
        _check("journal_origin", _journal_origin),
        _check("one_gate_authority", _one_gate_authority),
        _check("positive_product_boundary", _product_boundary),
        _check("journal_separation", _journal_separation),
        _check("provisional_status", _provisional_status),
        _check("reference_independence", _reference_independence),
        _check("canonical_pytest", _canonical_pytest),
        _check("static_discovery", _static_discovery),
        _check("repository_hygiene", _repository_hygiene),
    ]
    passed = all(check.status == "PASS" for check in checks)
    recorded = datetime.now(timezone.utc)
    run_id = recorded.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    evidence_directory = arguments.evidence_root.resolve() / run_id
    evidence_directory.mkdir(parents=True, exist_ok=False)
    evidence_path = evidence_directory / "bootstrap-gate.json"
    evidence = {
        "schema_version": 1,
        "gate": "T0-bootstrap",
        "status": "PASS" if passed else "FAIL",
        "recorded_at": recorded.isoformat(),
        "run_id": run_id,
        "baseline_commit": BASELINE,
        "head_commit": _git("rev-parse", "HEAD"),
        "python": sys.version,
        "platform": platform.platform(),
        "checks": [asdict(check) for check in checks],
    }
    evidence_path.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    try:
        reported_evidence = evidence_path.relative_to(ROOT).as_posix()
    except ValueError:
        reported_evidence = evidence_path.as_posix()
    print(
        json.dumps(
            {
                "gate": evidence["gate"],
                "status": evidence["status"],
                "passed": sum(check.status == "PASS" for check in checks),
                "total": len(checks),
                "evidence": reported_evidence,
                "failures": [asdict(check) for check in checks if check.status == "FAIL"],
            },
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
