"""
FILE:       tools/symbol_graph_shared.py
ROLE:       The resolved symbol graph - who actually refers to whom, not who shares a name.
DOMAIN:     tool (shared substrate)
DOES:       build_graph(root): parse the target's Python, build per-file BINDING TABLES (local
            defs + imports, with relative imports resolved against the real package path), and
            emit nodes (modules, symbols) + edges (import / ref) where every edge is RESOLVED -
            plus an honest ledger of what could NOT be resolved (star imports, dynamic imports,
            getattr) and a FUZZY attribute-name layer kept separate from the resolved facts.
DEPENDS ON: tools.code_intel_shared (parse/walk substrate); (stdlib) ast, collections
WIRES TO:   tools/symbol_graph (the query tool), tools/dead_code (two-tier reachability +
            resolved base classes for interface-override roots), tools/domain_boundary_audit
            (resolved module edges).
NOTES:      The predecessor evidence was a bag of names: any file mentioning `run` kept every
            `run` in the project alive, and two dead functions calling each other read as
            referenced. Both are the same defect - counting name coincidence as evidence. This
            module's contract is that an edge EXISTS only when the reference actually binds to
            that target through an import or a local definition; everything weaker is either in
            `fuzzy_attr_uses` (name-level attribute evidence, clearly labelled) or in
            `unresolved` (constructs static analysis cannot see). Consumers state their limits
            FROM those ledgers instead of pretending completeness.
"""
from __future__ import annotations

import ast
from collections import Counter

from tools.code_intel_shared import (
    ParsedFile,
    module_name,
    parse_python_files,
)


def _module_of(parsed: ParsedFile, root) -> str:
    try:
        return module_name(root, parsed.path)
    except ValueError:
        return parsed.rel.rsplit(".py", 1)[0].replace("/", ".")


def _resolve_relative(base_module: str, level: int, module: str | None, *, is_package: bool) -> str:
    """Resolve `from ..x import y` against the importing module's REAL package path.

    level=1 is the current package, each further level climbs one. A package's __init__ counts
    as one level shallower than a plain module. Returns "" when the climb walks off the top -
    that is a broken import, not something to guess at.
    """
    parts = base_module.split(".") if base_module else []
    # For a plain module, level 1 = its containing package = drop the module segment.
    # For a package __init__ (module name IS the package), level 1 = itself.
    drop = level if not is_package else level - 1
    if drop > len(parts):
        return ""
    anchor = parts[: len(parts) - drop] if drop else parts
    if module:
        anchor = anchor + module.split(".")
    return ".".join(anchor)


class _FileFacts(ast.NodeVisitor):
    """One pass over one file: definitions, bindings, uses, and the honesty ledger."""

    def __init__(self, rel: str, module: str, is_package: bool):
        self.rel = rel
        self.module = module
        self.is_package = is_package
        # name -> ("module", dotted_module) | ("symbol", module, symbol_name)
        self.bindings: dict[str, tuple] = {}
        self.symbols: list[dict] = []      # defs in this file
        self.imports: list[dict] = []      # raw import records (module-level edges)
        self.name_uses: list[tuple[str, str, int]] = []   # (name, context_qualname, line)
        self.attr_uses: list[tuple[str, str, str, int]] = []  # (dotted_base, attr, context, line)
        self.exports: set[str] = set()     # names in __all__
        self.class_bases: list[tuple[str, str]] = []   # (class_qualname, base name/dotted)
        self.unresolved = Counter()        # star_import / dynamic_import / getattr
        self._stack: list[str] = []        # enclosing def/class qualname parts
        self._class_depth = 0

    # -- context helpers ---------------------------------------------------------------
    def _ctx(self) -> str:
        return ".".join(self._stack)  # "" = module top level

    def _add_symbol(self, node, kind: str) -> None:
        qual = ".".join([*self._stack, node.name])
        decos = []
        for d in getattr(node, "decorator_list", []):
            f = d.func if isinstance(d, ast.Call) else d
            if isinstance(f, ast.Attribute):
                decos.append(f.attr)   # @app.command -> "command"
            elif isinstance(f, ast.Name):
                decos.append(f.id)
        self.symbols.append({
            "name": node.name, "qualname": qual, "kind": kind,
            "line_start": int(node.lineno), "line_end": int(getattr(node, "end_lineno", node.lineno)),
            "decorators": decos,
        })

    # -- definitions -------------------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._add_symbol(node, "class")
        if not self._stack:
            self.bindings[node.name] = ("symbol", self.module, node.name)
        # record base-class names so inheritance can be resolved (ABC overrides are live)
        qual = ".".join([*self._stack, node.name])
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.class_bases.append((qual, base.id))
            elif isinstance(base, ast.Attribute):
                parts, cur = [], base
                while isinstance(cur, ast.Attribute):
                    parts.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    parts.append(cur.id)
                    self.class_bases.append((qual, ".".join(reversed(parts))))
        # bases, decorators, keywords execute in the ENCLOSING context (before the push)
        for expr in [*node.bases, *node.decorator_list, *[k.value for k in node.keywords]]:
            self.visit(expr)
        self._stack.append(node.name)
        self._class_depth += 1
        for child in node.body:
            self.visit(child)
        self._class_depth -= 1
        self._stack.pop()

    def _visit_func(self, node, kind_free: str, kind_method: str) -> None:
        kind = kind_method if self._class_depth else kind_free
        self._add_symbol(node, kind)
        if not self._stack:
            self.bindings[node.name] = ("symbol", self.module, node.name)
        # decorators, defaults, annotations execute at DEF time in the enclosing context
        pre: list = [*node.decorator_list, *node.args.defaults]
        pre += [d for d in node.args.kw_defaults if d is not None]
        pre += [a.annotation for a in
                [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
                if a.annotation is not None]
        if node.returns is not None:
            pre.append(node.returns)
        for expr in pre:
            self.visit(expr)
        self._stack.append(node.name)
        for child in node.body:
            self.visit(child)
        self._stack.pop()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_func(node, "function", "method")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_func(node, "async_function", "async_method")

    # -- imports -----------------------------------------------------------------------
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            top = alias.name.split(".", 1)[0]
            bound = alias.asname or top
            target = alias.name if alias.asname else top
            self.bindings[bound] = ("module", target)
            self.imports.append({"module": alias.name, "line": node.lineno, "level": 0})

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.level:
            base = _resolve_relative(self.module, node.level, node.module,
                                     is_package=self.is_package)
        else:
            base = node.module or ""
        if not base:
            self.unresolved["broken_relative_import"] += 1
            return
        self.imports.append({"module": base, "line": node.lineno, "level": node.level})
        for alias in node.names:
            if alias.name == "*":
                self.unresolved["star_import"] += 1
                continue
            bound = alias.asname or alias.name
            # `from pkg import thing` - thing is a symbol OF pkg or the submodule pkg.thing;
            # record both candidates and let resolution pick whichever exists in the graph.
            self.bindings[bound] = ("symbol_or_module", base, alias.name)

    # -- uses --------------------------------------------------------------------------
    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load):
            self.name_uses.append((node.id, self._ctx(), int(node.lineno)))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Flatten a.b.c -> (dotted_base, final_attr). When the chain bottoms out in something
        # that is not a bare Name (a call result, a subscript), the attr is honestly fuzzy AND
        # the base expression still gets visited - `foo().bar` must not lose the use of `foo`.
        parts: list[str] = []
        cur: ast.AST = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        line = int(getattr(node, "lineno", 1) or 1)
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            parts.reverse()
            self.attr_uses.append((".".join(parts[:-1]), parts[-1], self._ctx(), line))
        else:
            self.attr_uses.append(("", node.attr, self._ctx(), line))
            self.visit(cur)  # keep walking the non-Name base

    def visit_Assign(self, node: ast.Assign) -> None:
        if not self._stack:  # module-level __all__ only
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "__all__":
                    for elt in getattr(node.value, "elts", []):
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                            self.exports.add(elt.value)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        f = node.func
        if isinstance(f, ast.Name) and f.id in {"getattr", "globals", "eval", "exec", "__import__"}:
            self.unresolved["dynamic_dispatch"] += 1
        if isinstance(f, ast.Attribute) and f.attr == "import_module":
            self.unresolved["dynamic_import"] += 1
        self.generic_visit(node)


def build_graph(root, *, max_files: int = 2000) -> dict:
    """The whole graph in one pass. Returns:

    modules:  {module: {"path": rel, "package": bool}}
    symbols:  {sym_id: {...}}  where sym_id = "<module>::<qualname>"
    imports:  [{"src": module, "dst": module, "line": n}]           (internal, resolved)
    refs:     [{"src": ctx_id, "dst": sym_id, "line": n}]           (resolved name/attr refs;
              ctx_id is a sym_id or "<module>::" for module top-level code)
    fuzzy_attr_uses: {attr_name: count}   (attribute evidence that could not be bound to a
              target - the name-level layer, deliberately separate from `refs`)
    unresolved: {construct: count}        (what static analysis cannot see)
    external_imports: {top_level_name: count}
    """
    parsed = parse_python_files(root, max_files=max_files)
    facts: list[_FileFacts] = []
    modules: dict[str, dict] = {}
    for p in parsed:
        if p.tree is None:
            continue
        is_pkg = p.rel.endswith("__init__.py")
        mod = _module_of(p, root)
        ff = _FileFacts(p.rel, mod, is_pkg)
        ff.visit(p.tree)
        facts.append(ff)
        modules[mod] = {"path": p.rel, "package": is_pkg, "exports": sorted(ff.exports)}

    # Global symbol table: (module, top_level_name) and full qualnames.
    symbols: dict[str, dict] = {}
    top_level: dict[tuple[str, str], str] = {}
    by_qual: dict[tuple[str, str], str] = {}
    for ff in facts:
        for s in ff.symbols:
            sid = f"{ff.module}::{s['qualname']}"
            symbols[sid] = {**s, "module": ff.module, "path": ff.rel}
            by_qual[(ff.module, s["qualname"])] = sid
            if "." not in s["qualname"]:
                top_level[(ff.module, s["name"])] = sid

    def _sym(module: str, dotted: str) -> str | None:
        """Find `dotted` (name or Class.method) defined in `module`."""
        return by_qual.get((module, dotted)) or top_level.get((module, dotted.split(".", 1)[0]))

    imports: list[dict] = []
    refs: list[dict] = []
    fuzzy = Counter()
    unresolved = Counter()
    external = Counter()

    # When the scanned root is itself a package (root=src, files import `src.core.config`),
    # internal modules are named relative to the root (`core.config`) while the imports carry
    # the root's own name as a prefix. Tolerate that prefix as an ALIAS - after the exact form
    # fails - so a subtree scan still resolves its own absolute imports. The predecessor had
    # this via an aliases dict; dropping it silently zeroed the boundary audit on src/.
    root_pkg = getattr(root, "name", "") or ""

    def _forms(target: str):
        yield target
        if root_pkg and target.startswith(root_pkg + "."):
            yield target[len(root_pkg) + 1:]

    def _norm_module(target: str) -> str | None:
        """`target` as an EXACT internal module, tolerating the root-name prefix."""
        return next((f for f in _forms(target) if f in modules), None)

    def _resolve_binding(ff: _FileFacts, name: str):
        """A bound name -> ("module", mod) | ("symbol", sid) | None."""
        b = ff.bindings.get(name)
        if b is None:
            return None
        if b[0] == "module":
            mod = _norm_module(b[1])
            return ("module", mod) if mod else None
        if b[0] == "symbol":
            sid = _sym(b[1], b[2])
            return ("symbol", sid) if sid else None
        # symbol_or_module: prefer the defined symbol, fall back to the submodule
        base = _norm_module(b[1])
        sid = _sym(base, b[2]) if base else None
        if sid:
            return ("symbol", sid)
        sub = _norm_module(f"{b[1]}.{b[2]}")
        if sub:
            return ("module", sub)
        return None

    for ff in facts:
        unresolved.update(ff.unresolved)
        ctx_prefix = f"{ff.module}::"

        # resolve base classes onto the class symbols (inheritance edges for consumers)
        for cls_qual, base_name in ff.class_bases:
            cls_id = by_qual.get((ff.module, cls_qual))
            if cls_id is None:
                continue
            head, _, rest = base_name.partition(".")
            r = _resolve_binding(ff, head)
            base_sid = None
            if r and r[0] == "symbol" and not rest:
                base_sid = r[1]
            elif r and r[0] == "module" and rest:
                base_sid = _sym(r[1], rest)
            elif not rest:
                base_sid = top_level.get((ff.module, head))
            if base_sid:
                symbols[cls_id].setdefault("bases", []).append(base_sid)

        for imp in ff.imports:
            target = imp["module"]
            # longest internal prefix: `import a.b.c` links to the deepest module we own;
            # each alias form gets the same walk
            hit = None
            for form in _forms(target):
                parts = form.split(".")
                hit = next((".".join(parts[:i]) for i in range(len(parts), 0, -1)
                            if ".".join(parts[:i]) in modules), None)
                if hit:
                    break
            if hit and hit != ff.module:
                imports.append({"src": ff.module, "dst": hit, "line": imp["line"]})
            elif not hit:
                external[target.split(".", 1)[0]] += 1

        def _ctx_id(ctx: str) -> str:
            return by_qual.get((ff.module, ctx), ctx_prefix) if ctx else ctx_prefix

        def _local_lookup(ctx: str, name: str) -> str | None:
            """A nested def/class referenced by bare name from inside an enclosing scope -
            `def outer(): def walk(): ... walk()` - resolves lexically, not through imports."""
            parts = ctx.split(".") if ctx else []
            while parts:
                sid = by_qual.get((ff.module, ".".join(parts) + "." + name))
                if sid:
                    return sid
                parts.pop()
            return None

        for name, ctx, line in ff.name_uses:
            target = _local_lookup(ctx, name)
            if target is None:
                r = _resolve_binding(ff, name)
                target = r[1] if r and r[0] == "symbol" else None
            if target and target != by_qual.get((ff.module, ctx)):
                refs.append({"src": _ctx_id(ctx), "dst": target, "line": line})

        for base, attr, ctx, line in ff.attr_uses:
            if base:
                head = base.split(".", 1)
                r = _resolve_binding(ff, head[0])
                if r and r[0] == "module":
                    # module.attr or module.sub.attr -> symbol in that module
                    dotted = (head[1] + "." + attr) if len(head) > 1 else attr
                    mod = r[1]
                    # walk submodule chain: pkg.sub.func with `import pkg`
                    seg = dotted.split(".")
                    for i in range(len(seg) - 1, 0, -1):
                        cand = mod + "." + ".".join(seg[:i])
                        if cand in modules:
                            mod, seg = cand, seg[i:]
                            break
                    sid = _sym(mod, ".".join(seg))
                    if sid:
                        refs.append({"src": _ctx_id(ctx), "dst": sid, "line": line})
                        continue
                elif r and r[0] == "symbol":
                    # attribute on an imported CLASS: Class.method / instance-typed too deep;
                    # credit the class (resolved) and the method name (fuzzy)
                    refs.append({"src": _ctx_id(ctx), "dst": r[1], "line": line})
                    fuzzy[attr] += 1
                    continue
            fuzzy[attr] += 1

    return {
        "root": str(root),
        "file_count": len(parsed),
        "modules": modules,
        "symbols": symbols,
        "imports": imports,
        "refs": refs,
        "fuzzy_attr_uses": dict(fuzzy),
        "unresolved": dict(unresolved),
        "external_imports": dict(external),
        "parse_errors": [{"path": p.rel, "error": p.error} for p in parsed if p.error],
    }


def reachable_symbols(graph: dict, roots: set[str], *,
                      assume_method_dispatch: bool = False) -> set[str]:
    """BFS over resolved edges from the root set.

    Reaching a symbol pulls in the refs made FROM that symbol's body. Module top-level code
    (ctx "<module>::") is always live - importing the module executes it - which keeps this
    conservative: nothing actually invoked at import time can read as dead.

    Two tiers, because dynamic dispatch is real but not proof:
    - strict (default): reaching a class pulls in only its lifecycle dunders (they run whenever
      the class is used). Ordinary methods need a real reference - the distinction the
      name-coincidence approach could not make.
    - assume_method_dispatch=True: reaching a class pulls in ALL its members, modelling
      frameworks that getattr their way to methods (ast.NodeVisitor's visit_*, handler
      registries). A symbol live only under THIS assumption is a medium lead, never proof of
      life - and one dead under it too is dead under every assumption we can model.
    """
    by_src: dict[str, list[str]] = {}
    for r in graph["refs"]:
        by_src.setdefault(r["src"], []).append(r["dst"])

    symbols = graph["symbols"]
    # class -> members pulled in when the class itself becomes reachable
    members: dict[str, list[str]] = {}
    for sid, s in symbols.items():
        if "." in s["qualname"]:
            cls_qual = s["qualname"].rsplit(".", 1)[0]
            cls_id = f"{s['module']}::{cls_qual}"
            is_lifecycle = s["name"].startswith("__") and s["name"].endswith("__")
            if is_lifecycle or assume_method_dispatch:
                members.setdefault(cls_id, []).append(sid)

    live = set()
    queue = list(roots)
    # every module's top-level context is live
    queue.extend(f"{m}::" for m in graph["modules"])
    while queue:
        node = queue.pop()
        if node in live:
            continue
        live.add(node)
        queue.extend(by_src.get(node, ()))
        queue.extend(members.get(node, ()))
    return {n for n in live if not n.endswith("::")}


def module_import_edges(root, *, max_files: int = 2000) -> tuple[list[dict], dict]:
    """Just the resolved internal module->module edges (for the boundary audit), plus the
    honesty ledger. Relative imports are resolved against the real package path - the
    predecessor's `lstrip('.')` guess attributed `from ..core import x` to a TOP-LEVEL `core`
    whether or not that was the anchor package."""
    g = build_graph(root, max_files=max_files)
    return g["imports"], {"unresolved": g["unresolved"], "parse_errors": g["parse_errors"],
                          "modules": g["modules"], "file_count": g["file_count"]}
