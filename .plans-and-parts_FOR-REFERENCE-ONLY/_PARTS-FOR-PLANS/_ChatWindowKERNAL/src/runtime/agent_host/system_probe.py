"""
Owns: host-side hardware telemetry collection for session/runtime headers.
Does not own: UI rendering, vendored runtime imports, or task orchestration.
Collaborates with: session controller background probes.
"""

from __future__ import annotations

import ctypes
import json
import os
import subprocess

from src.runtime.contracts.session import HardwareSnapshot
from src.utils.time_utils import utc_timestamp


class _MemoryStatus(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def collect_hardware_snapshot() -> HardwareSnapshot:
    cpu_label = f"CPU {os.cpu_count() or '?'} threads"
    ram_used_gb, ram_total_gb = _memory_totals_gb()
    gpu_name, vram_used_mb, vram_total_mb = _gpu_probe()

    ram_summary = (
        f"RAM {ram_used_gb:.1f}/{ram_total_gb:.1f} GB"
        if ram_total_gb > 0
        else "RAM unavailable"
    )
    if vram_total_mb is not None:
        used_label = "--" if vram_used_mb is None else str(vram_used_mb)
        vram_summary = f"VRAM {used_label}/{vram_total_mb} MB"
    else:
        vram_summary = "VRAM unavailable"

    return HardwareSnapshot(
        cpu_label=cpu_label,
        ram_summary=ram_summary,
        gpu_label=gpu_name or "GPU unavailable",
        vram_summary=vram_summary,
        updated_at=utc_timestamp(),
    )


def _memory_totals_gb() -> tuple[float, float]:
    try:
        status = _MemoryStatus()
        status.dwLength = ctypes.sizeof(_MemoryStatus)
        if not ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            return 0.0, 0.0
        total = status.ullTotalPhys / (1024**3)
        used = (status.ullTotalPhys - status.ullAvailPhys) / (1024**3)
        return used, total
    except Exception:
        return 0.0, 0.0


def _gpu_probe() -> tuple[str, int | None, int | None]:
    nvidia = _probe_nvidia_smi()
    if nvidia is not None:
        return nvidia
    return _probe_wmi_gpu()


def _probe_nvidia_smi() -> tuple[str, int | None, int | None] | None:
    try:
        completed = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None

    line = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
    if not line:
        return None
    parts = [part.strip() for part in line.split(",")]
    if len(parts) < 3:
        return None
    return parts[0], _safe_int(parts[1]), _safe_int(parts[2])


def _probe_wmi_gpu() -> tuple[str, int | None, int | None]:
    try:
        completed = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-CimInstance Win32_VideoController | "
                "Select-Object -First 1 Name,AdapterRAM | ConvertTo-Json -Compress",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=6,
        )
        payload = json.loads(completed.stdout.strip() or "{}")
        name = str(payload.get("Name", "")).strip()
        adapter_ram = _safe_int(payload.get("AdapterRAM"))
        if adapter_ram is None:
            return name, None, None
        return name, None, int(adapter_ram / (1024 * 1024))
    except Exception:
        return "", None, None


def _safe_int(value) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
