from __future__ import annotations

import importlib
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

from library.microservice_std_lib import extract_service_schema
from lib.reference_service import MindshardReferenceLibraryService


def _build_service_spec():
    schema = extract_service_schema(MindshardReferenceLibraryService)
    meta = schema["meta"]
    return {
        "service_id": "service_mindshard_reference_library",
        "class_name": "MindshardReferenceLibraryService",
        "service_name": meta["name"],
        "module_import": "lib.reference_service",
        "description": meta["description"],
        "tags": list(meta.get("tags", [])),
        "capabilities": list(meta.get("capabilities", [])),
        "manager_layer": "",
        "registry_name": meta["name"],
        "is_ui": False,
        "endpoints": [
            {
                "method_name": endpoint["name"],
                "inputs_json": json.dumps(endpoint["inputs"], sort_keys=True),
                "outputs_json": json.dumps(endpoint["outputs"], sort_keys=True),
                "description": endpoint["description"],
                "tags_json": json.dumps(endpoint.get("tags", []), sort_keys=True),
                "mode": endpoint.get("mode", "sync"),
            }
            for endpoint in schema["endpoints"]
        ],
    }


SERVICE_SPECS = [_build_service_spec()]


class BackendRuntime:
    def __init__(self) -> None:
        self.app_dir = APP_DIR
        self.settings = SETTINGS
        self._instances = {}

    def list_services(self):
        return list(SERVICE_SPECS)

    def _find_spec(self, name):
        target = str(name).strip()
        for spec in SERVICE_SPECS:
            if target in {spec["class_name"], spec["service_name"], spec["service_id"]}:
                return spec
        return None

    def get_service(self, name, config=None):
        spec = self._find_spec(name)
        if spec is None:
            raise KeyError(name)
        cache_key = spec["class_name"]
        if config is None and cache_key in self._instances:
            return self._instances[cache_key]
        module = importlib.import_module(spec["module_import"])
        cls = getattr(module, spec["class_name"])
        try:
            instance = cls(config or {})
        except TypeError:
            if config:
                instance = cls(**config)
            else:
                instance = cls()
        if config is None:
            self._instances[cache_key] = instance
        return instance

    def call(self, service_name, endpoint, **kwargs):
        service = self.get_service(service_name, config=kwargs.pop("_config", None))
        fn = getattr(service, endpoint)
        return fn(**kwargs)

    def health(self):
        report = {"instantiated": {}, "deferred": []}
        for spec in SERVICE_SPECS:
            if spec["class_name"] in self._instances:
                service = self._instances[spec["class_name"]]
                try:
                    report["instantiated"][spec["class_name"]] = service.get_health()
                except Exception as exc:
                    report["instantiated"][spec["class_name"]] = {"status": "error", "error": str(exc)}
            else:
                report["deferred"].append(spec["class_name"])
        return report

    def shutdown(self):
        for service in list(self._instances.values()):
            closer = getattr(service, "shutdown", None)
            if callable(closer):
                closer()
