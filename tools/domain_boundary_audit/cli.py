"""
FILE:       tools/domain_boundary_audit/cli.py
ROLE:       Python domain/layer boundary auditor.
DOMAIN:     tool
DOES:       Groups Python modules by top-level directory/package and reports internal imports
            crossing those boundaries, with allowed/dependency-direction summaries.
DEPENDS ON: tools._toolkit, tools.code_intel_shared, tools.symbol_graph_shared
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json
NOTES:      Layer policy must come from the project, not from this tool. Absent a
            policy its output is a lead, not a verdict. See _design/CHARTER.md sec 4.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from tools._toolkit import project_root, suite_home, tool_main
from tools.code_intel_shared import resolve_root
from tools.symbol_graph_shared import module_import_edges

_POLICY_FILE = ".uh-policy.json"
_PROFILE_DIR = Path("config") / "domain-boundary"
_PROFILE_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def _domain(module: str) -> str:
    return module.split(".", 1)[0] if module else "(root)"


def _available_profiles() -> list[str]:
    try:
        return sorted(
            path.stem for path in (suite_home() / _PROFILE_DIR).glob("*.json") if path.is_file()
        )
    except OSError:
        return []


def _read_policy(path: Path, source: str):
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return None, source, f"cannot read boundary policy {source}: {exc}"
    except json.JSONDecodeError as exc:
        return None, source, f"invalid JSON in boundary policy {source}: {exc}"
    if not isinstance(policy, dict):
        return None, source, f"boundary policy {source} must contain a JSON object"
    return policy, source, None


def _load_policy(args: dict):
    """Load an inline, sidecar-owned, or legacy project-owned policy.

    Precedence: inline policy, inline allowed_edges, policy_profile,
    project-root .uh-policy.json, then none.
    """
    policy = args.get("policy")
    if "policy" in args:
        if not isinstance(policy, dict):
            return None, "inline:policy", "policy must be a JSON object"
        return policy, "inline:policy", None

    if args.get("allowed_edges"):
        return {"allowed_edges": args["allowed_edges"]}, "inline:allowed_edges", None

    profile = args.get("policy_profile")
    if profile is not None:
        name = str(profile).strip()
        source = f"profile:{name}"
        if not _PROFILE_NAME.fullmatch(name):
            return (
                None,
                source,
                (
                    "policy_profile must be 1-64 characters using letters, digits, hyphens, "
                    "or underscores"
                ),
            )

        base = (suite_home() / _PROFILE_DIR).resolve()
        path = (base / f"{name}.json").resolve()
        if not path.is_relative_to(base):
            return None, source, "policy_profile resolves outside the profile directory"
        if not path.is_file():
            return None, source, f"boundary policy profile not found: {name}"
        return _read_policy(path, source)

    policy_file = project_root() / _POLICY_FILE
    if policy_file.is_file():
        return _read_policy(policy_file, _POLICY_FILE)
    return None, "none", None


def _compile_policy(policy):
    """Compile and validate layer mappings and allowed directed edges."""
    if policy is None:
        return None, None, None

    layers = policy.get("layers", {})
    edges = policy.get("allowed_edges", [])
    if layers is None:
        layers = {}
    if edges is None:
        edges = []
    if not isinstance(layers, dict):
        return None, None, "policy.layers must be a JSON object"
    if not isinstance(edges, list) or not all(isinstance(edge, str) for edge in edges):
        return None, None, "policy.allowed_edges must be an array of strings"
    if not layers and not edges:
        return None, None, "policy must declare layers or allowed_edges"

    layer_of = {str(domain).strip(): str(layer).strip() for domain, layer in layers.items()}
    if any(not domain or not layer for domain, layer in layer_of.items()):
        return None, None, "policy layer names and domains must be non-empty"

    allowed: set[tuple[str, str]] = set()
    for edge in edges:
        if edge.count("->") != 1:
            return None, None, f"invalid policy edge {edge!r}; expected from->to"
        source, target = (part.strip() for part in edge.split("->", 1))
        if not source or not target:
            return None, None, f"invalid policy edge {edge!r}; expected from->to"
        allowed.add((source, target))
    return layer_of, allowed, None


@tool_main
def run(args: dict) -> dict:
    root, error = resolve_root(args.get("root"))
    if error:
        return {"ok": False, "error": error}
    assert root is not None

    max_files = max(1, min(int(args.get("max_files", 500)), 5000))
    available_profiles = _available_profiles()
    policy, policy_source, policy_error = _load_policy(args)
    if policy_error:
        return {
            "ok": False,
            "error": policy_error,
            "policy_source": policy_source,
            "available_policy_profiles": available_profiles,
        }

    layer_of, allowed, policy_error = _compile_policy(policy)
    if policy_error:
        return {
            "ok": False,
            "error": policy_error,
            "policy_source": policy_source,
            "available_policy_profiles": available_profiles,
        }

    has_policy = allowed is not None
    # G6: edges come from the resolved symbol graph. Relative imports are anchored against the
    # importing module's REAL package path - the previous lstrip('.') guess attributed
    # `from ..core import x` to a top-level `core` whether or not that was the anchor.
    edges, graph_meta = module_import_edges(root, max_files=max_files)
    module_paths = {m: info["path"] for m, info in graph_meta["modules"].items()}

    crossings = []
    domain_counts: Counter[str] = Counter()
    edge_counts: Counter[tuple[str, str]] = Counter()

    def _layer(domain: str):
        return layer_of.get(domain, domain) if has_policy else None

    def _verdict(src_domain: str, dst_domain: str):
        # None when no policy (a neutral fact); else True/False against the layering policy.
        if not has_policy:
            return None
        src_layer, dst_layer = _layer(src_domain), _layer(dst_domain)
        return src_layer == dst_layer or (src_layer, dst_layer) in allowed

    for module in graph_meta["modules"]:
        domain_counts[_domain(module)] += 1

    for edge in edges:
        src_module, target = edge["src"], edge["dst"]
        src_domain, dst_domain = _domain(src_module), _domain(target)
        if src_domain == dst_domain:
            continue
        crossings.append(
            {
                "from_domain": src_domain,
                "to_domain": dst_domain,
                "from_layer": _layer(src_domain),
                "to_layer": _layer(dst_domain),
                "from_module": src_module,
                "to_module": target,
                "path": module_paths.get(src_module, ""),
                "line": edge["line"],
                "import": target,
                "allowed": _verdict(src_domain, dst_domain),
            }
        )
        edge_counts[(src_domain, dst_domain)] += 1

    hotspots = [
        {
            "from_domain": source,
            "to_domain": target,
            "from_layer": _layer(source),
            "to_layer": _layer(target),
            "count": count,
            "allowed": _verdict(source, target),
        }
        for (source, target), count in edge_counts.most_common()
    ]
    violations = [crossing for crossing in crossings if crossing["allowed"] is False]
    parse_errors = graph_meta["parse_errors"]
    verdict = "policy applied" if has_policy else "none (no policy supplied)"
    unmapped_domains = sorted(
        domain for domain in domain_counts if has_policy and layer_of and domain not in layer_of
    )
    warnings = (
        []
        if has_policy
        else [
            "No layering policy supplied: crossings are reported as NEUTRAL FACTS, not "
            "violations. A crossing is only a defect against a project's declared "
            "architecture. Supply policy or allowed_edges, select a sidecar "
            f"policy_profile, or add {_POLICY_FILE} at the project root, to get pass/fail."
        ]
    )
    if unmapped_domains:
        warnings.append(
            "Policy does not map these domains; each is treated as its own strict layer: "
            + ", ".join(unmapped_domains)
        )
    policy_status = "none" if not has_policy else ("fail" if violations else "pass")

    return {
        "tool": "domain_boundary_audit",
        "root": root.as_posix(),
        "verdict": verdict,
        "policy_source": policy_source,
        "policy_name": policy.get("name") if policy else None,
        "policy_status": policy_status,
        "available_policy_profiles": available_profiles,
        "unmapped_domains": unmapped_domains,
        "domains": [
            {"domain": domain, "module_count": count}
            for domain, count in sorted(domain_counts.items())
        ],
        "crossing_count": len(crossings),
        "violation_count": len(violations) if has_policy else None,
        "violations": violations if has_policy else [],
        "crossings": crossings,
        "hotspots": hotspots,
        "parse_errors": parse_errors,
        "truncated": graph_meta["file_count"] >= max_files,
        "warnings": warnings,
        "summary": {
            "files": graph_meta["file_count"],
            "domains": len(domain_counts),
            "crossings": len(crossings),
            "violations": len(violations) if has_policy else None,
            "verdict": verdict,
            "policy_status": policy_status,
            "unmapped_domains": len(unmapped_domains),
            "parse_errors": len(parse_errors),
        },
    }
