from __future__ import annotations

import shutil
from pathlib import Path

from product.core import instance, storage


class AttachError(RuntimeError):
    pass


_PAYLOAD_DIRECTORIES = ("bin", "core", "tools")


def _product_root() -> Path:
    return Path(__file__).resolve().parents[1] / "product"


def attach(target: str | Path) -> dict:
    """Positively assemble one new instrument inside an existing target."""
    target_root = Path(target).expanduser().resolve()
    if not target_root.is_dir():
        raise AttachError(f"target must be an existing directory: {target_root}")

    instance_root = target_root / ".sidecar"
    if instance_root.exists():
        raise AttachError(f"an entry already exists at {instance_root}; refusing to overwrite it")

    product_root = _product_root()
    missing = [name for name in _PAYLOAD_DIRECTORIES if not (product_root / name).is_dir()]
    if missing:
        raise AttachError(f"product payload is incomplete: missing {', '.join(missing)}")

    instance_root.mkdir()
    try:
        for name in _PAYLOAD_DIRECTORIES:
            shutil.copytree(
                product_root / name,
                instance_root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        (instance_root / "state" / "objects").mkdir(parents=True)
        (instance_root / "logs").mkdir()
        context = instance.create(instance_root, target_root)
        storage.bootstrap(context)
    except Exception as exc:
        shutil.rmtree(instance_root, ignore_errors=True)
        if isinstance(exc, AttachError):
            raise
        raise AttachError(f"attachment failed: {exc}") from exc

    return {
        "instance_uuid": context.instance_uuid,
        "instance": ".sidecar",
        "target_relation": context.target_relation,
        "front_door": ".sidecar/bin/sidecar.py",
    }
