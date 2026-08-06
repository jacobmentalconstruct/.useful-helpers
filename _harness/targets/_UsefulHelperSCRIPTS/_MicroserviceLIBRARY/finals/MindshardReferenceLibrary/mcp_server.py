"""MCP server for MindshardReferenceLibrary."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
SETTINGS = json.loads((APP_DIR / "settings.json").read_text(encoding="utf-8"))
for candidate in [SETTINGS.get("canonical_import_root", "")] + list(SETTINGS.get("compat_paths", [])):
    if not candidate:
        continue
    resolved = str(APP_DIR / candidate) if not os.path.isabs(candidate) else candidate
    if resolved not in sys.path:
        sys.path.insert(0, resolved)

from fastmcp import FastMCP
from backend import BackendRuntime, SERVICE_SPECS

mcp = FastMCP("MindshardReferenceLibrary")
_runtime = BackendRuntime()


def _fmt(obj: object) -> str:
    return json.dumps(obj, indent=2, default=str)


@mcp.tool
def list_services() -> str:
    summary = []
    for spec in SERVICE_SPECS:
        summary.append(
            {
                "class_name": spec["class_name"],
                "service_name": spec["service_name"],
                "description": spec["description"],
                "endpoints": [{"method": endpoint["method_name"], "description": endpoint["description"]} for endpoint in spec.get("endpoints", [])],
            }
        )
    return _fmt(summary)


@mcp.tool
def app_health() -> str:
    return _fmt(_runtime.health())


@mcp.tool
def library_manifest() -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_manifest"))


@mcp.tool
def library_import(source_path: str, parent_node_id: str = "", title: str = "", project_root: str = "") -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_import", source_path=source_path, parent_node_id=parent_node_id, title=title, project_root=project_root))


@mcp.tool
def library_refresh(node_id: str, source_path: str = "") -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_refresh", node_id=node_id, source_path=source_path))


@mcp.tool
def library_archive(node_id: str) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_archive", node_id=node_id))


@mcp.tool
def library_attach(project_root: str, node_id: str, attachment_context_json: str = "{}") -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_attach", project_root=project_root, node_id=node_id, attachment_context_json=attachment_context_json))


@mcp.tool
def library_detach(project_root: str, node_id: str) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_detach", project_root=project_root, node_id=node_id))


@mcp.tool
def library_list_roots(include_archived: bool = False) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_list_roots", include_archived=include_archived))


@mcp.tool
def library_list_children(node_id: str = "", include_archived: bool = False) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_list_children", node_id=node_id, include_archived=include_archived))


@mcp.tool
def library_search(query: str, project_root: str = "", scope: str = "attached", limit: int = 10, include_archived: bool = False) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_search", query=query, project_root=project_root, scope=scope, limit=limit, include_archived=include_archived))


@mcp.tool
def library_get_detail(node_id: str, revision_id: str = "") -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_get_detail", node_id=node_id, revision_id=revision_id))


@mcp.tool
def library_list_revisions(node_id: str) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_list_revisions", node_id=node_id))


@mcp.tool
def library_read_excerpt(
    node_id: str,
    revision_id: str = "",
    section_id: str = "",
    anchor_path: str = "",
    char_start: int = 0,
    char_end: int = 0,
    project_root: str = "",
    session_db_path: str = "",
    session_id: str = "",
    attachment_context_json: str = "{}",
) -> str:
    return _fmt(
        _runtime.call(
            "MindshardReferenceLibraryService",
            "library_read_excerpt",
            node_id=node_id,
            revision_id=revision_id,
            section_id=section_id,
            anchor_path=anchor_path,
            char_start=char_start,
            char_end=char_end,
            project_root=project_root,
            session_db_path=session_db_path,
            session_id=session_id,
            attachment_context_json=attachment_context_json,
        )
    )


@mcp.tool
def library_export(node_id: str, destination: str) -> str:
    return _fmt(_runtime.call("MindshardReferenceLibraryService", "library_export", node_id=node_id, destination=destination))


if __name__ == "__main__":
    mcp.run()
