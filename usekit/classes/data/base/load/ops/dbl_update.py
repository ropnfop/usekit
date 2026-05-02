# Path: usekit.classes.data.base.load.ops.dbl_update.py
# -----------------------------------------------------------------------------------------------
#  Update Operation - Refactored with helper_search Integration
#  Created by: THE Little Prince × ROP × FOP
#  [SIMPLIFIED] helper_search handles ALL path logic, update reads then modifies
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional

from usekit.infra.io_signature import params_for_update, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_search import find_data_search, detect_format_from_file
from usekit.classes.common.utils.helper_format import get_format_parser      
from usekit.classes.common.utils.helper_keypath import set_key_path
from usekit.classes.data.base.load.sub.dbl_a_index_sub import proc_update_data, proc_read_data, proc_write_data
from usekit.classes.data.base.load.sub.dbl_common_sub import _filter_dump_kwargs

# ===============================================================================
# Parameter Filtering
# ===============================================================================

# Parameters used only at ops layer (should NOT be passed to proc/parser)
OPS_ONLY_PARAMS = {
    # Ops layer processing
    'keydata', 'default', 'recursive', 'find_all', 'create_missing',
    'walk', 'case_sensitive',
    
    # Future features
    'k', 'kv', 'kc', 'kf',
    
    # System layer (ops control)
    'fmt', 'mode', 'mode_sub', 'debug',
    
    # User layer (path building)
    'name', 'path', 'loc', 'cus', 'data',
    
    # Internal params
    'dir_path', 'mod',
    
    # Update behavior control (passed to _process_single_file but not to parsers)
    'merge'
}


def _extract_parser_kwargs(params: dict, fmt: str, for_file: bool = True) -> dict:
    """
    Extract parameters for parser using format-specific whitelist.
    
    Delegates to _filter_dump_kwargs from dbl_common_sub which handles
    format-specific filtering (e.g., JSON gets wrap/indent, TXT doesn't).
    
    Args:
        params: All parameters from params_for_update()
        fmt: Format name (json, txt, csv, etc.)
        for_file: If True, include 'encoding' for file I/O
        
    Returns:
        Filtered kwargs safe for the specific format's parser
    """
    # First remove ops-only params
    candidate_params = {k: v for k, v in params.items() if k not in OPS_ONLY_PARAMS}
    
    # Then apply format-specific whitelist
    return _filter_dump_kwargs(fmt, for_file=for_file, **candidate_params)


# ===============================================================================
# Single File Update
# ===============================================================================

def _process_single_file(file_path: Path, p: dict) -> Path:
    """
    Update a single file: read, modify, write back.
    
    SmallBig Pattern:
    - keydata present: Update specific path only (Small)
    - keydata absent: Merge entire data (Big)
    
    Args:
        file_path: Path object to the file
        p: Parameters dict from params_for_update()
        
    Returns:
        Updated file Path
    """
    
    # Detect actual format from file extension
    fmt_actual = detect_format_from_file(file_path)
    fmt_actual = get_format_parser(fmt_actual)
    
    if not fmt_actual:
        raise ValueError(f"Unknown format for file: {file_path}")
    
    # Cache location uses pkl regardless of logical format
    if p["loc"] == "cache":
        fmt_actual = "pkl"
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Read existing data
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["debug"]:
        prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
        print(f"{prefix}{fmt_actual.upper()} Reading: {file_path}")
    
    existing_data = proc_read_data(fmt_actual, file_path)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Modify data (Small vs Big)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["keydata"] is not None:
        # Small: Update specific keydata path
        if p["debug"]:
            print(f"[{fmt_actual.upper()}] Updating keydata: {p['keydata']}")
        
        success = set_key_path(
            existing_data,
            p["keydata"],
            p["data"],
            create_missing=p["create_missing"],
            recursive=p["recursive"]
        )
        
        if not success:
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Failed to set keydata: {p['keydata']}")
            raise ValueError(f"Failed to update keydata path: {p['keydata']}")
        
        updated_data = existing_data
    else:
        # Big: Merge entire data (respects merge parameter)
        merge_enabled = p.get("merge", True)  # Default merge=True
        
        if merge_enabled:
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Merging entire data")
            
            # Merge existing data with new data
            if isinstance(existing_data, dict) and isinstance(p["data"], dict):
                updated_data = {**existing_data, **p["data"]}
            elif isinstance(existing_data, list) and isinstance(p["data"], list):
                updated_data = existing_data + p["data"]
            else:
                # Type mismatch or non-dict/list: replace
                if p["debug"]:
                    print(f"[{fmt_actual.upper()}] Type mismatch - replacing data")
                updated_data = p["data"] if p["data"] is not None else {}
        else:
            # merge=False: Replace mode
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Replace mode (merge=False)")
            updated_data = p["data"] if p["data"] is not None else {}
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Write back
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["debug"]:
        print(f"[{fmt_actual.upper()}] Writing updated data: {file_path}")
    
    # Extract parser kwargs (format-specific filtering)
    parser_kwargs = _extract_parser_kwargs(p, fmt_actual, for_file=True)
    
    # Write updated data with parser options
    # Note: We already merged, so use proc_write_data instead of proc_update_data
    proc_write_data(fmt_actual, file_path, updated_data, **parser_kwargs)
    
    return file_path

# ===============================================================================
# Multi-File Update
# ===============================================================================

def _process_multiple_files(file_paths: list[Path], p: dict) -> dict:
    """
    Update multiple files and return structured results.
    
    Args:
        file_paths: List of Path objects
        p: Parameters dict from params_for_update()
        
    Returns:
        {"updated": [...], "failed": [...], "total": N, "success": N}
    """
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Processing {len(file_paths)} files")
    
    updated = []
    failed = []
    
    for file_path in file_paths:
        try:
            result_path = _process_single_file(file_path, p)
            updated.append(result_path)
            
        except Exception as e:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Error: {file_path.name} - {e}")
            
            failed.append({
                "path": file_path,
                "error": str(e)
            })
    
    result = {
        "updated": updated,
        "failed": failed,
        "total": len(file_paths),
        "success": len(updated),
        "failed_count": len(failed)
    }
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Update complete: {result['success']}/{result['total']}")
    
    return result


# ===============================================================================
# Main Update Operation
# ===============================================================================

@log_and_raise
def update_operation(**kwargs) -> Any:
    """
    Update operation with unified search-based architecture.
    
    Architecture (Simplified):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. helper_search: Handles ALL path/pattern/format logic
    2. dbl_update: Read → Modify → Write back
    3. No duplicate path logic, no pattern detection needed
    4. Update MUST have existing file(s) to work on
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    update_operation(fmt, name, data, ...)
      → find_data_search(format, pattern, ...)  # ALL cases
      → [file1.json, file2.txt, ...]
      → _process_single_file() or _process_multiple_files()
        → proc_read_data() → modify (Small/Big) → proc_update_data()
      → return path or {"updated": [...], "failed": [...]}
    
    SmallBig Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    User mental model:
    
    1. data only             → dump (display)
    2. data + name           → merge entire file (Big)
    3. data + name + keydata → update specific path (Small)
    
    With keydata → data is "value at that path" (Small)
    Without keydata → data is "entire dataset" (Big)
    
    Merge Behavior (keydata=None only):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - merge=True (default): Merge new data with existing data
      * dict + dict → {**existing, **new}
      * list + list → existing + new
      * Type mismatch → replace
    - merge=False: Replace entire file with new data
    
    Note: merge parameter is ignored when keydata is provided
          (keydata mode always updates specific path only)
    
    Features:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - SmallBig pattern support
    - Pattern matching: "user_*", "config_*"
    - Recursive search: walk=True (default: False)
    - Keydata navigation: "user/email" (JSON) or "ERROR" pattern (TXT)
    - Create missing paths: create_missing=True
    - TXT replace: regex, case_sensitive, tail_*, replace_all, max_count
    - Parser options: Auto-forwarded (indent, encoding, etc.)
    
    Safety:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Files MUST exist (update requires read first)
    - No file creation (unlike write operation)
    - Pattern matching requires keydata for bulk updates (safety)
    - walk defaults to False (non-recursive)
    
    Args:
        **kwargs: Common I/O parameters (see io_signature)
        walk: Recursive search (default: False)
        use_format: Use only helper_format registered formats (default: True)
        
    Returns:
        Dump mode: None
        Single file: Path object
        Multiple files: {"updated": [...], "failed": [...], "total": N, "success": N}
        
    Examples:
        # 1. Dump mode (data only)
        >>> update_operation(fmt="json", data={"user": "Alice"})
        None  # Display only
        
        # 2. Merge entire (data + name) - Big!
        >>> update_operation(fmt="json", data={"new_key": "value"}, name="config")
        PosixPath('/path/to/config.json')  # Merged with existing
        
        # 2-1. Replace entire (merge=False) - Big!
        >>> update_operation(
        ...     fmt="json",
        ...     data={"new_key": "value"},
        ...     name="config",
        ...     merge=False  # Replace instead of merge
        ... )
        PosixPath('/path/to/config.json')  # Completely replaced
        
        # 3. Update specific path (data + name + keydata) - Small!
        >>> update_operation(
        ...     fmt="json",
        ...     data="new@example.com",  # Just this value!
        ...     name="config",
        ...     keydata="user/email"  # At this location!
        ... )
        PosixPath('/path/to/config.json')  # Only user/email changed
        
        # 4. TXT replace (search & replace)
        >>> update_operation(
        ...     fmt="txt",
        ...     data="FIXED",  # Replacement text
        ...     name="app.log",
        ...     keydata="ERROR",  # Pattern to find
        ...     tail_bottom=100,  # Last 100 lines only
        ...     regex=True,
        ...     replace_all=True
        ... )
        PosixPath('/path/to/app.log')  # ERROR → FIXED in last 100 lines
        
        # 5. Pattern matching - exact match
        >>> update_operation(fmt="json", data={"status": "active"}, name="config")
        PosixPath('/path/to/config.json')
        
        # 6. Pattern + keydata (bulk update specific field) - SAFE!
        >>> update_operation(
        ...     fmt="json",
        ...     data="updated@example.com",
        ...     name="user_*",
        ...     keydata="email"  # keydata REQUIRED for pattern updates
        ... )
        {
            "updated": [Path(...), Path(...), Path(...)],
            "failed": [],
            "total": 3,
            "success": 3
        }
        
        # 7. Pattern without keydata - ERROR (unsafe!)
        >>> update_operation(fmt="json", data={"key": "value"}, name="user_*")
        ValueError: Pattern matching requires keydata parameter for safety
        
        # 8. Any format with mod
        >>> update_operation(
        ...     fmt="any",
        ...     mod="toml",
        ...     data="[server]\nport=8080",
        ...     name="config",
        ...     keydata="old_text"
        ... )
        PosixPath('/path/to/config.toml')
        
        # 9. Recursive search with pattern
        >>> update_operation(
        ...     fmt="any",
        ...     mod="all",
        ...     data="updated",
        ...     name="*.log",
        ...     keydata="error_pattern",
        ...     walk=True
        ... )
        {
            "updated": [Path(...), Path(...), ...],
            "total": 5,
            "success": 5
        }
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_update(**kwargs)
    
    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)
    
    # Extract walk parameter (default: False)
    walk = kwargs.get("walk", False)
    p["walk"] = walk
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1.5] Handle fmt=any validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    fmt_parser = p["fmt"]
    if p["fmt"] == "any" and p["name"]:  # File update mode only
        if not p["mod"]:
            from usekit.classes.common.utils.helper_format import get_supported_formats
            available_mods = ", ".join(sorted(get_supported_formats()))
            
            raise ValueError(
                "fmt='any' requires 'mod' parameter for update operations.\n"
                f"Available mod values: {available_mods}\n\n"
                "Examples:\n"
                "  u.update(data, name='config', fmt='any', mod='toml', keydata='old')\n"
                "  u.update(data, name='app', fmt='any', mod='ini', keydata='pattern')\n\n"
                "Note: fmt='any' uses TXT parser for unsupported formats"
            )
        
        # Validate mod exists in supported formats
        from usekit.classes.common.utils.helper_format import get_supported_formats, get_format_set, get_format_parser      
        
        try:
            # This will raise ParserLoadError if mod is invalid
            ext = get_format_set(p["mod"])
            fmt_parser = get_format_parser(p["mod"])
            if p["debug"]:
                print(f"[ANY] Using parser_any.py wrapper with mod={p['mod']} → {ext}")
        except Exception as e:
            available_mods = ", ".join(sorted(get_supported_formats()))
            raise ValueError(
                f"Invalid mod='{p['mod']}' for fmt='any'.\n"
                f"Available mod values: {available_mods}\n"
                f"Error: {e}"
            )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Dump mode (no filename)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not p["name"]:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Update (dump mode - display only)")
        
        # Determine physical format (cache uses pkl)
        fmt_actual = "pkl" if p["loc"] == "cache" else fmt_parser
        
        # Extract parser kwargs (for_file=False for dump mode)
        parser_kwargs = _extract_parser_kwargs(p, fmt_actual, for_file=False)
        
        # Dump without file
        proc_update_data(fmt_actual, None, p["data"] or {}, dump_mode=True, **parser_kwargs)
        return None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Find Files (helper_search handles ALL cases)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    matched_files = find_data_search(
        format_type=p["fmt"],
        mod=p["mod"],
        pattern=p["name"],
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        walk=walk,
        case_sensitive=p.get("case_sensitive", False),
        debug=p["debug"]
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3.5] Filter by helper_format support
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p.get("use_format", True):
        supported_files = [f for f in matched_files 
                          if detect_format_from_file(f) is not None]
        
        if p["debug"] and len(supported_files) < len(matched_files):
            skipped = len(matched_files) - len(supported_files)
            print(f"[FORMAT] Skipped {skipped} unsupported file(s) (use_format=True)")
        
        matched_files = supported_files
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4] Handle Results
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if len(matched_files) == 0:
        raise FileNotFoundError(
            f"No files found to update: name='{p['name']}', fmt={p['fmt']}, "
            f"mod={p['mod']}, loc={p['loc']}, walk={walk}\n"
            f"Note: Update operation requires existing files to modify"
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4.5] Pattern Safety Check
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Pattern matching without keydata is dangerous (overwrites all matched files)
    has_pattern = any(c in p["name"] for c in ('*', '?', '[', '%'))
    
    if len(matched_files) > 1:
        # Multiple files matched
        if has_pattern and p["keydata"] is None:
            # UNSAFE: Pattern without keydata means full data overwrite
            raise ValueError(
                f"Pattern matching requires 'keydata' parameter for safety.\n"
                f"Found {len(matched_files)} files matching '{p['name']}'.\n\n"
                f"Reason: Without keydata, pattern updates would overwrite entire files.\n"
                f"This is almost never what you want!\n\n"
                f"Solutions:\n"
                f"1. Add keydata to update specific field:\n"
                f"   update(data='value', name='{p['name']}', keydata='field/path')\n"
                f"2. Update files individually:\n"
                f"   for file in files: update(data={{...}}, name=file)\n"
                f"3. Use write() for full file overwrites (more explicit)\n\n"
                f"Note: walk={walk}, use walk=True for recursive search"
            )
        
        # SAFE: Pattern with keydata (bulk field update)
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Pattern update (SAFE): {len(matched_files)} files with keydata")
    
    elif len(matched_files) == 1:
        # Single file: return data directly
        return _process_single_file(matched_files[0], p)
    
    # Multiple files: return structured list
    return _process_multiple_files(matched_files, p)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["update_operation"]
