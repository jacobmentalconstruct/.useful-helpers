from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

# The gate imports the product owner in-process for executed known-answer checks; it must
# not leave bytecode behind that its own hygiene check would then reject.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FIXTURE_ROOT = (ROOT / "tests/.runtime").resolve()
PRODUCT_ROOT = ROOT / "product"


@dataclass(frozen=True)
class Check:
    name: str
    status: str
    detail: str


class _ScratchDirectory:
    def __init__(self, prefix: str) -> None:
        RUNTIME_FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
        self.path = Path(tempfile.mkdtemp(prefix=prefix, dir=RUNTIME_FIXTURE_ROOT))

    def __enter__(self) -> str:
        return str(self.path)

    def __exit__(self, exc_type, exc, traceback) -> None:
        _force_rmtree(self.path)


def _force_rmtree(path: Path) -> None:
    if not path.exists():
        return

    def fix_permissions(function, failed_path, exc_info) -> None:
        try:
            os.chmod(failed_path, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            function(failed_path)
        except OSError:
            raise exc_info[1]

    shutil.rmtree(path, onerror=fix_permissions)


def _scratch_directory(prefix: str) -> _ScratchDirectory:
    return _ScratchDirectory(prefix)


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
        "_GENERATED_PARTS",
        "_SOFTWARE_CONDITIONAL_PARTS",
        "def _profile_decision(",
        "def _text_documents_dominate(",
        "def _inventory_limitations(",
        "detected only through size and modification time",
        "not traversed",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"T7 substrate domain owner terms missing: {missing}")
    for kind in ("resource_version", "domain_signal"):
        body_start = source.index(f'kind="{kind}",\n')
        body_end = source.index("created_at=observed_at,", body_start)
        if '"observed_at": observed_at' in source[body_start:body_end]:
            raise AssertionError(f"{kind} evidence body embeds observed_at; evidence is not content-addressed")
    return "substrate owns deterministic domain signals, claims, evidence, and relations"


def _weak_material_metadata_only_boundary() -> str:
    source = (ROOT / "product/core/substrate.py").read_text(encoding="utf-8")
    required = [
        "def _observation_type(",
        "file_metadata",
        "record[\"domain\"] = _domain_signal(",
        "record[\"domain\"][\"content_basis\"] != \"metadata_only\"",
        "record[\"content_hash\"] = hashlib.sha256(path.read_bytes()).hexdigest()",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"metadata-only boundary terms missing: {missing}")
    domain_index = source.index("record[\"domain\"] = _domain_signal(")
    hash_index = source.index("record[\"content_hash\"] = hashlib.sha256(path.read_bytes()).hexdigest()")
    if hash_index < domain_index:
        raise AssertionError("content hash is computed before weak-material basis is known")
    return "weak metadata-only material is classified before optional content hashing"


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
        "def _truncation_limitations(",
        "def _inventory_limitations(",
        '"projection": projection',
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"T7 awareness projection terms missing: {missing}")
    for table in ("resources", "observations", "claims", "epistemic_evidence", "relations"):
        if re.search(rf"\b(?:FROM|JOIN|INTO|UPDATE|DELETE FROM)\s+{table}\b", source, re.I):
            raise AssertionError(f"awareness directly queries T3-owned table: {table}")
    return "awareness projects domain truth through substrate APIs and owns no T3 tables"


def _import_substrate():
    if str(PRODUCT_ROOT) not in sys.path:
        sys.path.insert(0, str(PRODUCT_ROOT))
    from core import substrate  # noqa: PLC0415  (gate imports the product owner it measures)

    return substrate


def _write_realistic_software_target(target: Path) -> None:
    (target / "pyproject.toml").write_text("[project]\nname = 'gate-demo'\n", encoding="utf-8")
    (target / "README.md").write_text("# gate demo\n", encoding="utf-8")
    (target / "LICENSE").write_text("MIT\n", encoding="utf-8")
    (target / "config.json").write_text('{"debug": false}\n', encoding="utf-8")
    (target / "NOTES.txt").write_text("todo\n", encoding="utf-8")
    (target / "data").mkdir()
    (target / "data" / "sample.json").write_text('{"rows": []}\n', encoding="utf-8")
    (target / "src").mkdir()
    (target / "src" / "app.py").write_text("def main():\n    return 1\n", encoding="utf-8")
    (target / "src" / "util.py").write_text("X = 1\n", encoding="utf-8")
    (target / "tests").mkdir()
    (target / "tests" / "test_app.py").write_text("def test():\n    assert True\n", encoding="utf-8")
    objects = target / ".git" / "objects" / "ab"
    objects.mkdir(parents=True)
    (target / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (objects / "cdef").write_bytes(b"x\x9c" + bytes(range(32)))
    vendor = target / "node_modules" / "pkg"
    vendor.mkdir(parents=True)
    (vendor / "index.js").write_text("module.exports = 1;\n", encoding="utf-8")


def _write_true_mixed_target(target: Path) -> None:
    (target / "tools").mkdir()
    (target / "tools" / "export.py").write_text("print(1)\n", encoding="utf-8")
    (target / "tools" / "clean.py").write_text("print(2)\n", encoding="utf-8")
    (target / "README.md").write_text("# records\n", encoding="utf-8")
    (target / "records").mkdir()
    (target / "records" / "a.csv").write_text("id\n1\n", encoding="utf-8")
    (target / "records" / "b.csv").write_text("id\n2\n", encoding="utf-8")
    (target / "contracts").mkdir()
    (target / "contracts" / "agreement.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")


def _write_notes_heavy_target(target: Path) -> None:
    (target / "notes").mkdir()
    for index in range(24):
        (target / "notes" / f"note{index}.md").write_text(f"# note {index}\n", encoding="utf-8")
    (target / "scripts").mkdir()
    (target / "scripts" / "export.py").write_text("print(1)\n", encoding="utf-8")
    (target / "scripts" / "index.py").write_text("print(2)\n", encoding="utf-8")


def _write_records_with_ordinary_folders_target(target: Path) -> None:
    for folder in ("vendor", "build"):
        (target / folder).mkdir()
        for index in range(3):
            (target / folder / f"doc{index}.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    (target / "invoices").mkdir()
    (target / "invoices" / "a.csv").write_text("id\n1\n", encoding="utf-8")


def _known_answer_profiles(substrate) -> dict[str, str]:
    """Execute the substrate's own classification against known-answer targets."""
    results: dict[str, str] = {}
    with _scratch_directory(prefix="t7-gate-") as scratch:
        for name, writer, expected in (
            ("realistic_software", _write_realistic_software_target, "software"),
            ("true_mixed", _write_true_mixed_target, "mixed"),
            ("notes_heavy", _write_notes_heavy_target, "mixed"),
            ("records_ordinary_folders", _write_records_with_ordinary_folders_target, "records_documents"),
        ):
            target = Path(scratch) / name
            target.mkdir()
            writer(target)
            context = SimpleNamespace(target_root=target, instance_root=target / ".sidecar")
            records = substrate._resource_records(context)
            handles = {record["handle"] for record in records}
            if name == "realistic_software":
                if "path:.git/" not in handles or "path:node_modules/" not in handles:
                    raise AssertionError("generated/vendor subtree roots are not recorded")
                nested = sorted(
                    handle
                    for handle in handles
                    if handle.startswith(("path:.git/", "path:node_modules/"))
                    and handle not in {"path:.git/", "path:node_modules/"}
                )
                if nested:
                    raise AssertionError(f"generated/vendor subtrees were traversed: {nested[:3]}")
                if any(record.get("content_hash") for record in records if record["domain"]["weak_material"]):
                    raise AssertionError("weak material carries a content hash")
            if name == "records_ordinary_folders" and "path:vendor/doc0.pdf" not in handles:
                raise AssertionError("ordinary vendor/build folders on a records target were not traversed")
            observations = [
                {
                    "observation_id": f"observation:{index}",
                    "evidence_id": f"evidence:{index}",
                    "resource_handle": record["handle"],
                    **record["domain"],
                }
                for index, record in enumerate(records)
                if record["domain"]["categories"] or record["domain"]["limitations"]
            ]
            by_category: dict[str, list[dict]] = {}
            for observation in observations:
                for category in observation["categories"]:
                    by_category.setdefault(category, []).append(observation)
            decision = substrate._profile_decision(
                software=by_category.get("software", []),
                documents=by_category.get("documents", []),
                records=by_category.get("records", []),
                config_data=by_category.get("config_data", []),
            )
            has_software = bool(by_category.get("software"))
            has_records_documents = bool(decision["records_documents"])
            if has_software and has_records_documents:
                profile = "mixed"
            elif has_software:
                profile = "software"
            elif has_records_documents:
                profile = "records_documents"
            else:
                profile = "generic_observed"
            results[name] = profile
            if profile != expected:
                raise AssertionError(f"{name} target classified {profile!r}, expected {expected!r}")
    return results


def _known_answer_domain_profiles() -> str:
    results = _known_answer_profiles(_import_substrate())
    return "; ".join(f"{name} -> {profile}" for name, profile in sorted(results.items()))


def _consumer_entrance_known_answer() -> str:
    """Prove the same answers through the installed consumer entrance, not internal imports."""
    with _scratch_directory(prefix="t7-gate-entrance-") as scratch:
        target = Path(scratch) / "software"
        target.mkdir()
        _write_realistic_software_target(target)
        attach = _run([sys.executable, "-B", "-m", "factory", "attach", str(target)])
        if attach.returncode:
            raise AssertionError(attach.stderr.strip() or attach.stdout.strip())
        front_door = target / ".sidecar" / "bin" / "sidecar.py"

        def sidecar(*arguments: str) -> dict:
            process = _run([sys.executable, str(front_door), *arguments])
            if process.returncode:
                raise AssertionError(process.stderr.strip() or process.stdout.strip())
            return json.loads(process.stdout)

        sidecar("substrate", "refresh")
        first = sidecar("substrate", "status")["counts"]
        sidecar("substrate", "refresh")
        second = sidecar("substrate", "status")["counts"]
        for table in ("resource_versions", "epistemic_evidence"):
            if second[table] != first[table]:
                raise AssertionError(f"unchanged refresh grew {table}: {first[table]} -> {second[table]}")
        revision = sidecar("awareness", "refresh")["revision"]
        profile = revision["summary"]["domain_profile"]
        if profile != "software":
            raise AssertionError(f"consumer entrance reports {profile!r} for realistic software target")
        projection = revision["summary"].get("projection")
        if not projection or "source_handles" not in projection:
            raise AssertionError("awareness summary does not disclose projection shown/total counts")
        if not any("not traversed" in item for item in revision["limitations"]):
            raise AssertionError("awareness does not disclose untraversed generated/vendor subtrees")
        resource = sidecar("substrate", "resources", "read", "path:.git/")["resource"]
        if resource["latest"]["content_hash"] is not None:
            raise AssertionError("generated subtree root carries a content hash")
        shutil.rmtree(target, ignore_errors=True)
    return (
        f"installed sidecar reports software on a realistic target, stable evidence/versions across"
        f" unchanged refresh ({first['epistemic_evidence']} evidence rows), and disclosed projection"
    )


def _working_tree_provenance() -> str:
    """Authoritative receipts must name a head_commit that contains the measured source."""
    status = _git("status", "--short")
    offending = [
        line
        for line in status.splitlines()
        if not (line.startswith("??") and line[3:].startswith(".builder/evidence/"))
    ]
    if offending:
        raise AssertionError(f"working tree differs from head_commit: {offending[:5]}")
    return "measured source is fully contained in head_commit (untracked evidence receipts only)"


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
        "test_true_mixed_fixture_reports_mixed_for_substantive_records",
        "test_subordinate_document_beside_software_does_not_produce_mixed",
        "test_generated_and_vendor_subtrees_are_metadata_only_and_not_traversed",
        "test_unchanged_refresh_does_not_grow_evidence_or_versions",
        "test_awareness_discloses_truncated_projection",
        "test_notes_collection_with_helper_scripts_is_not_software",
        "test_documentation_that_does_not_dominate_stays_software_ancillary",
        "test_ordinary_vendor_and_build_folders_on_records_target_are_traversed",
        "mixed_text_documents_dominate",
        "generated or vendor material was read",
        "node_modules",
        "large.dat",
        "file_metadata",
        "large weak material was fully read",
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
            "hash computed before weak-material basis",
            lambda: _weak_material_metadata_only_boundary_source(
                substrate_source.replace(
                    "record[\"domain\"] = _domain_signal(",
                    "record[\"content_hash\"] = hashlib.sha256(path.read_bytes()).hexdigest()\n"
                    "    record[\"domain\"] = _domain_signal(",
                )
            ),
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
    witnessed.extend(_executed_mutations())
    return "rejected: " + "; ".join(witnessed)


def _executed_mutations() -> list[str]:
    """Run the known-answer classification against live wrong implementations."""
    substrate = _import_substrate()
    witnessed: list[str] = []
    originals = {
        "_GENERATED_PARTS": substrate._GENERATED_PARTS,
        "_VENDOR_PARTS": substrate._VENDOR_PARTS,
        "_RECORD_SUFFIXES": substrate._RECORD_SUFFIXES,
        "_ANCILLARY_DOCUMENT_SUFFIXES": substrate._ANCILLARY_DOCUMENT_SUFFIXES,
        "_profile_decision": substrate._profile_decision,
        "_text_documents_dominate": substrate._text_documents_dominate,
        "_SOFTWARE_CONDITIONAL_PARTS": substrate._SOFTWARE_CONDITIONAL_PARTS,
    }

    def detect_only(**kwargs):
        candidates = [*kwargs["records"], *kwargs["documents"], *kwargs["config_data"]]
        return {
            "records_documents": candidates,
            "decision": "detect_only",
            "ancillary_document_count": 0,
            "subordinate_count": 0,
        }

    mutations = (
        ("generated subtrees traversed", {"_GENERATED_PARTS": set()}),
        ("vendor subtrees traversed", {"_VENDOR_PARTS": set()}),
        ("config JSON counted as records", {"_RECORD_SUFFIXES": originals["_RECORD_SUFFIXES"] | {".json"}}),
        ("README/notes counted as records/documents evidence", {"_ANCILLARY_DOCUMENT_SUFFIXES": set()}),
        ("text documents always ancillary", {"_text_documents_dominate": lambda text, software: False}),
        ("vendor/build/dist untraversed on every target", {"_SOFTWARE_CONDITIONAL_PARTS": set()}),
        ("profile detects instead of discriminates", {"_profile_decision": detect_only}),
    )
    try:
        for label, patch in mutations:
            for name, value in patch.items():
                setattr(substrate, name, value)
            try:
                _known_answer_profiles(substrate)
            except AssertionError:
                witnessed.append(f"executed: {label}")
            else:
                raise AssertionError(f"executed discrimination accepted {label}")
            finally:
                for name in patch:
                    setattr(substrate, name, originals[name])
    finally:
        for name, value in originals.items():
            setattr(substrate, name, value)
    return witnessed


def _weak_material_metadata_only_boundary_source(source: str) -> None:
    required = [
        "def _observation_type(",
        "file_metadata",
        "record[\"domain\"] = _domain_signal(",
        "record[\"domain\"][\"content_basis\"] != \"metadata_only\"",
        "record[\"content_hash\"] = hashlib.sha256(path.read_bytes()).hexdigest()",
    ]
    missing = [term for term in required if term not in source]
    if missing:
        raise AssertionError(f"metadata-only boundary terms missing: {missing}")
    domain_index = source.index("record[\"domain\"] = _domain_signal(")
    hash_index = source.index("record[\"content_hash\"] = hashlib.sha256(path.read_bytes()).hexdigest()")
    if hash_index < domain_index:
        raise AssertionError("content hash is computed before weak-material basis is known")


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
        _check("weak_material_metadata_only_boundary", _weak_material_metadata_only_boundary),
        _check("t7_awareness_projection", _t7_awareness_projection),
        _check("known_answer_domain_profiles", _known_answer_domain_profiles),
        _check("consumer_entrance_known_answer", _consumer_entrance_known_answer),
        _check("working_tree_provenance", _working_tree_provenance),
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
