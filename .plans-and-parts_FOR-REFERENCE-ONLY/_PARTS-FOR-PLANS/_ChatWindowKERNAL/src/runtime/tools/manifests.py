"""
Owns: portable tool-package manifest loading and runner invocation.
Does not own: tool runtime state, UI rendering, or background scheduling.
Collaborates with: package tool service and top-level tool_packages.
"""

from __future__ import annotations

import importlib.util
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.runtime.contracts.tools import ToolDescriptor


@dataclass(frozen=True)
class ToolPackageDefinition:
    descriptor: ToolDescriptor
    package_dir: Path
    entrypoint: str


def discover_tool_packages(tool_packages_dir: Path) -> dict[str, ToolPackageDefinition]:
    definitions: dict[str, ToolPackageDefinition] = {}
    if not tool_packages_dir.exists():
        return definitions

    for package_dir in sorted(child for child in tool_packages_dir.iterdir() if child.is_dir()):
        manifest_path = package_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        with manifest_path.open("r", encoding="utf-8") as handle:
            manifest = json.load(handle)

        descriptor = ToolDescriptor(
            tool_id=str(manifest["id"]),
            name=str(manifest["name"]),
            description=str(manifest["description"]),
            category=str(manifest.get("category", "general")),
            manifest_path=str(manifest_path),
            status=str(manifest.get("status", "available")),
            capability_class=str(manifest.get("capability_class", "standard")),
        )
        definitions[descriptor.tool_id] = ToolPackageDefinition(
            descriptor=descriptor,
            package_dir=package_dir,
            entrypoint=str(manifest.get("entrypoint", "runner.py:run")),
        )
    return definitions


def invoke_tool(definition: ToolPackageDefinition, arguments: dict[str, Any]) -> Any:
    module_name = f"toolpkg_{definition.descriptor.tool_id.replace('.', '_')}"
    relative_path, callable_name = definition.entrypoint.split(":", 1)
    module_path = definition.package_dir / relative_path

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load tool module: {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    callback = getattr(module, callable_name, None)
    if callback is None or not callable(callback):
        raise RuntimeError(f"Tool entrypoint is not callable: {definition.entrypoint}")

    return callback(arguments)
