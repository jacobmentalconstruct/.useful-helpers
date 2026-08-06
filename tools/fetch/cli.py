"""
FILE:       tools/fetch/cli.py
ROLE:       Confirm-gated download  -  URL to file, dry-run-first, through the governed seam.
DOMAIN:     tool
DOES:       Dry-run: HEAD the URL and report host/size/content-type (the plan). Apply: GET
            and stream to a file  -  default destination under the toolkit's output root
            (`_artifacts/fetch/`), explicit `dest` may target the project deliberately.
            Size-capped; reports sha256 of the written file.
DEPENDS ON: tools._toolkit, (stdlib) urllib, hashlib, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
            downloads are exactly what should be governed + audit-logged)
NOTES:      Same local-first stance as http_probe: non-local hosts require allow_remote:true.
            Roots contract: default output under output_root(), never the host project.
"""
from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from tools._toolkit import confirmed, output_root, tool_main

_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_DEFAULT_MAX = 50 * 1024 * 1024  # 50 MB


def _head(url: str, timeout: int) -> dict:
    req = urllib.request.Request(url, method="HEAD",
                                 headers={"User-Agent": "useful-helpers/fetch"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": resp.status, "size": resp.headers.get("Content-Length"),
                    "content_type": resp.headers.get("Content-Type")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "note": f"HEAD not honored ({e.reason}); GET may still work"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"error": f"unreachable: {getattr(e, 'reason', e)}"}


@tool_main
def run(args: dict) -> dict:
    url = str(args.get("url") or "").strip()
    if not url:
        return {"ok": False, "error": "'url' is required"}
    if "://" not in url:
        url = "http://" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        return {"ok": False, "error": f"unsupported scheme: {parsed.scheme}"}
    host = (parsed.hostname or "").lower()
    if host not in _LOCAL_HOSTS and not args.get("allow_remote"):
        return {"ok": False, "error": f"non-local host {host!r}; pass allow_remote:true to "
                "fetch beyond localhost"}

    timeout = min(int(args.get("timeout_s", 30)), 300)
    max_bytes = min(int(args.get("max_bytes", _DEFAULT_MAX)), 500 * 1024 * 1024)
    name = Path(parsed.path).name or "download.bin"
    dest = Path(str(args["dest"])).resolve() if args.get("dest") else (
        output_root() / "fetch" / name)

    dry_run = bool(args.get("dry_run", True))
    if dry_run or not confirmed(args):
        plan = _head(url, timeout)
        return {"tool": "fetch", "dry_run": True, "url": url, "host": host,
                "dest": dest.as_posix(), "max_bytes": max_bytes, **plan}

    req = urllib.request.Request(url, headers={"User-Agent": "useful-helpers/fetch"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            written = 0
            with open(dest, "wb") as out:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > max_bytes:
                        out.close()
                        dest.unlink(missing_ok=True)
                        return {"ok": False, "error": f"aborted: exceeds max_bytes "
                                f"({max_bytes}); raise the cap deliberately if intended"}
                    out.write(chunk)
                    digest.update(chunk)
            return {"tool": "fetch", "dry_run": False, "url": url, "host": host,
                    "dest": dest.as_posix(), "bytes": written,
                    "sha256": digest.hexdigest(),
                    "content_type": resp.headers.get("Content-Type")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "error": f"unreachable: {getattr(e, 'reason', e)}"}
