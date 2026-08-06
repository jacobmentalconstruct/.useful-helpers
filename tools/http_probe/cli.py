"""
FILE:       tools/http_probe/cli.py
ROLE:       Local-first HTTP probe  -  verify a running server through the governed seam.
DOMAIN:     tool
DOES:       GET/HEAD a URL; return status, headers, size, a capped body snippet, and elapsed
            ms. Local hosts by default; non-local requires `allow_remote:true`. Redirects
            followed to a small cap. Never writes anything.
DEPENDS ON: tools._toolkit, (stdlib) urllib, time
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Observe authority)
            HTTP probe, not a browser; pairs with dev_server_manager)
NOTES:      Deliberately NOT a browser (report B2 rejected that scope). Body snippet is
            text-decoded best-effort and capped so results stay seam-friendly.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.parse
import urllib.request

from tools._toolkit import tool_main

_SNIPPET_CAP = 8_192
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "0.0.0.0"}
_MAX_REDIRECTS = 3


class _CappedRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        count = getattr(req, "redirect_count", 0)
        if count >= _MAX_REDIRECTS:
            raise urllib.error.HTTPError(req.full_url, code,
                                         f"too many redirects (>{_MAX_REDIRECTS})", headers, fp)
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.redirect_count = count + 1
        return new


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
                "probe beyond localhost"}

    method = str(args.get("method", "GET")).upper()
    if method not in ("GET", "HEAD"):
        return {"ok": False, "error": "method must be GET or HEAD"}
    timeout = min(int(args.get("timeout_s", 10)), 60)

    opener = urllib.request.build_opener(_CappedRedirects())
    req = urllib.request.Request(url, method=method,
                                 headers={"User-Agent": "useful-helpers/http_probe"})
    started = time.monotonic()
    try:
        with opener.open(req, timeout=timeout) as resp:
            body = b"" if method == "HEAD" else resp.read(_SNIPPET_CAP + 1)
            elapsed_ms = int((time.monotonic() - started) * 1000)
            headers = {k: v for k, v in resp.headers.items()}
            snippet = body[:_SNIPPET_CAP].decode("utf-8", errors="replace")
            return {
                "tool": "http_probe", "url": resp.url, "method": method,
                "status": resp.status, "elapsed_ms": elapsed_ms, "headers": headers,
                "content_length": headers.get("Content-Length"),
                "body_snippet": snippet, "body_truncated": len(body) > _SNIPPET_CAP,
            }
    except urllib.error.HTTPError as e:
        return {"tool": "http_probe", "url": url, "method": method, "status": e.code,
                "elapsed_ms": int((time.monotonic() - started) * 1000),
                "error_reason": str(e.reason), "ok": True}  # a response IS a probe result
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"ok": False, "tool": "http_probe", "url": url,
                "error": f"unreachable: {getattr(e, 'reason', e)}"}
