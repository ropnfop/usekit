# Path: usekit.classes.common.utils.helper_keydata_path.py
# -----------------------------------------------------------------------------------------------
#  Keydata Path Helper
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------
#  Design
#  ------
#  - helper_search: decides *which files* to inspect (paths / loc / fmt / mod)
#  - parser_factory: decides *how* to read each file (fmt → parser module)
#  - each parser: decides *how to interpret* keydata / search options
#
#  This module is intentionally thin:
#    1) collect candidate file paths using helper_search
#    2) for each file, call parser.load(..., keydata=...)
#    3) return the paths (and optionally values) that matched
#
#  All format-specific behavior (JSON/YAML/CSV/TXT/PYP/…) is delegated
#  to the parser layer. No hard-coded per-format routing here.
#
#  Universal Path Resolution:
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Mode 1: keydata=None  → Pure file search (SQL/DDL/PYP common)
#  Mode 2: keydata="..." → Content-based filtering (PYP specific)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

from usekit.classes.common.utils.helper_search import (
    find_data_search,
    detect_format_from_file,
)
from usekit.classes.common.utils.helper_format import get_format_parser
from usekit.classes.data.base.post.parser_factory import get_parser_by_format


# ===============================================================================
# Internal: per-file search
# ===============================================================================

def _search_in_file(
    file_path: Path,
    *,
    fmt_hint: str,
    keydata: str,
    search_value: Any = None,
    key_type: Optional[str] = None,
    keydata_exists: bool = False,
    regex: bool = False,
    case_sensitive: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    line_numbers: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> Any:
    """
    Run keydata search inside a single file.

    Responsibility:
      - Decide effective format (fmt_hint or auto-detect)
      - Load parser via parser_factory
      - Call parser.load(file_path, keydata=..., ...)
      - Normalize result for existence vs. value mode
    """

    # 1) Decide effective format
    if fmt_hint == "any":
        detected = detect_format_from_file(file_path)
        if detected is None:
            if debug:
                print(f"[KEYDATA] Skip unsupported file: {file_path}")
            return False if keydata_exists else None
        # Simple alias normalization
        if detected == "yml":
            detected = "yaml"
        effective_fmt = detected
    else:
        effective_fmt = fmt_hint

    # 2) Load parser for this format
    try:
        parser_name = get_format_parser(effective_fmt)
        parser = get_parser_by_format(parser_name)
    except Exception as e:
        if debug:
            print(f"[KEYDATA] Parser error for fmt={effective_fmt}, path={file_path}: {e}")
        return False if keydata_exists else None

    # 3) Prepare kwargs for parser.load
    parser_kwargs = {
        "keydata": keydata,
        "search_value": search_value,
        "key_type": key_type,
        "keydata_exists": keydata_exists,
        "regex": regex,
        "case_sensitive": case_sensitive,
        "recursive": recursive,
        "find_all": find_all,
        "line_numbers": line_numbers,
    }
    parser_kwargs.update(kwargs)

    # 4) Call parser.load() with appropriate input type
    try:
        # PKL and other binary formats: pass path directly
        if parser_name in ("pkl",):
            result = parser.load(file_path, **parser_kwargs)
        # Text formats: open file and pass file handle
        else:
            encoding = kwargs.get("encoding", "utf-8")
            with file_path.open("r", encoding=encoding) as f:
                result = parser.load(f, **parser_kwargs)
                
    except TypeError as e:
        # Some parsers may not accept all advanced options.
        # Retry with minimal core keydata kwargs.
        if debug:
            print(f"[KEYDATA] TypeError in parser.load for {file_path}: {e}")
            print("[KEYDATA] Retrying with minimal keydata kwargs")

        minimal_kwargs = {
            "keydata": keydata,
            "keydata_exists": keydata_exists,
        }
        try:
            if parser_name in ("pkl",):
                result = parser.load(file_path, **minimal_kwargs)
            else:
                encoding = kwargs.get("encoding", "utf-8")
                with file_path.open("r", encoding=encoding) as f:
                    result = parser.load(f, **minimal_kwargs)
        except Exception as e2:
            if debug:
                print(f"[KEYDATA] Fallback load failed for {file_path}: {e2}")
            return False if keydata_exists else None
    except Exception as e:
        if debug:
            print(f"[KEYDATA] Error reading {file_path}: {e}")
        return False if keydata_exists else None

    # 5) Normalize result
    if keydata_exists:
        # Parser may return bool or any truthy/falsy container/value.
        return bool(result)

    if result is None:
        return None
    if isinstance(result, (list, tuple, dict, str)) and not result:
        # Empty container / string → treat as "no match"
        return None

    return result


# ===============================================================================
# Public: search across many files
# ===============================================================================

def search_keydata_paths(
    fmt: str = "any",
    *,
    mod: Optional[str] = "all",
    pattern: str = "*",
    keydata: Optional[str] = None,
    loc: str = "base",
    user_dir: Optional[str] = None,
    # search options
    walk: bool = True,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    line_numbers: bool = False,
    # result options
    keydata_exists: bool = False,
    with_values: bool = False,
    max_files: Optional[int] = None,
    debug: bool = False,
    **kwargs: Any,
) -> Union[bool, List[Path], List[Tuple[Path, Any]]]:
    """
    Universal path resolver with optional content filtering.

    Modes:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. keydata=None  → Pure file search (like helper_search)
                       Returns paths matching pattern/fmt/loc
                       
    2. keydata="..."  → Content-based search (filter by keydata)
                       Returns only paths where content matches keydata
    
    High-level responsibility:
      1) Collect candidate files via helper_search.find_data_search()
      2) If keydata is None: return paths directly
      3) If keydata provided: filter by file content
      4) Return:
         - bool when keydata_exists=True
         - list of paths when with_values=False
         - list of (path, value) when with_values=True
    
    Examples:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Pure path search (SQL/DDL/PYP common)
    >>> search_keydata_paths(fmt="sql", pattern="query_*", keydata=None)
    [Path("query_users.sql"), Path("query_orders.sql")]
    
    # Content filtering (PYP specific)
    >>> search_keydata_paths(fmt="pyp", keydata="clean_data", key_type="def")
    [Path("helpers.pyp")]  # Only files with "def clean_data"
    
    # Hybrid (pattern + content)
    >>> search_keydata_paths(fmt="pyp", pattern="utils_*", keydata="process", key_type="def")
    [Path("utils_data.pyp")]  # Matches pattern AND has "def process"
    """

    # 1) Collect candidate file paths
    if fmt == "any" and mod is None:
        mod = "all"

    candidates = find_data_search(
        format_type=fmt,
        mod=mod,
        pattern=pattern,
        loc=loc,
        user_dir=user_dir,
        walk=walk,
        case_sensitive=case_sensitive,
        debug=debug,
    )

    if not candidates:
        if debug:
            print(f"[KEYDATA] No candidate files for pattern='{pattern}', fmt='{fmt}', mod='{mod}'")
        return False if keydata_exists else []

    if max_files is not None and max_files > 0:
        candidates = candidates[:max_files]

    # 2) No keydata? Return paths directly (pure file search)
    if not keydata:
        if debug:
            print(f"[KEYDATA] No keydata → returning {len(candidates)} paths directly")
        
        if keydata_exists:
            return True if candidates else False
        
        if with_values:
            # No content to extract, return (path, None) tuples
            return [(p, None) for p in candidates]
        
        return candidates

    # 3) Has keydata: filter by content
    if debug:
        print(f"[KEYDATA] Filtering {len(candidates)} files by keydata: {keydata}")

    hits: List[Union[Path, Tuple[Path, Any]]] = []

    # COMMON options used for all files
    search_value = kwargs.pop("search_value", None)
    key_type = kwargs.pop("key_type", None)

    # Run keydata search per file
    for path in candidates:
        result = _search_in_file(
            path,
            fmt_hint=fmt,
            keydata=keydata,
            search_value=search_value,
            key_type=key_type,
            keydata_exists=keydata_exists,
            regex=regex,
            case_sensitive=case_sensitive,
            recursive=recursive,
            find_all=find_all,
            line_numbers=line_numbers,
            debug=debug,
            **kwargs,
        )

        # Existence-only mode: early exit on first hit
        if keydata_exists:
            if result:
                if debug:
                    print(f"[KEYDATA] Early exit: found match in {path}")
                return True
            continue

        # Normal mode: collect all hits
        if result is not None:
            if with_values:
                hits.append((path, result))
            else:
                hits.append(path)

    # 4) Final result
    if keydata_exists:
        return False

    if debug:
        print(f"[KEYDATA] Found {len(hits)} matching files")

    return hits


# ===============================================================================
# Convenience: first match only
# ===============================================================================

def search_keydata_first(
    fmt: str = "any",
    *,
    mod: Optional[str] = "all",
    pattern: str = "*",
    keydata: Optional[str] = None,
    loc: str = "base",
    user_dir: Optional[str] = None,
    walk: bool = True,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    line_numbers: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> Optional[Path]:
    """
    Return only the first Path that matches the search criteria.
    
    Modes:
    - keydata=None  → First file matching pattern/fmt/loc
    - keydata="..." → First file where content matches keydata
    
    Examples:
        # Pure path search
        >>> search_keydata_first(fmt="sql", pattern="query_users")
        Path("query_users.sql")
        
        # Content-based search
        >>> search_keydata_first(fmt="pyp", keydata="clean_data", key_type="def")
        Path("helpers.pyp")  # First file with "def clean_data"
    """

    results = search_keydata_paths(
        fmt=fmt,
        mod=mod,
        pattern=pattern,
        keydata=keydata,
        loc=loc,
        user_dir=user_dir,
        walk=walk,
        case_sensitive=case_sensitive,
        regex=regex,
        recursive=recursive,
        find_all=find_all,
        line_numbers=line_numbers,
        keydata_exists=False,
        with_values=False,
        max_files=None,
        debug=debug,
        **kwargs,
    )

    if not results:
        return None

    # search_keydata_paths(with_values=False) → List[Path]
    return results[0]


# ===============================================================================
# Backward-compatible alias
# ===============================================================================

def find_files_by_keydata(
    fmt: str,
    name_pattern: str = "*",
    loc: str = "base",
    mod: Optional[str] = None,
    user_dir: Optional[str] = None,
    keydata: Optional[str] = None,
    search_value: Any = None,
    key_type: Optional[str] = None,
    keydata_exists: bool = False,
    walk: bool = True,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    with_values: bool = False,
    debug: bool = False,
    **kwargs: Any,
) -> Union[bool, List[Path], List[Tuple[Path, Any]]]:
    """
    Legacy-style wrapper kept for compatibility with earlier code.

    Only difference:
      - name_pattern here → pattern in search_keydata_paths
    """

    return search_keydata_paths(
        fmt=fmt,
        mod=mod,
        pattern=name_pattern,
        keydata=keydata,
        loc=loc,
        user_dir=user_dir,
        walk=walk,
        case_sensitive=case_sensitive,
        regex=regex,
        recursive=recursive,
        find_all=find_all,
        line_numbers=False,
        keydata_exists=keydata_exists,
        with_values=with_values,
        debug=debug,
        search_value=search_value,
        key_type=key_type,
        **kwargs,
    )


__all__ = [
    "search_keydata_paths",
    "search_keydata_first",
    "find_files_by_keydata",
]
