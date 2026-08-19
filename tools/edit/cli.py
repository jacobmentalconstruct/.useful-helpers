"""
FILE:       tools/edit/cli.py
ROLE:       Headless find/replace on text or a file  -  regex or literal, with a count guard.
DOMAIN:     tool
DOES:       Replace `pattern` with `replacement` over `text` or a `path`. `literal:true` matches an
            exact string (no regex). `expected_replacements` REFUSES the write unless the count
            matches  -  so a greedy/ambiguous match can't silently change more than intended.
            Preview by default; writes back only with write:true (or apply:true) AND a `path`.
DEPENDS ON: tools._toolkit, (stdlib) re
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Path is confined to the roots. `expected_replacements` is the safety belt for exact
            edits; without it, behavior is the old regex subn (backward compatible).
            `expected_source_sha256` is the REVIEWED-SOURCE WITNESS: a preview reports the hash
            of the bytes it read, and an Apply carrying that hash refuses if the file has moved
            underneath it. See _source_witness.
"""
from __future__ import annotations

import hashlib
import io
import re

from tools._toolkit import confirmed, resolve_within_roots, tool_main

_FLAGS = {"ignorecase": re.IGNORECASE, "multiline": re.MULTILINE, "dotall": re.DOTALL}


def _source_witness(path):
    """Read the file ONCE; return (decoded text, sha256 of the bytes actually read).

    ONE READ, NOT TWO. Hashing in a separate `read_bytes()` would leave a window in which
    the witness describes a file the edit never saw - a check that introduces the race it
    exists to close.

    THE HASH IS OVER RAW BYTES, and the decode is derived from those same bytes. Hashing
    the decoded text instead would make the witness blind to any change that survives
    newline translation: `read_text` maps CRLF to LF, so a whole-file line-ending rewrite
    would hash identically to the original. The witness has to be as sensitive as the
    filesystem, not as sensitive as the parser.

    TextIOWrapper rather than `raw.decode()` because it applies the SAME universal-newline
    translation `Path.read_text()` does. Decoding directly would leave `\\r\\n` in the
    content and silently change which patterns match on Windows-authored files - a
    behaviour change smuggled in under a safety fix.
    """
    raw = path.read_bytes()
    text = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8").read()
    return text, hashlib.sha256(raw).hexdigest()


@tool_main
def run(args: dict) -> dict:
    pattern = args.get("pattern")
    replacement = args.get("replacement")
    if pattern is None or replacement is None:
        return {"ok": False, "error": "'pattern' and 'replacement' are required"}
    pattern, replacement = str(pattern), str(replacement)

    witness = None
    if args.get("text") is not None:
        content, source, path = str(args["text"]), "text", None
    elif args.get("path"):
        path, err = resolve_within_roots(args["path"])
        if err:
            return {"ok": False, "error": err}
        if not path.is_file():
            return {"ok": False, "error": f"not a file: {path}"}
        content, witness = _source_witness(path)
        source = "path"
    else:
        return {"ok": False, "error": "provide 'text' or 'path'"}

    # THE REVIEWED-SOURCE WITNESS. A caller previews a change, a human reads the diff and
    # approves it, and the Apply lands some time later. Without this the approval is bound
    # to nothing: an approved diff against state A can be applied to state B, and the bytes
    # that reach disk are bytes nobody looked at.
    #
    # Checked HERE - after the read, before any replacement or write - so a refusal cannot
    # be a report of something already done.
    #
    # AN ABSENT WITNESS IS NOT A FAILED ONE, deliberately, and this is the same distinction
    # governance draws between a missing config and an unreadable one: a caller that sent no
    # witness did not ask for the check, while a caller whose witness does not match asked
    # and got an answer. Requiring one unconditionally would break every existing caller and
    # amount to a general approval protocol, which is not what this is. Previews always
    # OFFER the witness in `apply_with`, so the governed path carries it by construction.
    expected_source = args.get("expected_source_sha256")
    if expected_source and witness and str(expected_source) != witness:
        return {"ok": False, "tool": "edit", "written": False, "changed": False,
                "source": source, "expected_source_sha256": str(expected_source),
                "actual_source_sha256": witness,
                "error": "source changed since it was previewed: refusing to apply an "
                         "approved change to bytes that were never reviewed",
                # THE REFUSAL MUST NOT HAND BACK A ROUTE AROUND ITSELF. `_hint_apply`
                # helpfully appends `apply_with: {"apply": true}` to anything reporting
                # `written: false`, and that fragment carries no witness - so an agent
                # doing the obvious thing (resend what the refusal suggested) would blow
                # straight through the check it just tripped. Set explicitly so the
                # toolkit's `setdefault` has nothing to fill in.
                #
                # Nothing applyable is offered because nothing is safely applyable: the
                # approved diff describes bytes that no longer exist, and the only honest
                # next step is a new preview a human reviews again. Offering the CURRENT
                # witness here would be worse than the original defect - a one-hop path
                # from "refused, unreviewed" to "applied".
                "apply_with": None,
                "remediation": "re-preview this edit and review the new diff; the "
                               "approved change described bytes that no longer exist"}

    literal = bool(args.get("literal"))
    count = int(args.get("count", 0))
    if literal:
        # exact-string replacement; count=0 means all
        n = content.count(pattern) if count == 0 else min(content.count(pattern), count)
        new_content = content.replace(pattern, replacement, -1 if count == 0 else count)
    else:
        flags = 0
        for name, val in _FLAGS.items():
            if args.get(name):
                flags |= val
        try:
            new_content, n = re.subn(pattern, replacement, content, count=count, flags=flags)
        except re.error as e:
            return {"ok": False, "error": f"bad regex: {e}"}

    # The safety belt: refuse to touch anything if the match count isn't what the caller expected.
    expected = args.get("expected_replacements")
    if expected is not None and n != int(expected):
        return {"ok": False, "tool": "edit", "replacements": n, "written": False,
                "error": f"expected {int(expected)} replacement(s), found {n}: refusing",
                "literal": literal}

    changed = new_content != content
    result = {"tool": "edit", "replacements": n, "changed": changed, "source": source,
              "literal": literal}
    if witness:
        result["source_sha256"] = witness
    if confirmed(args, legacy=("write",)) and source == "path" and changed:
        path.write_text(new_content, encoding="utf-8")
        result["written"] = True
        result["path"] = path.as_posix()
    else:
        result["written"] = False
        result["result"] = new_content  # preview
        if source == "path":
            # The witness travels WITH the approval. A caller that reviews this preview and
            # sends `apply_with` back unmodified is bound to the state it reviewed without
            # having to know that binding is happening.
            result["apply_with"] = {"apply": True, "expected_source_sha256": witness}
    return result
