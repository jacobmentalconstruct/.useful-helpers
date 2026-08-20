"""
FILE:       tools/patch/cli.py
ROLE:       Surgical, indentation-aware JSON patching (tokenized hunks) with dry-run validation.
DOMAIN:     tool
DOES:       apply/validate a patch {hunks:[{search_block, replace_block, use_patch_indent?}]} to
            `text` or a `path`. Strict match then content-only fallback; rejects not-found,
            ambiguous, or overlapping hunks; reflows replacement indent to the file anchor unless
            use_patch_indent. Preview by default; writes only with write:true + a path.
DEPENDS ON: tools._toolkit, (stdlib) json, re, pathlib
WIRES TO:   invoked by src/core/invoke.py; described by sibling tool.json (Apply authority)
NOTES:      Hunk fields are `search_block`/`replace_block`. Preserves trailing newlines
            (a naive join drops them).
"""
from __future__ import annotations

import json
import re

from tools._toolkit import resolve_within_roots, tool_main


# ===== re-homed engine (faithful) ==========================================
class PatchError(Exception):
    pass


class StructuredLine:
    """A single line split into indent + content + trailing whitespace."""
    __slots__ = ["indent", "content", "trailing", "original"]

    def __init__(self, line: str):
        self.original = line
        m = re.match(r"(^[ \t]*)(.*?)([ \t]*$)", line, re.DOTALL)
        if m:
            self.indent, self.content, self.trailing = m.group(1), m.group(2), m.group(3)
        else:
            self.indent, self.content, self.trailing = "", line, ""

    def reconstruct(self) -> str:
        return f"{self.indent}{self.content}{self.trailing}"


def tokenize_text(text: str):
    newline = "\r\n" if "\r\n" in text else "\n"
    return [StructuredLine(ln) for ln in text.splitlines()], newline


def locate_hunk(file_lines, search_lines, floating=False):
    if not search_lines:
        return []
    matches = []
    for start in range(len(file_lines) - len(search_lines) + 1):
        ok = True
        for i, s in enumerate(search_lines):
            f = file_lines[start + i]
            if (f.content != s.content) if floating else (f.reconstruct() != s.reconstruct()):
                ok = False
                break
        if ok:
            matches.append(start)
    return matches


def apply_patch_text(original_text: str, patch_obj: dict, global_force_indent: bool = False) -> str:
    if not isinstance(patch_obj, dict) or "hunks" not in patch_obj:
        raise PatchError("Patch must be a dict with a 'hunks' list.")
    hunks = patch_obj.get("hunks", [])
    if not isinstance(hunks, list):
        raise PatchError("'hunks' must be a list.")

    file_lines, newline = tokenize_text(original_text)
    applications = []
    for idx, hunk in enumerate(hunks, start=1):
        search_block = hunk.get("search_block")
        replace_block = hunk.get("replace_block")
        use_patch_indent = hunk.get("use_patch_indent", global_force_indent)
        if search_block is None or replace_block is None:
            raise PatchError(f"Hunk {idx}: Missing 'search_block' or 'replace_block'.")
        s_lines = [StructuredLine(ln) for ln in search_block.splitlines()]
        r_lines = [StructuredLine(ln) for ln in replace_block.splitlines()]
        matches = locate_hunk(file_lines, s_lines, floating=False) or locate_hunk(file_lines, s_lines, floating=True)
        if not matches:
            raise PatchError(f"Hunk {idx}: Search block not found.")
        if len(matches) > 1:
            raise PatchError(f"Hunk {idx}: Ambiguous match ({len(matches)} found).")
        start = matches[0]
        applications.append({"start": start, "end": start + len(s_lines),
                             "replace_lines": r_lines, "use_patch_indent": bool(use_patch_indent), "id": idx})

    applications.sort(key=lambda a: a["start"])
    for i in range(len(applications) - 1):
        if applications[i]["end"] > applications[i + 1]["start"]:
            raise PatchError(f"Hunks {applications[i]['id']} and {applications[i+1]['id']} overlap in the target file.")

    for app in reversed(applications):
        start, end, r_lines = app["start"], app["end"], app["replace_lines"]
        base_indent = file_lines[start].indent if 0 <= start < len(file_lines) else ""
        patch_base_indent = next((rl.indent for rl in r_lines if rl.content.strip()), "")
        final_block = []
        for rl in r_lines:
            if not app["use_patch_indent"] and rl.content.strip():
                relative = rl.indent[len(patch_base_indent):] if rl.indent.startswith(patch_base_indent) else rl.indent
                rl.indent = base_indent + relative
            final_block.append(rl)
        file_lines[start:end] = final_block

    return newline.join(ln.reconstruct() for ln in file_lines)


def _multi(args: dict, patch: dict, action: str) -> dict:
    """A patch SET over several files, applied as one unit or not at all."""
    entries = patch["files"]
    force = bool(args.get("force_indent", False))
    planned, problems = [], []

    for i, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict) or not entry.get("path"):
            problems.append(f"file {i}: each entry needs a 'path' and 'hunks'")
            continue
        p, err = resolve_within_roots(entry["path"])
        if err:
            problems.append(f"{entry['path']}: {err}")
            continue
        if not p.is_file():
            problems.append(f"{entry['path']}: not a file")
            continue
        original = p.read_text(encoding="utf-8")
        try:
            new_text = apply_patch_text(original, {"hunks": entry.get("hunks", [])},
                                        global_force_indent=force)
        except PatchError as e:
            problems.append(f"{entry['path']}: {e}")
            continue
        if original.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"
        planned.append({"path": p, "rel": str(entry["path"]), "new_text": new_text,
                        "changed": new_text != original,
                        "hunks": len(entry.get("hunks", []))})

    files = [{"path": q["rel"], "changed": q["changed"], "hunks": q["hunks"]}
             for q in planned]
    result = {"tool": "patch", "action": action, "source": "files",
              "files": files, "file_count": len(entries),
              "hunks": sum(q["hunks"] for q in planned),
              "changed": any(q["changed"] for q in planned)}

    if problems:
        # NAME EVERY PROBLEM, not just the first. A caller fixing a patch set one error per
        # run is being made to pay for the tool's convenience.
        return {**result, "ok": False, "written": False, "problems": problems,
                "error": f"{len(problems)} of {len(entries)} file(s) rejected; "
                         "no file was written"}
    if action == "validate":
        return {**result, "valid": True, "written": False,
                "preview": {q["rel"]: q["new_text"] for q in planned}}
    if not bool(args.get("write")):
        return {**result, "written": False,
                "result": {q["rel"]: q["new_text"] for q in planned},
                "apply_with": {"apply": True}}

    written = []
    for q in planned:
        if q["changed"]:
            q["path"].write_text(q["new_text"], encoding="utf-8")
            written.append(q["rel"])
    return {**result, "written": True, "written_paths": written}


# ===== tool wrapper ========================================================
@tool_main
def run(args: dict) -> dict:
    action = str(args.get("action", "apply")).lower()
    if action not in ("apply", "validate"):
        return {"ok": False, "error": "action must be 'apply' or 'validate'"}

    patch = args.get("patch")
    if patch is None and args.get("patch_json") is not None:
        try:
            patch = json.loads(args["patch_json"])
        except json.JSONDecodeError as e:
            return {"ok": False, "error": f"bad patch_json: {e}"}
    if not isinstance(patch, dict):
        return {"ok": False, "error": "provide 'patch' (object) or 'patch_json'"}

    # PARITY ROW 2.5 — one reviewed patch operation spanning several files.
    #
    # The donor's product is a patch SET applied as one unit, and the smallest owner that
    # can represent it is this tool: `patch` already understands hunks, ambiguity and
    # overlap. Adding an iteration construct to playbooks to fake it would have been a
    # general execution engine built to turn one row green.
    #
    # EVERY FILE IS VALIDATED BEFORE ANY FILE IS WRITTEN. A set that half-applies is worse
    # than one that refuses: the target ends up in a state nobody designed, and the caller
    # is told it "partly worked". This is the same all-or-nothing rule the single-file path
    # already enforces across hunks, applied one level up across files.
    if isinstance(patch.get("files"), list):
        return _multi(args, patch, action)

    if args.get("text") is not None:
        original, source, path = str(args["text"]), "text", None
    elif args.get("path"):
        # CONTAINED, like every other target writer. This read `Path(args["path"])` with no
        # containment at all, while `edit` and `write_file` both resolve within the roots -
        # so `patch` could read and WRITE anywhere the process could reach. Found while
        # implementing 2.5, and it makes census row 11.5 ("path containment on every file
        # read and store write") false as written for this tool. Repaired here rather than
        # recorded, because the row claims a property the product did not have.
        path, err = resolve_within_roots(args["path"])
        if err:
            return {"ok": False, "error": err}
        if not path.is_file():
            return {"ok": False, "error": f"not a file: {args['path']}"}
        original, source = path.read_text(encoding="utf-8"), "path"
    else:
        return {"ok": False, "error": "provide 'text' or 'path'"}

    try:
        new_text = apply_patch_text(original, patch, global_force_indent=bool(args.get("force_indent", False)))
    except PatchError as e:
        return {"ok": False, "error": str(e)}

    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"  # engine's join drops the trailing newline
    changed = new_text != original
    result = {"tool": "patch", "action": action, "source": source,
              "hunks": len(patch.get("hunks", [])), "changed": changed}

    if action == "validate":
        result.update(valid=True, written=False, preview=new_text)
        return result
    if bool(args.get("write")) and source == "path" and changed:
        path.write_text(new_text, encoding="utf-8")
        result.update(written=True, path=str(path).replace("\\", "/"))
    else:
        result.update(written=False, result=new_text)
    return result
