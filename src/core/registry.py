"""
FILE:       src/core/registry.py
ROLE:       The shared Tool Registry  -  single source of truth for suite capabilities.
DOMAIN:     core
DOES:       Discover `tool.json` manifests under tools/ and apps/, validate them, expose
            list_tools()/get(id), and (re)generate config/registry.json.
DEPENDS ON: src.core.config, src.lib.logging_setup, (stdlib) json, dataclasses
WIRES TO:   read by interfaces.mcp_server, interfaces.cli, ui.registry_view
NOTES:      Carries the donor's category + authority model (Observe | Sandbox | Apply).
            DATA ONLY: never imports tool code; only describes how to invoke it.
            Dirs whose name starts with '_' (e.g. tools/_template) are skipped.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from src.core.config import Paths
from src.lib.logging_setup import get_logger

log = get_logger("core.registry")

AUTHORITIES = ("Observe", "Sandbox", "Apply")
OPERATES_ON = ("project", "toolkit")  # roots contract: the tool's declared subject
WRITES = ("none", "toolkit", "target")  # what a tool is permitted to write (Phase 4 ENFORCE)

# Absent `writes` is inferred from authority: reads write nothing; anything that writes defaults
# to the toolkit's own state, NEVER the target. A tool that legitimately writes into the target
# (installer, editors, project-command runner) must say so explicitly  -  the seam enforces it.
_WRITES_DEFAULT = {"Observe": "none", "Sandbox": "toolkit", "Apply": "toolkit"}


@dataclass(frozen=True)
class ToolRecord:
    """One registered capability. Mirror of a tool.json manifest entry."""
    id: str
    summary: str
    category: str
    authority: str
    invocation: dict
    operates_on: str = "project"
    writes: str = "none"
    input_schema: dict = field(default_factory=dict)
    output_shape: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)


def _to_record(data: dict, source: str) -> "ToolRecord | None":
    tool_id = str(data.get("id") or "").strip()
    if not tool_id:
        log.warning("skipping manifest with no id: %s", source)
        return None
    authority = str(data.get("authority") or "Observe")
    if authority not in AUTHORITIES:
        log.warning("manifest %s has invalid authority %r; defaulting to Observe", source, authority)
        authority = "Observe"
    operates_on = str(data.get("operates_on") or "")
    if operates_on not in OPERATES_ON:
        # Roots contract (T-roots): every tool declares its subject. Missing/invalid is a
        # manifest defect  -  surfaced loudly, defaulted safely.
        log.warning("manifest %s missing/invalid operates_on %r; defaulting to 'project'",
                    source, operates_on)
        operates_on = "project"
    writes = str(data.get("writes") or "").strip().lower()
    if writes not in WRITES:
        if writes:
            log.warning("manifest %s has invalid writes %r; inferring from authority", source, writes)
        writes = _WRITES_DEFAULT.get(authority, "none")
    return ToolRecord(
        id=tool_id,
        summary=str(data.get("summary") or ""),
        category=str(data.get("category") or "uncategorized"),
        authority=authority,
        operates_on=operates_on,
        writes=writes,
        invocation=dict(data.get("invocation") or {}),
        input_schema=dict(data.get("input_schema") or {}),
        output_shape=dict(data.get("output_shape") or {}),
        provenance=dict(data.get("provenance") or {}),
    )


def discover(paths: Paths) -> list[ToolRecord]:
    """Scan tools/ and apps/ for tool.json manifests (skipping _-prefixed dirs)."""
    records: list[ToolRecord] = []
    seen: dict[str, str] = {}
    for base in (paths.tools, paths.apps):
        if not base.is_dir():
            continue
        for manifest in sorted(base.glob("*/tool.json")):
            if manifest.parent.name.startswith("_"):
                continue
            try:
                data = json.loads(manifest.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as e:
                log.error("could not read manifest %s: %s", manifest, e)
                continue
            record = _to_record(data, str(manifest))
            if record is None:
                continue
            if record.id in seen:
                log.warning("duplicate tool id %r at %s (already registered from %s); skipping",
                            record.id, manifest, seen[record.id])
                continue
            seen[record.id] = str(manifest)
            records.append(record)
    return records


def list_tools(paths: Paths) -> list[ToolRecord]:
    """Return all registered tools (fresh discovery)."""
    return discover(paths)


def get(paths: Paths, tool_id: str) -> "ToolRecord | None":
    """Return one tool by id, or None."""
    for record in discover(paths):
        if record.id == tool_id:
            return record
    return None


def ensure_manifest(paths: Paths) -> bool:
    """Generate config/registry.json if it is missing. Returns True if it was written.

    The registry JSON is DERIVED state: `discover()` reads the tool.json manifests
    directly and never needs it, so it is deliberately untracked. But consumers that
    read the file - `operational_audit`, and the suite's registry cross-check -
    reasonably expect it to exist, and a fresh clone has no such file.

    That combination made the repository unable to pass its own suite from a clean
    checkout, while passing everywhere the file happened to linger from an earlier
    run. Untracking a file does not delete it, so the defect was invisible in every
    working tree that had ever generated one.

    Generating on demand keeps the file out of version control (no drift, no merge
    conflicts on a build artifact) while making a clean checkout work with no manual
    setup step. Cheap and idempotent: it is a no-op once the file exists.
    """
    if (paths.config / "registry.json").is_file():
        return False
    generate_manifest(paths)
    return True


def generate_manifest(paths: Paths) -> dict:
    """Regenerate config/registry.json from discovered manifests (derived state)."""
    records = discover(paths)
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(records),
        "tools": [asdict(r) for r in records],
    }
    paths.config.mkdir(parents=True, exist_ok=True)
    (paths.config / "registry.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log.info("regenerated registry.json with %d tools", len(records))
    return manifest
