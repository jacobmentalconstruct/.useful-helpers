"""
FILE:       src/core/instance.py
ROLE:       The one authority on what an installed instance IS.
DOMAIN:     core
DOES:       Defines the identity manifest, creates it, validates it, and resolves an
            InstanceContext from a directory on disk.
DEPENDS ON: stdlib only
WIRES TO:   packaging/installer (creation), src/core/config (resolution),
            everything else through the resolved context
NOTES:      T6. Before this module, FOUR surfaces answered "what is the sidecar":
            `config.py` by a marker file, `tools/_toolkit.py` by an environment
            variable with a basename fallback, and two installers by their own
            private constant. `BCC-ONE-AUTHORITY`, sixth recorded instance.

            IDENTITY IS TWO THINGS, AND BOTH ARE NEEDED.

              UUID       proves CONTINUITY. The same instance across updates, so
                         durable records keyed to it are not orphaned.
              relation   proves LOCATION. Where the target is, RELATIVE to here.

            Neither substitutes for the other, and neither is a lookup key into an
            external registry of installations. A target plus its sidecar must remain
            self-contained and relocatable: move both together to another drive and
            the relationship is intact, because nothing absolute was ever written
            down.

            ABSENT IS NOT MALFORMED. The distinction is the whole reason the previous
            resolution scheme could hide a failure:

              no manifest        -> this is not a canonical instance. Say so, return
                                    None, let the caller decide.
              manifest present   -> this CLAIMS to be an instance and its identity is
              but invalid           broken. RAISE. Never fall through to a guess.

            Falling through from corrupt canonical identity into a legacy heuristic is
            how a new mechanism fails while an old one masks it - the false green this
            project has now produced four times.

            OWNERSHIP SPLIT. This module owns identity MECHANICS: schema, validation,
            serialisation, resolution, construction. The installer owns lifecycle
            POLICY: what a fresh install, an update and a clean reinstall each MEAN
            for identity. `create()` therefore never adopts an existing identity by
            itself - the caller passes one in, explicitly, or a new one is minted.
"""
from __future__ import annotations

import json
import os
import re
import uuid as _uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["InstanceContext", "InstanceError", "MANIFEST", "SCHEMA",
           "create", "resolve", "read_identity"]

MANIFEST = "instance.json"
SCHEMA = 1

# The state root lives inside the instance. Named here because it is part of what an
# instance IS, not a detail of who happens to write to it.
STATE_DIRNAME = "_state"

_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-"
                      r"[0-9a-f]{4}-[0-9a-f]{12}$")


class InstanceError(RuntimeError):
    """This claims to be an installed instance, and its identity is broken.

    Deliberately not a subclass of anything callers already swallow. A broken
    identity must be loud: the alternative is resolving to a plausible directory and
    reporting success, which is what `SUITE_PROJECT_ROOT` already refuses to do for
    the same reason (config.py case 2).
    """


@dataclass(frozen=True)
class InstanceContext:
    """The resolved truth every runtime consumer reads instead of guessing.

    Frozen: a consumer that could mutate this would become a second authority.
    """
    instance_root: Path      # where the sidecar physically is
    target_root: Path        # the one target it is bound to
    state_root: Path         # its durable memory
    uuid: str                # continuity across updates
    schema: int

    def as_env(self) -> dict:
        """Resolved values for TRANSPORT to a subprocess.

        Environment is a transport boundary, not an authority. A child receiving
        these is consuming resolved identity; a child that reads them and then falls
        back to cwd or a basename is inferring, which is the defect this replaces.
        """
        return {"SUITE_HOME": str(self.instance_root),
                "SUITE_PROJECT_ROOT": str(self.target_root),
                "SUITE_STATE_ROOT": str(self.state_root)}


def _manifest_path(instance_root: Path) -> Path:
    return Path(instance_root) / MANIFEST


def new_uuid() -> str:
    return str(_uuid.uuid4())


def create(instance_root: "Path | str", target_root: "Path | str", *,
           identity: "str | None" = None) -> InstanceContext:
    """Write the identity manifest and return the resolved context.

    `identity` is the LIFECYCLE POLICY hook, and it is explicit on purpose. A fresh
    install passes None and gets a new UUID. An update passes the UUID it read before
    replacing the tree, because an update is the same instance with newer code. A
    clean reinstall passes None, because that is a different instance in the same
    place - if that is the meaning we adopt, the installer says so, not this module.

    Nothing absolute is written. The target is stored as a path RELATIVE to the
    instance root, so the pair relocates intact.
    """
    instance_root = Path(instance_root).resolve()
    target_root = Path(target_root).resolve()
    instance_root.mkdir(parents=True, exist_ok=True)

    rel = os.path.relpath(target_root, instance_root)
    doc = {
        "schema": SCHEMA,
        "uuid": identity or new_uuid(),
        "target": Path(rel).as_posix(),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _manifest_path(instance_root).write_text(
        json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return _context(instance_root, doc)


def read_identity(instance_root: "Path | str") -> "str | None":
    """The UUID, or None if there is no canonical instance here.

    For the installer's update path, which must read identity BEFORE it replaces the
    tree. Returns None for absent; raises for malformed - the same distinction as
    resolve(), because an update that silently mints a new identity over a corrupt
    one is exactly the continuity break this exists to prevent.
    """
    ctx = resolve(instance_root)
    return ctx.uuid if ctx else None


def resolve(instance_root: "Path | str") -> "InstanceContext | None":
    """Resolve identity structurally. None if absent; RAISE if malformed.

    Consults no environment variable, no basename, and no working directory. The
    only inputs are this directory and what is written inside it.
    """
    instance_root = Path(instance_root).resolve()
    path = _manifest_path(instance_root)
    if not path.is_file():
        return None                      # not a canonical instance. Not an error.

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        raise InstanceError(f"identity manifest unreadable: {path} ({e})") from e
    try:
        doc = json.loads(raw)
    except ValueError as e:
        raise InstanceError(f"identity manifest is not valid JSON: {path} ({e})") from e
    if not isinstance(doc, dict):
        raise InstanceError(f"identity manifest is not an object: {path}")
    return _context(instance_root, doc, path=path)


def _context(instance_root: Path, doc: dict,
             path: "Path | None" = None) -> InstanceContext:
    """Validate every field before anything is allowed to depend on it."""
    where = path or _manifest_path(instance_root)

    schema = doc.get("schema")
    if not isinstance(schema, int):
        raise InstanceError(f"identity schema is missing or not an integer: {where}")
    if schema > SCHEMA:
        raise InstanceError(
            f"identity schema {schema} is newer than this sidecar understands "
            f"({SCHEMA}): {where}. Refusing to guess at a format from the future.")

    ident = doc.get("uuid")
    if not isinstance(ident, str) or not _UUID_RE.match(ident):
        raise InstanceError(f"identity uuid is missing or malformed: {ident!r} in {where}")

    rel = doc.get("target")
    if not isinstance(rel, str) or not rel:
        raise InstanceError(f"identity target relation is missing: {where}")
    if Path(rel).is_absolute():
        raise InstanceError(
            f"identity target is absolute ({rel!r}) in {where}. Identity records a "
            "RELATIONSHIP; an absolute path breaks the moment the pair is moved.")

    target = (instance_root / rel).resolve()
    if not target.is_dir():
        raise InstanceError(
            f"identity target does not resolve to a directory: {rel!r} -> {target} "
            f"(from {where})")

    return InstanceContext(
        instance_root=instance_root,
        target_root=target,
        state_root=instance_root / STATE_DIRNAME,
        uuid=ident,
        schema=schema,
    )
