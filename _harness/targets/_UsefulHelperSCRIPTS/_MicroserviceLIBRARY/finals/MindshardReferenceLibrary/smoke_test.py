from __future__ import annotations

import json
import tempfile
from pathlib import Path

from backend import BackendRuntime


def main() -> int:
    runtime = BackendRuntime()
    with tempfile.TemporaryDirectory(prefix="mindshard_ref_smoke_") as temp_dir:
        root = Path(temp_dir)
        source_dir = root / "sample_source"
        source_dir.mkdir(parents=True, exist_ok=True)
        project_root = root / "sample_project"
        project_root.mkdir(parents=True, exist_ok=True)
        (source_dir / "README.md").write_text("# Sample\n\nThis is a reference note.\n\nIt has two paragraphs.\n", encoding="utf-8")
        (source_dir / "demo.py").write_text("def hello():\n    return 'world'\n\nclass Demo:\n    pass\n", encoding="utf-8")
        import_report = runtime.call("MindshardReferenceLibraryService", "library_import", source_path=str(source_dir), title="SampleRoot", project_root=str(project_root))
        root_id = import_report["root_node_id"]
        search_report = runtime.call("MindshardReferenceLibraryService", "library_search", query="reference", project_root=str(project_root), scope="attached", limit=5)
        if not search_report["results"]:
            raise RuntimeError("Smoke test search returned no results.")
        hit = search_report["results"][0]
        excerpt_report = runtime.call(
            "MindshardReferenceLibraryService",
            "library_read_excerpt",
            node_id=hit["node_id"],
            revision_id=hit["revision_id"],
            section_id=hit["section_id"],
            project_root=str(project_root),
            session_db_path=str(root / "session.sqlite3"),
            session_id="smoke_session",
        )
        if not excerpt_report.get("excerpt_text", "").strip():
            raise RuntimeError("Smoke test excerpt was empty.")
        export_dir = root / "exported"
        export_report = runtime.call("MindshardReferenceLibraryService", "library_export", node_id=root_id, destination=str(export_dir))
        if not export_report["written_files"]:
            raise RuntimeError("Smoke test export wrote no files.")
        summary = {
            "status": "ok",
            "import_root_node_id": root_id,
            "search_hits": len(search_report["results"]),
            "excerpt_hash": excerpt_report["excerpt_hash"],
            "exported_files": export_report["written_files"],
            "health": runtime.health(),
        }
        print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
