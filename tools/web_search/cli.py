"""
FILE:       tools/web_search/cli.py
ROLE:       Governed web search  -  discovery through the seam, audit-logged like everything else.
DOMAIN:     tool
DOES:       Preview-first: report WHICH provider and endpoint the query would be sent to (an
            outbound disclosure deserves a look before it happens), then on apply run the search
            and return normalised {title, url, snippet} results. Optional evidence:true grounds
            the results in the Bag of Evidence.
DEPENDS ON: tools._toolkit, (stdlib) json, os, urllib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Provider behind a thin ADAPTER so the tool is not welded to one service. Configure via
            SUITE_SEARCH_PROVIDER (searxng|brave|tavily) + SUITE_SEARCH_URL / SUITE_SEARCH_API_KEY.
            With none configured it says so plainly and returns ok:false  -  it never fabricates
            results, the same honesty stance as the embedding/summary backends.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from tools._toolkit import apply_with, attach_evidence, confirmed, tool_main

_TIMEOUT = 20
_MAX_RESULTS = 25

PROVIDER = os.environ.get("SUITE_SEARCH_PROVIDER", "").strip().lower()
API_KEY = os.environ.get("SUITE_SEARCH_API_KEY", "").strip()
SEARCH_URL = os.environ.get("SUITE_SEARCH_URL", "").strip()

_CONFIG_HELP = ("set SUITE_SEARCH_PROVIDER to one of searxng|brave|tavily "
                "(searxng also needs SUITE_SEARCH_URL; brave/tavily need SUITE_SEARCH_API_KEY)")


def _endpoint() -> tuple[str, str]:
    """(endpoint, error) for the configured provider  -  no network contact."""
    if not PROVIDER:
        return "", f"no search provider configured: {_CONFIG_HELP}"
    if PROVIDER == "searxng":
        if not SEARCH_URL:
            return "", f"searxng needs SUITE_SEARCH_URL: {_CONFIG_HELP}"
        return SEARCH_URL.rstrip("/") + "/search", ""
    if PROVIDER == "brave":
        if not API_KEY:
            return "", f"brave needs SUITE_SEARCH_API_KEY: {_CONFIG_HELP}"
        return "https://api.search.brave.com/res/v1/web/search", ""
    if PROVIDER == "tavily":
        if not API_KEY:
            return "", f"tavily needs SUITE_SEARCH_API_KEY: {_CONFIG_HELP}"
        return "https://api.tavily.com/search", ""
    return "", f"unknown provider {PROVIDER!r}: {_CONFIG_HELP}"


def _request(endpoint: str, query: str, limit: int):
    """Provider adapter -> a urllib Request. One place per service; add a provider here only."""
    if PROVIDER == "searxng":
        qs = urllib.parse.urlencode({"q": query, "format": "json"})
        return urllib.request.Request(f"{endpoint}?{qs}", headers={"Accept": "application/json"})
    if PROVIDER == "brave":
        qs = urllib.parse.urlencode({"q": query, "count": limit})
        return urllib.request.Request(f"{endpoint}?{qs}", headers={
            "Accept": "application/json", "X-Subscription-Token": API_KEY})
    # tavily
    body = json.dumps({"api_key": API_KEY, "query": query, "max_results": limit}).encode()
    return urllib.request.Request(endpoint, data=body, method="POST",
                                  headers={"Content-Type": "application/json"})


def _normalise(payload: dict, limit: int) -> list[dict]:
    """Provider-shaped JSON -> a uniform result list, so callers never branch on provider."""
    rows = []
    if PROVIDER == "searxng":
        rows = [{"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
                for r in (payload.get("results") or [])]
    elif PROVIDER == "brave":
        rows = [{"title": r.get("title"), "url": r.get("url"), "snippet": r.get("description")}
                for r in ((payload.get("web") or {}).get("results") or [])]
    elif PROVIDER == "tavily":
        rows = [{"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content")}
                for r in (payload.get("results") or [])]
    return [r for r in rows if r.get("url")][:limit]


@tool_main
def run(args: dict) -> dict:
    query = str(args.get("query") or "").strip()
    if not query:
        return {"ok": False, "error": "query is required"}
    limit = max(1, min(int(args.get("limit", 8)), _MAX_RESULTS))
    endpoint, err = _endpoint()
    if err:
        return {"ok": False, "tool": "web_search", "error": err, "provider": PROVIDER or None,
                "configure": _CONFIG_HELP}

    plan = {"tool": "web_search", "provider": PROVIDER, "endpoint": endpoint,
            "query": query, "limit": limit}
    if not confirmed(args):
        # An outbound disclosure: show what would leave the machine, and where, before it does.
        return {**plan, "dry_run": True, "searched": False,
                "note": "the query above would be sent to this endpoint",
                "apply_with": apply_with()}

    try:
        with urllib.request.urlopen(_request(endpoint, query, limit), timeout=_TIMEOUT) as resp:
            payload = json.loads(resp.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, ValueError) as e:
        return {**plan, "ok": False, "searched": False,
                "error": f"{type(e).__name__}: {str(e)[:200]}"}

    results = _normalise(payload, limit)
    out = {**plan, "dry_run": False, "searched": True, "count": len(results), "results": results}
    if args.get("evidence"):
        out["evidence_id"] = attach_evidence(
            f"web_search: {query[:80]}", json.dumps(results, ensure_ascii=False))
    return out
