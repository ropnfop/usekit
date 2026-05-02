# Path: usekit.classes.data.base.load.ops.dbl_has.py
# -----------------------------------------------------------------------------------------------
#  Exists Operation - Refactored with helper_search Integration
#  Created by: THE Little Prince × ROP × FOP
#  [SIMPLIFIED] helper_search handles ALL path logic, has checks file/keydata presence
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Union

from usekit.infra.io_signature import params_for_has, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_search import find_data_search, detect_format_from_file
from usekit.classes.common.utils.helper_format import get_format_parser
from usekit.classes.common.utils.helper_keypath import has_key_path
from usekit.classes.data.base.load.sub.dbl_a_index_sub import proc_read_data


# ===============================================================================
# Single File Exists Check
# ===============================================================================

def _check_single_file(file_path: Path, p: dict) -> bool:
    """
    Check if a single file has (and optionally check keydata path).
    
    SmallBig Pattern:
    - keydata present: Check if specific path has in file (Small)
    - keydata absent: File existence is enough (Big)
    
    Args:
        file_path: Path object to the file
        p: Parameters dict from params_for_has()
        
    Returns:
        True if has (and keydata has if specified), False otherwise
    """
    
    # File should exist at this point (from find_data_search)
    # But double-check for safety
    if not file_path.is_file():
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] File not found: {file_path}")
        return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Small Mode: Check keydata path
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["keydata"] is not None:
        # Detect actual format from file extension
        fmt_actual = detect_format_from_file(file_path)
        fmt_actual = get_format_parser(fmt_actual)
        
        if not fmt_actual:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Unknown format for file: {file_path}")
            return False
        
        # Cache location uses pkl regardless of logical format
        if p["loc"] == "cache":
            fmt_actual = "pkl"
        
        if p["debug"]:
            prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
            print(f"{prefix}{fmt_actual.upper()} Checking keydata: {p['keydata']} in {file_path}")
        
        try:
            # Read data and check keydata path
            data = proc_read_data(fmt_actual, file_path)
            result = has_key_path(
                data,
                p["keydata"],
                recursive=p.get("recursive", False)
            )
            
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Keydata has: {result}")
            
            return result
            
        except Exception as e:
            if p["debug"]:
                print(f"[{fmt_actual.upper()}] Error checking keydata: {e}")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Big Mode: File existence is enough
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["debug"]:
        prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
        print(f"{prefix} File has: {file_path}")
    
    return True


# ===============================================================================
# Main Exists Operation
# ===============================================================================

@log_and_raise
def has_operation(**kwargs) -> bool:
    """
    Exists operation with unified search-based architecture.
    
    Architecture (Simplified):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. helper_search: Handles ALL path/pattern/format logic
    2. dbl_has: Check if files exist (and optionally check keydata)
    3. No duplicate path logic, no pattern detection needed
    4. Returns True if ANY file matches (pattern) or file has (exact)
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    has_operation(fmt, name, ...)
      → find_data_search(format, pattern, ...)  # ALL cases
      → [file1.json, file2.txt, ...] or []
      → If keydata: Check each file for keydata path
      → Return True if ANY file matches (pattern) or file has (exact)
    
    SmallBig Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    User mental model:
    
    1. name only           → check if file has (Big)
    2. name + keydata      → check if specific path has in file (Small)
    
    With keydata → check "path has in file" (Small)
    Without keydata → check "file has" (Big)
    
    Pattern Matching:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Returns True if ANY file matches pattern
    - With keydata: ALL matched files must have the keydata path
    - Without keydata: Just file existence check
    
    Features:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - SmallBig pattern support
    - Pattern matching: "user_*", "config_????"
    - Recursive search: walk=True (default: False)
    - Keydata navigation: "api/key" (check specific path)
    - Format detection: Auto-detect from file extension
    
    Args:
        **kwargs: Common I/O parameters (see io_signature)
        walk: Recursive search (default: False)
        use_format: Use only helper_format registered formats (default: True)
        
    Returns:
        True if file(s) exist (and keydata has if specified)
        False otherwise
        
    Examples:
        # 1. Single file has (name only) - Big!
        >>> has_operation(fmt="json", name="config")
        True
        
        # 2. File + keydata has (name + keydata) - Small!
        >>> has_operation(
        ...     fmt="json",
        ...     name="config",
        ...     keydata="api/key"  # Check if this path has
        ... )
        True  # File has AND keydata path has
        
        # 3. Pattern has (any match)
        >>> has_operation(fmt="json", name="user_*", loc="base")
        True  # At least one user_* file has in base/
        
        # 4. Pattern + recursive
        >>> has_operation(fmt="json", name="user_*", loc="base", walk=True)
        True  # At least one user_* file has in base/ or subdirs
        
        # 5. Pattern + keydata (all must have keydata)
        >>> has_operation(
        ...     fmt="json",
        ...     name="user_*",
        ...     keydata="email"  # ALL matched files must have 'email' field
        ... )
        True  # All user_* files have 'email' field
        
        # 6. Any format with mod
        >>> has_operation(
        ...     fmt="any",
        ...     mod="toml",
        ...     name="config"
        ... )
        True  # config.toml has
        
        # 7. LIKE pattern (SQL style)
        >>> has_operation(fmt="json", name="%test%", loc="tmp")
        True  # Any file with 'test' in name has in tmp/
        
        # 8. Non-existent file
        >>> has_operation(fmt="json", name="missing")
        False
        
        # 9. File has but keydata missing
        >>> has_operation(
        ...     fmt="json",
        ...     name="config",
        ...     keydata="missing/path"
        ... )
        False  # File has but keydata path not found
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_has(**kwargs)
    
    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)
    
    # Extract walk parameter (default: False)
    walk = kwargs.get("walk", False)
    p["walk"] = walk
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1.5] Handle fmt=any validation
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    fmt_parser = p["fmt"]
    if p["fmt"] == "any" and p["name"]:  # File has mode only
        if not p["mod"]:
            from usekit.classes.common.utils.helper_format import get_supported_formats
            available_mods = ", ".join(sorted(get_supported_formats()))
            
            raise ValueError(
                "fmt='any' requires 'mod' parameter for has operations.\n"
                f"Available mod values: {available_mods}\n\n"
                "Examples:\n"
                "  e.has(name='config', fmt='any', mod='toml')\n"
                "  e.has(name='user_*', fmt='any', mod='ini', walk=True)\n\n"
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
            print(f"[{p['fmt'].upper()}] Exists: no name provided -> False")
        return False
    
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
            print(f"[{p['fmt'].upper()}] No files found: name='{p['name']}'")
        return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [5] Check Files
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Pattern without keydata: ANY file has → True
    if p["keydata"] is None:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Pattern has: True ({len(matched_files)} file(s) found)")
        return True
    
    # Pattern with keydata: ALL files must have keydata
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Checking keydata in {len(matched_files)} file(s)")
    
    for file_path in matched_files:
        if not _check_single_file(file_path, p):
            # One file doesn't have the keydata
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Keydata missing in: {file_path.name}")
            return False
    
    # All files have the keydata
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] All {len(matched_files)} file(s) have keydata: {p['keydata']}")
    
    return True


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["has_operation"]
