# Path: usekit.tools.convert.common.common_convert.py
# -----------------------------------------------------------------------------------------------
#  ROP × THE Little Prince × FOP
#  Universal Format Auto-Converter for usekit
#
#  Goals
#   - One converter for both NAVI(simple) and DATA(simple)
#   - Token-safe replacements (avoid breaking words like "context")
#   - Auto mode detection per file:
#       * NAVI: act = p/f/l/g/s, ops = path/find/list/get/set
#       * DATA: act = r/w/u/d/e, ops = read/write/update/delete/exists
#
#  Public API
#   - convert_format(src, old, new, dst=None, mode="auto")
#   - convert_by_name(name, old, new, loc="dir", mode="auto")
#   - convert_by_name_v2(name, old, new, loc="dir", mode="auto")
#   - convert_all_simple(old="txt", new="csv", mode="auto", root=".")
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
import re
import shutil
from pathlib import Path
from typing import List, Optional


# ===============================================================================
# Internal helpers
# ===============================================================================

def _ensure_backup(src: str) -> str:
    bak = src + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(src, bak)
        print(f"[BACKUP] {bak}")
    return bak


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _write_text(path: str, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _safe_token_replace(text: str, old: str, new: str) -> str:
    """
    Replace 'old' only when it is a standalone token.
    This avoids corrupting words like "context" when old="txt".
    """
    text = re.sub(rf"\b{re.escape(old)}\b", new, text)
    text = re.sub(rf"\b{re.escape(old.capitalize())}\b", new.capitalize(), text)
    text = re.sub(rf"\b{re.escape(old.upper())}\b", new.upper(), text)
    return text


def _safe_snake_replace(text: str, old: str, new: str) -> str:
    """
    Replace snake segments like *_txt and txt_*.
    This covers module names such as dbi_wrap_txt, dbi_simple_txt, etc.
    """
    text = re.sub(rf"_{re.escape(old)}\b", f"_{new}", text)
    text = re.sub(rf"\b{re.escape(old)}_", f"{new}_", text)
    return text


def _detect_mode(text: str, old: str) -> str:
    """
    Detect NAVI vs DATA by the most reliable patterns.
    """
    if re.search(rf"\b(read|write|update|delete|exists)_{re.escape(old)}_", text):
        return "data"
    if re.search(rf"\b(path|find|list|get|set)_{re.escape(old)}_", text):
        return "navi"

    if re.search(r"\bact:\s*r\s*/\s*w\s*/\s*u\s*/\s*d\s*/\s*e\b", text, flags=re.I):
        return "data"
    if re.search(r"\bact:\s*p\s*/\s*f\s*/\s*l\s*/\s*g\s*/\s*s\b", text, flags=re.I):
        return "navi"

    if re.search(r"\b[rwude][a-z][bnsdtpc]\b", text):
        return "data"

    return "navi"


def _replace_obj_header(text: str, old_obj: str, new_obj: str) -> str:
    text = re.sub(rf"(\bobj:\s*){re.escape(old_obj)}\b", rf"\1{new_obj}", text)
    text = re.sub(rf"(\b#\s*obj:\s*){re.escape(old_obj)}\b", rf"\1{new_obj}", text)
    return text


def _replace_alias_3letter(text: str, act_chars: str, old_obj: str, new_obj: str) -> str:
    loc_chars = "bnsdtpc"
    pattern = rf"\b([{re.escape(act_chars)}]){re.escape(old_obj)}([{loc_chars}])\b"
    return re.sub(pattern, rf"\1{new_obj}\2", text)


def _replace_wrap_ops(text: str, mode: str, old: str, new: str) -> str:
    if mode == "navi":
        ops_union = "path|find|list|get|set"
    else:
        ops_union = "read|write|update|delete|exists"

    return re.sub(
        rf"\b({ops_union})_{re.escape(old)}_",
        rf"\1_{new}_",
        text
    )


def _replace_header_alias_star(text: str, act_chars: str, old_obj: str, new_obj: str) -> str:
    return re.sub(
        rf"\(([{re.escape(act_chars)}]){re.escape(old_obj)}\*\)",
        rf"(\1{new_obj}*)",
        text
    )


def _replace_known_module_names(text: str, old: str, new: str) -> str:
    text = text.replace(f"dbi_wrap_{old}", f"dbi_wrap_{new}")
    text = text.replace(f"dbi_simple_{old}", f"dbi_simple_{new}")
    text = text.replace(f"dbi_class_{old}", f"dbi_class_{new}")
    return text


def _build_dst_path(src_str: str, old: str, new: str, loc: str = "dir") -> str:
    """
    Build destination path safely:
      - Directory segment: /txt/ -> /csv/
      - Filename stem: _txt -> _csv
    loc:
      - "dir": replace both directory segment and filename
      - "name": replace filename only
      - "path": replace directory only
    """
    dst_str = src_str

    if loc in ("dir", "path"):
        dst_str = dst_str.replace(f"/{old}/", f"/{new}/")

    if loc in ("dir", "name"):
        dst_str = dst_str.replace(f"_{old}", f"_{new}")

    if loc in ("dir", "path"):
        dst_str = dst_str.replace(f"\\{old}\\", f"\\{new}\\")

    return dst_str

def _safe_prefix_case_replace(text: str, old: str, new: str) -> str:
    """
    Replace format prefix in identifiers.
    Examples:
      TxtSP  -> KmSP
      TxtNS  -> KmNS
      TXT_PATH -> KM_PATH
    """
    old_cap = old.capitalize()
    new_cap = new.capitalize()

    # PascalCase prefix: TxtSP, TxtNS, TxtWrap...
    text = re.sub(rf"\b{re.escape(old_cap)}(?=[A-Z0-9_])", new_cap, text)

    # UPPER prefix: TXT_PATH, TXTWrap...
    text = re.sub(rf"\b{re.escape(old.upper())}(?=[A-Z0-9_])", new.upper(), text)

    return text
    
# ===============================================================================
# Core engine
# ===============================================================================

def convert_format(src: str, old: str, new: str, dst: Optional[str] = None, mode: str = "auto") -> str:
    """
    Dual-mode convert engine (NAVI + DATA)

    Args:
      src: source python module file
      old/new: format tokens (e.g., "txt" -> "csv")
      dst: destination path; if None, will replace in src path
      mode: "auto" | "navi" | "data"
    """
    if mode not in ("auto", "navi", "data"):
        raise ValueError(f"Invalid mode: {mode}")

    if dst is None:
        dst = src.replace(old, new)

    if not os.path.isfile(src):
        raise FileNotFoundError(f"Source not found: {src}")

    _ensure_backup(src)

    print(f"[INFO] Converting {src} ({old} -> {new})")
    print(f"[INFO] Output -> {dst}")

    text = _read_text(src)

    detected = _detect_mode(text, old) if mode == "auto" else mode
    act_chars = "pflgs" if detected == "navi" else "rwude"

    old_obj = old[0]
    new_obj = new[0]

    text = _safe_token_replace(text, old, new)
    text = _safe_snake_replace(text, old, new)
    text = _safe_prefix_case_replace(text, old, new)

    text = _replace_obj_header(text, old_obj, new_obj)
    text = _replace_alias_3letter(text, act_chars, old_obj, new_obj)
    text = _replace_wrap_ops(text, detected, old, new)
    text = _replace_header_alias_star(text, act_chars, old_obj, new_obj)
    text = _replace_known_module_names(text, old, new)

    _write_text(dst, text)

    print(f"[DONE] mode={detected} conversion completed.")
    return dst


# ===============================================================================
# Auto-find + convert
# ===============================================================================

def convert_by_name(name: str, old: str, new: str, loc: str = "dir", mode: str = "auto") -> str:
    """
    Find source using find_operation(fmt="pyp") and convert.
    """
    from usekit.classes.navi.base.load.ops.nbl_find import find_operation

    results = find_operation(fmt="pyp", name=name)
    if not results:
        raise FileNotFoundError(f"[AUTO] not found: {name} (fmt='pyp')")

    src = Path(results[0])
    dst_str = _build_dst_path(str(src), old, new, loc=loc)
    dst = Path(dst_str)

    print(f"[AUTO] Found source -> {src}")
    print(f"[AUTO] Target path  -> {dst}")

    return convert_format(str(src), old, new, str(dst), mode=mode)


def convert_by_name_v2(name: str, old: str, new: str, loc: str = "dir", mode: str = "auto") -> str:
    """
    Same as convert_by_name, but keeps extra prints and directory creation.
    """
    from usekit.classes.navi.base.load.ops.nbl_find import find_operation
    from usekit.classes.navi.base.load.ops.nbl_path import path_operation  # noqa: F401

    results = find_operation(fmt="pyp", name=name, walk=True, loc=loc)
    if not results:
        raise FileNotFoundError(f"[AUTO] not found: {name} (fmt='pyp')")

    src = Path(results[0])
    dst_str = _build_dst_path(str(src), old, new, loc=loc)
    dst = Path(dst_str)

    dst.parent.mkdir(parents=True, exist_ok=True)
    print(f"[MKDIR] Directory ready -> {dst.parent}")

    print(f"[AUTO] Source -> {src}")
    print(f"[AUTO] Target -> {dst}")

    return convert_format(str(src), old, new, str(dst), mode=mode)


# ===============================================================================
# Project-wide bulk convert
# ===============================================================================

def convert_all_simple(
    old: str = "txt",
    new: str = "csv",
    mode: str = "auto",
    root: str = ".",
    include_wrap: bool = False
) -> List[str]:
    """
    Bulk convert across project:
      - *_simple_<old>.py -> *_simple_<new>.py
      - optionally *_wrap_<old>.py -> *_wrap_<new>.py
    """
    outputs: List[str] = []

    simple_pat = re.compile(rf".*_simple_{re.escape(old)}\.py$")
    wrap_pat = re.compile(rf".*_wrap_{re.escape(old)}\.py$") if include_wrap else None

    for r, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".py"):
                continue

            hit = bool(simple_pat.match(fn))
            if not hit and wrap_pat is not None:
                hit = bool(wrap_pat.match(fn))

            if not hit:
                continue

            src = os.path.join(r, fn)
            dst = _build_dst_path(src, old, new, loc="dir")

            print(f"[BULK] {src} -> {dst}")
            outputs.append(convert_format(src, old, new, dst, mode=mode))

    return outputs


__all__ = [
    "convert_format",
    "convert_by_name",
    "convert_by_name_v2",
    "convert_all_simple",
]