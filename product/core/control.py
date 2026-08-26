from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass

from . import registry, storage
from .constants import CONTROL_PLANE_VERSION, TOOL_CONTRACT_VERSION
from .containment import ContainmentError, resolve_declared_paths
from .contracts import ToolManifest, validate_json
from .instance import InstanceContext

_AUTHORITY_ORDER = {"observe": 0, "sandbox": 1, "apply": 2}


@dataclass(frozen=True)
class ControlPlane:
    context: InstanceContext

    def __post_init__(self) -> None:
        storage.bootstrap(self.context)

    def tools(self) -> list[dict]:
        return [record.public_record() for record in registry.discover(self.context).values()]

    def _envelope(self, tool_id: str, client: str, authority: str, **payload: object) -> dict:
        return {
            **payload,
            "tool_id": tool_id,
            "client": client,
            "authority": authority,
            "control_plane": {
                "version": CONTROL_PLANE_VERSION,
                "tool_contract": TOOL_CONTRACT_VERSION,
            },
        }

    def _failure(
        self,
        tool_id: str,
        client: str,
        authority: str,
        code: str,
        message: str,
        **extra: object,
    ) -> dict:
        return self._envelope(
            tool_id,
            client,
            authority,
            ok=False,
            error={"code": code, "message": message},
            **extra,
        )

    def _mechanical_context(self, manifest: ToolManifest) -> dict:
        domains = set(manifest.reads) | set(manifest.writes)
        excluded_roots = [str(self.context.instance_root)] if "target" in domains else []
        return {
            "target_root": str(self.context.target_root),
            "excluded_roots": excluded_roots,
        }

    def invoke(
        self,
        tool_id: str,
        arguments: dict,
        client: str,
        authority: str = "observe",
        timeout_seconds: int = 30,
    ) -> dict:
        started = time.monotonic()
        client = str(client or "").strip()
        authority = str(authority or "").lower()
        if not client:
            return self._failure(tool_id, "unknown", authority, "invalid_client", "client is required")
        if authority not in _AUTHORITY_ORDER:
            return self._failure(
                tool_id, client, authority, "invalid_authority", f"unknown authority: {authority}"
            )
        if not isinstance(arguments, dict):
            return self._failure(
                tool_id, client, authority, "invalid_arguments", "arguments must be an object"
            )

        try:
            manifest = registry.get(self.context, tool_id)
        except registry.RegistryError as exc:
            return self._failure(tool_id, client, authority, "registry_error", str(exc))

        if _AUTHORITY_ORDER[authority] < _AUTHORITY_ORDER[manifest.authority]:
            return self._failure(
                tool_id,
                client,
                authority,
                "authority_denied",
                f"{tool_id} requires {manifest.authority} authority; caller supplied {authority}",
                required_authority=manifest.authority,
                manifest_digest=manifest.digest,
            )

        input_errors = validate_json(arguments, manifest.input_schema)
        if input_errors:
            return self._failure(
                tool_id,
                client,
                authority,
                "input_contract",
                "; ".join(input_errors),
                manifest_digest=manifest.digest,
            )
        try:
            resolved_arguments = resolve_declared_paths(self.context, manifest, arguments)
        except ContainmentError as exc:
            return self._failure(
                tool_id,
                client,
                authority,
                "containment_refusal",
                str(exc),
                manifest_digest=manifest.digest,
            )

        request = {
            "args": resolved_arguments,
            "context": self._mechanical_context(manifest),
        }
        environment = dict(os.environ)
        existing_python_path = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = str(self.context.instance_root) + (
            os.pathsep + existing_python_path if existing_python_path else ""
        )
        environment["PYTHONUTF8"] = "1"
        for name in tuple(environment):
            if name.startswith("SIDECAR_IDENTITY_"):
                environment.pop(name, None)

        timeout = max(1, min(int(timeout_seconds), 300))
        try:
            process = subprocess.run(
                [sys.executable, str(manifest.entry)],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.context.target_root,
                env=environment,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return self._failure(
                tool_id,
                client,
                authority,
                "timeout",
                f"tool exceeded {timeout} seconds",
                duration_ms=int((time.monotonic() - started) * 1000),
                manifest_digest=manifest.digest,
            )
        except OSError as exc:
            return self._failure(
                tool_id,
                client,
                authority,
                "process_error",
                str(exc),
                duration_ms=int((time.monotonic() - started) * 1000),
                manifest_digest=manifest.digest,
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            result = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            return self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                f"tool output is not valid JSON: {exc}",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
            )
        if not isinstance(result, dict):
            return self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                "tool output must be a JSON object",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
            )

        output_errors = validate_json(result, manifest.output_schema)
        if output_errors:
            return self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                "; ".join(output_errors),
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                untrusted_result=result,
            )
        if process.returncode != 0:
            return self._failure(
                tool_id,
                client,
                authority,
                "tool_process_failed",
                result.get("error") or process.stderr.strip() or f"exit code {process.returncode}",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                result=result,
            )

        return self._envelope(
            tool_id,
            client,
            authority,
            ok=bool(result.get("ok")),
            result=result,
            duration_ms=duration_ms,
            exit_code=process.returncode,
            manifest_digest=manifest.digest,
        )
