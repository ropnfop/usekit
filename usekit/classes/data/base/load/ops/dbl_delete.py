# Path: usekit.classes.data.base.load.ops.dbl_delete.py
# -----------------------------------------------------------------------------------------------
#  Delete Operation - Refactored with helper_search Integration
#  Created by: THE Little Prince × ROP × FOP
#  [SIMPLIFIED] helper_search handles ALL path logic, delete reads then removes
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Union

from usekit.infra.io_signature import params_for_delete, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_search import find_data_search, detect_format_from_file
from usekit.classes.common.utils.helper_format import get_format_parser
from usekit.classes.common.utils.helper_keypath import delete_key_path
from usekit.classes.data.base.load.sub.dbl_a_index_sub import (
    proc_delete_data, proc_read_data, proc_write_data
)


# ===============================================================================
# Single File Delete
# ===============================================================================

def _process_single_file(file_path: Path, p: dict) -> Optional[Path]:
    """
    Delete a single file or keydata path within it.
    
    SmallBig Pattern:
    - keydata present: Delete specific path only, keep file (Small)
    - keydata absent: Delete entire file (Big)
    
    Args:
        file_path: Path object to the file
        p: Parameters dict from params_for_delete()
        
    Returns:
        Path if successful, None otherwise
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
    # [1] Small Mode: Delete keydata path only
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["keydata"] is not None:
        if p["debug"]:
            prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
            print(f"{prefix}{fmt_actual.upper()} Delete keydata: {p['keydata']} from {file_path}")
        
        # Read existing data
        existing_data = proc_read_data(fmt_actual, file_path)
        
        # Delete keydata path
        success = delete_key_path(
            existing_data,
            p["keydata"],
            recursive=p.get("recursive", False)
        )
        
        if not success:
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Failed to delete keydata: {p['keydata']}")
            return None
        
        # Write modified data back
        if p["debug"]:
            print(f"[{fmt_actual.upper()}] Writing modified data: {file_path}")
        
        proc_write_data(fmt_actual, file_path, existing_data)
        return file_path
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Big Mode: Delete entire file
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["debug"]:
        prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
        print(f"{prefix}{fmt_actual.upper()} Delete file: {file_path}")
    
    result = proc_delete_data(fmt_actual, file_path)
    return file_path if result else None


# ===============================================================================
# Multi-File Delete
# ===============================================================================

def _process_multiple_files(file_paths: list[Path], p: dict) -> dict:
    """
    Delete multiple files and return structured results.
    
    Args:
        file_paths: List of Path objects
        p: Parameters dict from params_for_delete()
        
    Returns:
        {"deleted": [...], "failed": [...], "total": N, "success": N}
    """
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Processing {len(file_paths)} files")
    
    deleted = []
    failed = []
    
    for file_path in file_paths:
        try:
            result_path = _process_single_file(file_path, p)
            if result_path:
                deleted.append(result_path)
            else:
                failed.append({
                    "path": file_path,
                    "error": "Delete operation returned None"
                })
            
        except Exception as e:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Error: {file_path.name} - {e}")
            
            failed.append({
                "path": file_path,
                "error": str(e)
            })
    
    result = {
        "deleted": deleted,
        "failed": failed,
        "total": len(file_paths),
        "success": len(deleted),
        "failed_count": len(failed)
    }
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Delete complete: {result['success']}/{result['total']}")
    
    return result


# ===============================================================================
# Main Delete Operation
# ===============================================================================

@log_and_raise
def delete_operation(**kwargs) -> Any:
    """
    Delete operation with unified search-based architecture.
    
    Architecture (Simplified):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. helper_search: Handles ALL path/pattern/format logic
    2. dbl_delete: Read (if keydata) → Delete → Write back (if keydata)
    3. No duplicate path logic, no pattern detection needed
    4. Delete requires existing file(s) to work on
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    delete_operation(fmt, name, ...)
      → find_data_search(format, pattern, ...)  # ALL cases
      → [file1.json, file2.txt, ...]
      → _process_single_file() or _process_multiple_files()
        → proc_read_data() → delete_key_path() → proc_write_data()  # Small
        → proc_delete_data()  # Big
      → return path or {"deleted": [...], "failed": [...]}
    
    SmallBig Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    User mental model:
    
    1. name only           → delete entire file (Big)
    2. name + keydata      → delete specific path, keep file (Small)
    
    With keydata → delete "value at that path" (Small)
    Without keydata → delete "entire file" (Big)
    
    Features:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - SmallBig pattern support
    - Pattern matching: "old_*", "temp_????"
    - Recursive search: walk=True (default: False)
    - Keydata navigation: "user/temp" (delete specific path)
    - Safety: Dangerous patterns blocked ("*", "*.*", etc.)
    
    Safety:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Files MUST exist (delete requires read first for keydata mode)
    - Dangerous patterns blocked: "*", "**", "*.*", multiple wildcards + walk
    - Pattern matching without specific constraint raises error
    - walk defaults to False (non-recursive)
    
    Args:
        **kwargs: Common I/O parameters (see io_signature)
        walk: Recursive search (default: False)
        use_format: Use only helper_format registered formats (default: True)
        
    Returns:
        No name: None
        Single file: Path if successful, None otherwise
        Multiple files: {"deleted": [...], "failed": [...], "total": N, "success": N}
        
    Examples:
        # 1. Delete single file (name only) - Big!
        >>> delete_operation(fmt="json", name="old_config")
        PosixPath('/path/to/old_config.json')
        
        # 2. Delete keydata path (name + keydata) - Small!
        >>> delete_operation(
        ...     fmt="json",
        ...     name="config",
        ...     keydata="user/temp_data"  # Only this path!
        ... )
        PosixPath('/path/to/config.json')  # File kept, only keydata removed
        
        # 3. Pattern delete (non-recursive)
        >>> delete_operation(fmt="json", name="temp_*", loc="tmp")
        {
            "deleted": [Path(...), Path(...)],
            "failed": [],
            "total": 2,
            "success": 2
        }
        
        # 4. Pattern + keydata (bulk keydata deletion)
        >>> delete_operation(
        ...     fmt="json",
        ...     name="user_*",
        ...     keydata="temp_field"  # Delete this field from all matched files
        ... )
        {
            "deleted": [Path(...), Path(...), Path(...)],
            "total": 3,
            "success": 3
        }
        
        # 5. Recursive pattern delete
        >>> delete_operation(
        ...     fmt="json",
        ...     name="old_user_*",
        ...     walk=True
        ... )
        {
            "deleted": [Path(...), Path(...), Path(...)],
            "failed": [{"path": Path(...), "error": "..."}],
            "total": 4,
            "success": 3,
            "failed_count": 1
        }
        
        # 6. Any format with mod
        >>> delete_operation(
        ...     fmt="any",
        ...     mod="toml",
        ...     name="old_config"
        ... )
        PosixPath('/path/to/old_config.toml')
        
        # 7. Dangerous pattern (raises ValueError)
        >>> delete_operation(fmt="json", name="*")
        ValueError: Dangerous delete pattern detected
        
        # 8. Pattern with walk and multiple wildcards (blocked)
        >>> delete_operation(fmt="json", name="*_test_*", walk=True)
        ValueError: Dangerous delete pattern detected
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [0] Mem shortcut — no file I/O
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if kwargs.get("loc") == "mem":
        from usekit.classes.data.base.load.ops.dbl_mem_store import mem_delete
        return mem_delete(kwargs.get("name"))

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_delete(**kwargs)

    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)
    
    # Extract walk parameter (default: False)
    walk = kwargs.get("walk", False)
    p["walk"] = walk
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1.5] Handle fmt=any validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    fmt_parser = p["fmt"]
    if p["fmt"] == "any" and p["name"]:  # File delete mode only
        if not p["mod"]:
            from usekit.classes.common.utils.helper_format import get_supported_formats
            available_mods = ", ".join(sorted(get_supported_formats()))
            
            raise ValueError(
                "fmt='any' requires 'mod' parameter for delete operations.\n"
                f"Available mod values: {available_mods}\n\n"
                "Examples:\n"
                "  d.delete(name='old_config', fmt='any', mod='toml')\n"
                "  d.delete(name='temp_*', fmt='any', mod='ini', walk=True)\n\n"
                "Note: fmt='any' uses TXT parser for unsupported formats"
            )
        
        # Validate mod has in supported formats
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
    # [2] No name mode
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not p["name"]:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Delete: no name provided")
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
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] No files found to delete: name='{p['name']}'")
        return None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4.5] Pattern Safety Check
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Dangerous patterns should be blocked for safety
    has_pattern = any(c in p["name"] for c in ('*', '?', '[', '%'))
    
    if has_pattern:
        # Check for dangerous patterns
        dangerous = [
            p["name"] == "*",
            p["name"] == "**",
            p["name"] == "*.*",
            p["name"] == "%" or p["name"] == "%%",
            (p["name"].count("*") >= 2 and walk),  # Multiple wildcards + recursive
        ]
        
        if any(dangerous):
            raise ValueError(
                f"Dangerous delete pattern detected: '{p['name']}' with walk={walk}.\n"
                f"This would delete {len(matched_files)} files.\n\n"
                f"Blocked patterns:\n"
                f"- '*' (all files)\n"
                f"- '**' (recursive all)\n"
                f"- '*.*' (all with extension)\n"
                f"- Multiple wildcards with walk=True\n\n"
                f"Please use more specific patterns like:\n"
                f"- 'temp_*' (files starting with temp_)\n"
                f"- 'old_data_?????' (specific length)\n"
                f"- Add keydata to delete specific paths only"
            )
        
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Pattern delete: {len(matched_files)} files matched")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [5] Execute Delete
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if len(matched_files) == 1:
        # Single file: return Path directly
        return _process_single_file(matched_files[0], p)
    
    # Multiple files: return structured dict
    return _process_multiple_files(matched_files, p)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["delete_operation"]
