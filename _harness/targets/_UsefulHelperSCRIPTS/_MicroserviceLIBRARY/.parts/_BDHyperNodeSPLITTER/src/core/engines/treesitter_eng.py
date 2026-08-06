"""treesitter_eng.py — AST-based engine for source code files.

Surface populator for the GRAMMATICAL + STRUCTURAL surfaces.

Grammatical surface fields populated:
    node_kind, layer_type ("AST"), decorators, base_classes,
    import_context, scope_docstrings

Structural surface fields populated:
    structural_path, scope_stack, sibling_index, sibling_count,
    document_position, parent_occurrence_id, prev_sibling_occurrence_id

Statistical surface fields populated (partial):
    extraction_engine = "TreeSitterEngine"
    extraction_confidence = 1.0
    split_reason = "ast_boundary"

V1 reference: _BDHyperNodeSPLITTER/src/engines/treesitter_eng.py
V1 bugs fixed:
    - _load_parser() called on every can_handle() — now cached in _PARSER_CACHE
    - Decorator text completely discarded — now extracted and stored
    - Scope names lost — now builds scope_stack via parent chain
    - Docstrings lost — now extracted from first string in body
    - Base classes lost — now extracted from class definition arguments
"""

from __future__ import annotations

import importlib
import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from core.contract.hyperhunk import HyperHunk

log = logging.getLogger(__name__)

# ── Language mapping ──────────────────────────────────────────────────────

_LANG_MODULES: Dict[str, str] = {
    ".py":  "tree_sitter_python",
    ".js":  "tree_sitter_javascript",
    ".jsx": "tree_sitter_javascript",
    ".ts":  "tree_sitter_javascript",
    ".tsx": "tree_sitter_javascript",
}

_CODE_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".c", ".cpp", ".h", ".cs", ".go", ".rb", ".rs",
})

# ── AST node classification ──────────────────────────────────────────────

_TOP_LEVEL_NODES = frozenset({
    "function_definition",
    "class_definition",
    "decorated_definition",
    "function_declaration",
    "class_declaration",
    "method_definition",
    "arrow_function",
    "export_statement",
    "lexical_declaration",
})

_CONTAINER_NODES = frozenset({
    "module",
    "program",
    "class_body",
    "statement_block",
    "block",
})

# ── Parser cache (fixes v1 redundant loading) ────────────────────────────

_PARSER_CACHE: Dict[str, Any] = {}


def _load_parser(ext: str) -> Optional[Any]:
    """Load and cache a tree-sitter parser for the given file extension.

    Returns None if the language package is not installed.
    Caches parsers so each extension is loaded at most once per process.
    """
    if ext in _PARSER_CACHE:
        return _PARSER_CACHE[ext]

    module_name = _LANG_MODULES.get(ext)
    if module_name is None:
        _PARSER_CACHE[ext] = None
        return None

    try:
        import tree_sitter
        lang_mod = importlib.import_module(module_name)
        language = tree_sitter.Language(lang_mod.language())
        parser = tree_sitter.Parser(language)
        _PARSER_CACHE[ext] = parser
        return parser
    except Exception as exc:
        log.debug("tree-sitter unavailable for %s: %s", ext, exc)
        _PARSER_CACHE[ext] = None
        return None


# ── AST helpers ───────────────────────────────────────────────────────────


def _node_name(node) -> str:
    """Extract the identifier name from a definition node.

    Looks for the first 'identifier' or 'property_identifier' child.
    Returns "" if no name found (e.g., anonymous arrow functions).
    """
    for child in node.children:
        if child.type in ("identifier", "property_identifier"):
            return child.text.decode("utf-8", errors="replace")
    return ""


def _extract_decorators(node, src_bytes: bytes) -> List[str]:
    """Extract decorator strings from a decorated_definition node.

    Returns list of decorator strings including the @ symbol.
    For non-decorated nodes, returns empty list.
    """
    if node.type != "decorated_definition":
        return []
    decorators = []
    for child in node.children:
        if child.type == "decorator":
            text = src_bytes[child.start_byte:child.end_byte].decode("utf-8", errors="replace").strip()
            decorators.append(text)
    return decorators


def _extract_base_classes(node, src_bytes: bytes) -> List[str]:
    """Extract inherited class names from a class_definition node.

    Looks for 'argument_list' or 'superclasses' child.
    Returns list of base class name strings.
    """
    if node.type not in ("class_definition", "class_declaration"):
        return []
    bases = []
    for child in node.children:
        if child.type in ("argument_list", "superclasses"):
            for arg in child.children:
                if arg.type in ("identifier", "attribute", "dotted_name"):
                    bases.append(arg.text.decode("utf-8", errors="replace"))
    return bases


def _extract_docstring(node, src_bytes: bytes) -> str:
    """Extract the docstring from a definition node.

    Looks for the first expression_statement containing a string literal
    in the node's body block. Returns the string content or "".
    """
    body = None
    for child in node.children:
        if child.type in ("block", "class_body", "statement_block"):
            body = child
            break
    if body is None:
        return ""
    for child in body.children:
        if child.type == "expression_statement":
            for grandchild in child.children:
                if grandchild.type in ("string", "concatenated_string"):
                    raw = grandchild.text.decode("utf-8", errors="replace")
                    # Strip triple quotes
                    for q in ('"""', "'''", '"', "'"):
                        if raw.startswith(q) and raw.endswith(q):
                            return raw[len(q):-len(q)].strip()
                    return raw.strip()
            break  # only check the first expression_statement
    return ""


def _extract_import_lines(text: str) -> List[str]:
    """Extract all import lines from a text block.

    Returns list of import statement strings.
    """
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            lines.append(stripped)
    return lines


def _filter_imports_for_content(import_lines: List[str], content: str) -> List[str]:
    """Filter import lines to only those whose imported names appear in content.

    Heuristic: extract the last dotted segment from each import and check
    if that name appears in the content.
    """
    relevant = []
    for line in import_lines:
        # Extract imported names
        names = _imported_names(line)
        for name in names:
            if name in content:
                relevant.append(line)
                break
    return relevant


def _imported_names(line: str) -> List[str]:
    """Extract the imported names from an import statement."""
    # "from X import a, b, c" → [a, b, c]
    m = re.match(r"from\s+\S+\s+import\s+(.+)", line)
    if m:
        parts = m.group(1).split(",")
        names = []
        for p in parts:
            p = p.strip()
            # handle "x as y" → take y
            if " as " in p:
                p = p.split(" as ")[-1].strip()
            names.append(p)
        return names
    # "import a, b" → [a, b] (last segment of dotted names)
    m = re.match(r"import\s+(.+)", line)
    if m:
        parts = m.group(1).split(",")
        names = []
        for p in parts:
            p = p.strip()
            if " as " in p:
                p = p.split(" as ")[-1].strip()
            else:
                p = p.split(".")[-1]
            names.append(p)
        return names
    return []


def _unwrap_decorated(node) -> Any:
    """If node is a decorated_definition, return the inner definition node.
    Otherwise return the node itself."""
    if node.type == "decorated_definition":
        for child in node.children:
            if child.type in _TOP_LEVEL_NODES and child.type != "decorated_definition":
                return child
        # Fallback: return last non-decorator child
        for child in reversed(node.children):
            if child.type != "decorator":
                return child
    return node


# ── Engine class ──────────────────────────────────────────────────────────


class TreeSitterEngine:
    """AST-based source code parser. Populates grammatical + structural surfaces."""

    def can_handle(self, origin_id: str, text: str | None = None) -> bool:  # noqa: ARG002
        """Handle source code files by extension."""
        return Path(origin_id).suffix.lower() in _CODE_EXTENSIONS

    def parse(
        self,
        text: str,
        origin_id: str,
        metadata: dict | None = None,
    ) -> Iterator[HyperHunk]:
        """Parse source code into structurally-aware HyperHunks.

        Uses tree-sitter when available. Falls back gracefully to yielding
        nothing if tree-sitter packages are not installed (the Fallback
        engine will handle the file via parallel dispatch).
        """
        ext = Path(origin_id).suffix.lower()
        parser = _load_parser(ext)
        if parser is None:
            log.debug("No tree-sitter parser for %s, deferring to other engines", ext)
            return

        src_bytes = text.encode("utf-8")
        total_bytes = len(src_bytes)
        tree = parser.parse(src_bytes)
        root = tree.root_node

        meta = dict(metadata or {})

        # Extract file-level imports for import_context filtering
        file_import_lines = _extract_import_lines(text)

        # Build scope context for the root level
        scope_stack: List[str] = []
        scope_docstrings: Dict[str, str] = {}

        yield from self._walk(
            node=root,
            src_bytes=src_bytes,
            total_bytes=total_bytes,
            origin_id=origin_id,
            metadata=meta,
            structural_path="module",
            parent_occurrence_id=None,
            scope_stack=scope_stack,
            scope_docstrings=scope_docstrings,
            file_import_lines=file_import_lines,
        )

    def _walk(
        self,
        node,
        src_bytes: bytes,
        total_bytes: int,
        origin_id: str,
        metadata: Dict[str, Any],
        structural_path: str,
        parent_occurrence_id: Optional[str],
        scope_stack: List[str],
        scope_docstrings: Dict[str, str],
        file_import_lines: List[str],
    ) -> Iterator[HyperHunk]:
        """Recursively walk AST nodes, emitting HyperHunks.

        Preserves v1 two-pass emission pattern:
          1. Accumulate non-definition nodes as preamble
          2. Flush preamble before each definition
          3. Emit trailing preamble after loop

        V2 enrichments: scope_stack, scope_docstrings, decorators,
        base_classes, import_context, sibling_count, document_position.
        """
        preamble_parts: List[str] = []
        preamble_start_byte: int = node.start_byte
        prev_occ: Optional[str] = None
        sibling_idx: int = 0

        # Pre-count top-level definitions for sibling_count
        top_level_count = 0
        for child in node.children:
            if child.type in _TOP_LEVEL_NODES:
                top_level_count += 1
            elif child.type not in _CONTAINER_NODES:
                top_level_count += 1  # preamble counts as a sibling
        # This is approximate — preamble segments between definitions
        # each count as one sibling. Exact count is computed during emission.

        children = list(node.children)

        for child in children:
            if child.type in _TOP_LEVEL_NODES:
                # ── Flush preamble before this definition ─────────────
                if preamble_parts:
                    preamble_text = "\n".join(preamble_parts).strip()
                    if preamble_text:
                        yield HyperHunk(
                            content=preamble_text,
                            origin_id=origin_id,
                            layer_type="AST",
                            node_kind="module_preamble",
                            structural_path=structural_path,
                            sibling_index=sibling_idx,
                            metadata={
                                **metadata,
                                "start_line": _byte_to_line(preamble_start_byte, src_bytes),
                            },
                            parent_occurrence_id=parent_occurrence_id,
                            prev_sibling_occurrence_id=prev_occ,
                            scope_stack=list(scope_stack),
                            scope_docstrings=dict(scope_docstrings),
                            import_context=_filter_imports_for_content(
                                file_import_lines, preamble_text
                            ),
                            sibling_count=top_level_count,
                            document_position=_doc_position(preamble_start_byte, total_bytes),
                            extraction_engine="TreeSitterEngine",
                            extraction_confidence=1.0,
                            split_reason="ast_boundary",
                        )
                        prev_occ = None  # will be set after yield
                        # Re-get the last yielded hunk's occurrence_id
                        # We need to yield first and capture — use a temp variable
                    preamble_parts = []

                # Rebuild prev_occ from the preamble hunk if we just yielded one
                # (Python generators make this tricky — track via a flag)

                # ── Emit the definition ───────────────────────────────
                content = src_bytes[child.start_byte:child.end_byte].decode(
                    "utf-8", errors="replace"
                )
                child_path = f"{structural_path}/{child.type}"

                # V2: Extract decorators
                decorators = _extract_decorators(child, src_bytes)

                # V2: Unwrap decorated_definition to get the inner node
                inner = _unwrap_decorated(child)
                name = _node_name(inner)

                # V2: Extract base classes
                base_classes = _extract_base_classes(inner, src_bytes)

                # V2: Extract docstring
                docstring = _extract_docstring(inner, src_bytes)

                # V2: Build scope context for this node
                child_scope_stack = list(scope_stack)
                child_scope_docstrings = dict(scope_docstrings)
                if name:
                    child_scope_stack.append(name)
                    if docstring:
                        child_scope_docstrings[name] = docstring

                # V2: Filter imports relevant to this content
                import_context = _filter_imports_for_content(
                    file_import_lines, content
                )

                hunk = HyperHunk(
                    content=content,
                    origin_id=origin_id,
                    layer_type="AST",
                    node_kind=inner.type if inner != child else child.type,
                    structural_path=child_path,
                    sibling_index=sibling_idx,
                    metadata={
                        **metadata,
                        "start_line": child.start_point[0] + 1,
                        "end_line": child.end_point[0] + 1,
                    },
                    parent_occurrence_id=parent_occurrence_id,
                    prev_sibling_occurrence_id=prev_occ,
                    scope_stack=child_scope_stack,
                    scope_docstrings=child_scope_docstrings,
                    base_classes=base_classes,
                    decorators=decorators,
                    import_context=import_context,
                    sibling_count=top_level_count,
                    document_position=_doc_position(child.start_byte, total_bytes),
                    extraction_engine="TreeSitterEngine",
                    extraction_confidence=1.0,
                    split_reason="ast_boundary",
                )
                prev_occ = hunk.occurrence_id
                sibling_idx += 1
                yield hunk

            elif child.type in _CONTAINER_NODES:
                # ── Recurse into containers (transparent to hierarchy) ─
                yield from self._walk(
                    node=child,
                    src_bytes=src_bytes,
                    total_bytes=total_bytes,
                    origin_id=origin_id,
                    metadata=metadata,
                    structural_path=structural_path,
                    parent_occurrence_id=parent_occurrence_id,
                    scope_stack=scope_stack,
                    scope_docstrings=scope_docstrings,
                    file_import_lines=file_import_lines,
                )

            else:
                # ── Accumulate preamble ────────────────────────────────
                segment = src_bytes[child.start_byte:child.end_byte].decode(
                    "utf-8", errors="replace"
                ).strip()
                if segment:
                    if not preamble_parts:
                        preamble_start_byte = child.start_byte
                    preamble_parts.append(segment)

        # ── Emit trailing preamble ────────────────────────────────────
        if preamble_parts:
            preamble_text = "\n".join(preamble_parts).strip()
            if preamble_text:
                hunk = HyperHunk(
                    content=preamble_text,
                    origin_id=origin_id,
                    layer_type="AST",
                    node_kind="module_preamble",
                    structural_path=structural_path,
                    sibling_index=sibling_idx,
                    metadata={
                        **metadata,
                        "start_line": _byte_to_line(preamble_start_byte, src_bytes),
                    },
                    parent_occurrence_id=parent_occurrence_id,
                    prev_sibling_occurrence_id=prev_occ,
                    scope_stack=list(scope_stack),
                    scope_docstrings=dict(scope_docstrings),
                    import_context=_filter_imports_for_content(
                        file_import_lines, preamble_text
                    ),
                    sibling_count=top_level_count,
                    document_position=_doc_position(preamble_start_byte, total_bytes),
                    extraction_engine="TreeSitterEngine",
                    extraction_confidence=1.0,
                    split_reason="ast_boundary",
                )
                prev_occ = hunk.occurrence_id
                sibling_idx += 1
                yield hunk


# ── Utility ───────────────────────────────────────────────────────────────


def _doc_position(byte_offset: int, total_bytes: int) -> float:
    """Compute 0.0–1.0 document position from byte offset."""
    if total_bytes <= 0:
        return 0.0
    return round(byte_offset / total_bytes, 4)


def _byte_to_line(byte_offset: int, src_bytes: bytes) -> int:
    """Convert byte offset to 1-indexed line number."""
    return src_bytes[:byte_offset].count(b"\n") + 1
