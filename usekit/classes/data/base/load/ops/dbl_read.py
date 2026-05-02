# Path: usekit.classes.data.base.load.ops.dbl_read.py
# -----------------------------------------------------------------------------------------------
#  Read Operation - Refactored Version
#  Created by: THE Little Prince × ROP × FOP
#  [SIMPLIFIED] helper_search handles ALL path logic, read only wraps parsers
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Union

from usekit.infra.io_signature import params_for_read, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise, debug_print
from usekit.classes.common.utils.helper_search import find_data_search, detect_format_from_file
from usekit.classes.common.utils.helper_format import get_format_parser      
from usekit.classes.common.utils.helper_keypath import resolve_key_path
from usekit.classes.data.base.load.sub.dbl_read_sub import proc_read_data
from usekit.classes.data.base.load.sub.dbl_common_sub import _filter_load_kwargs


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
    'dir_path', 'mod'
}


def _extract_parser_kwargs(params: dict, fmt: str) -> dict:
    """
    Extract parameters for parser using format-specific whitelist.
    
    Delegates to _filter_load_kwargs from dbl_common_sub which handles
    format-specific filtering (e.g., TXT gets regex/tail options, JSON doesn't).
    
    Args:
        params: All parameters from params_for_read()
        fmt: Format name (json, txt, csv, etc.)
        
    Returns:
        Filtered kwargs safe for the specific format's parser
    """
    # First remove ops-only params
    candidate_params = {k: v for k, v in params.items() if k not in OPS_ONLY_PARAMS}
    
    # Then apply format-specific whitelist
    return _filter_load_kwargs(fmt, **candidate_params)


# ===============================================================================
# Single File Processing
# ===============================================================================

def _process_single_file(file_path: Path, p: dict) -> Any:
    """
    Process a single file: detect format, read data, navigate keydata.
    
    This is the core parser wrapper function.
    
    Args:
        file_path: Path object to the file
        p: Parameters dict from params_for_read()
        
    Returns:
        Parsed data (with optional keydata navigation)
    """
    
    # Detect actual format from file extension
    fmt_actual = detect_format_from_file(file_path)
    fmt_actual = get_format_parser(fmt_actual)
                
    if not fmt_actual:
        raise ValueError(f"Unknown format for file: {file_path}")
    
    # Cache location uses pkl regardless of logical format
    if p["loc"] == "cache":
        fmt_actual = "pkl"
    
    prefix = f"[{p['fmt'].upper()}->]" if p['fmt'] == "any" else f"[{p['fmt'].upper()}]"
    message = f"{prefix}{fmt_actual.upper()} Reading: {file_path}"

    if p.get("debug"):
        print(message)
    
    debug_print(message)
    
    # Extract parser kwargs (format-specific filtering)
    parser_kwargs = _extract_parser_kwargs(p, fmt_actual)
    
    # Read data with parser options
    data = proc_read_data(fmt_actual, file_path, **parser_kwargs)
    
    # Apply keydata navigation if specified
    if p["keydata"] is not None:
        if p["debug"]:
            print(f"[{fmt_actual.upper()}] Navigating keydata: {p['keydata']}")
        return resolve_key_path(
            data,
            p["keydata"],
            default=p["default"],
            recursive=p["recursive"],
            find_all=p["find_all"]
        )
    
    return data


# ===============================================================================
# Multi-File Processing
# ===============================================================================

def _process_multiple_files(file_paths: list[Path], p: dict) -> list[dict]:
    """
    Process multiple files and return structured results.
    
    Args:
        file_paths: List of Path objects
        p: Parameters dict from params_for_read()
        
    Returns:
        List of {"file", "path", "data"} dicts (or "error" on failure)
    """
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Processing {len(file_paths)} files")
    
    results = []
    
    for file_path in file_paths:
        try:
            data = _process_single_file(file_path, p)
            
            results.append({
                "file": file_path.stem,
                "path": str(file_path),
                "data": data
            })
            
        except Exception as e:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Error: {file_path.name} - {e}")
            
            results.append({
                "file": file_path.stem,
                "path": str(file_path),
                "error": str(e)
            })
    
    return results


# ===============================================================================
# Main Read Operation
# ===============================================================================

@log_and_raise
def read_operation(**kwargs) -> Any:
    """
    Read operation with unified search-based architecture.
    
    Architecture (Simplified):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. helper_search: Handles ALL path/pattern/format logic
    2. dbl_read: Wraps parsers and applies keydata navigation
    3. No duplicate path logic, no pattern detection needed
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    read_operation(fmt, name, ...)
      → find_data_search(format, pattern, ...)  # ALL cases
      → [file1.json, file2.txt, ...]
      → _process_single_file() or _process_multiple_files()
      → return data or [{"file": ..., "data": ...}, ...]
    
    Features:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Pattern matching: "user_*", "log_????", "%test%"
    - Exact match: "config", "test"
    - Any format: fmt="any" auto-detects from extension
    - Keydata navigation: "user/email", "items[0]/name"
    - Parser options: tail_bottom, regex, encoding, etc. (auto-forwarded)
    - Recursive search: walk=True (default: False)
    
    Args:
        **kwargs: Common I/O parameters (see io_signature)
        use_format: Use only helper_format registered formats (default: True)
                    False allows all files (unsupported formats return error)
        
    Returns:
        Single file: data or keydata value
        Multiple files: List of {"file", "path", "data"} dicts
        
    Examples:
        # Single file - exact match
        >>> read_operation(fmt="json", name="config")
        {"key": "value"}
        
        # Single file - any format (auto-detect)
        >>> read_operation(fmt="any", name="test", mod="all")
        "content from test.txt"
        
        # Pattern matching (current directory only)
        >>> read_operation(fmt="json", name="user_*", loc="base")
        [{"file": "user_001", "data": {...}}, {"file": "user_002", "data": {...}}]
        
        # Pattern + recursive search
        >>> read_operation(fmt="any", name="*.log", mod="all", walk=True)
        [{"file": "error", "path": ".../error.log", "data": "..."}, ...]
        
        # Keydata navigation
        >>> read_operation(fmt="json", name="config", keydata="database/host")
        "localhost"
        
        # TXT with tail (options auto-forwarded to parser)
        >>> read_operation(fmt="txt", name="log", tail_bottom=100)
        "last 100 lines..."
        
        # TXT with regex search
        >>> read_operation(fmt="txt", name="log", keydata="ERROR.*timeout", regex=True)
        ["ERROR: timeout at 10:30", "ERROR: timeout at 14:22"]
        
        # Use all files (including unsupported formats)
        >>> read_operation(fmt="any", name="*", mod="all", use_format=False)
        [{"file": "config", "data": {...}}, {"file": "note", "error": "Unknown format"}]
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_read(**kwargs)
    
    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Find Files (helper_search handles ALL cases)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    matched_files = find_data_search(
        format_type=p["fmt"],
        mod=p["mod"],
        pattern=p["name"],
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        walk=p["walk"],
        case_sensitive=p.get("case_sensitive", False),
        debug=p["debug"]
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2.5] Filter by helper_format support
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p.get("use_format", True):
        supported_files = [f for f in matched_files 
                          if detect_format_from_file(f) is not None]
        
        if p["debug"] and len(supported_files) < len(matched_files):
            skipped = len(matched_files) - len(supported_files)
            print(f"[FORMAT] Skipped {skipped} unsupported file(s) (use_format=True)")
        
        matched_files = supported_files
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Handle Results
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if len(matched_files) == 0:
        raise FileNotFoundError(
            f"No files found: name='{p['name']}', fmt={p['fmt']}, "
            f"mod={p['mod']}, loc={p['loc']}, walk={p['walk']}"
        )
    
    elif len(matched_files) == 1:
        # Single file: return data directly
        return _process_single_file(matched_files[0], p)
    
    else:
        # Multiple files: return structured list
        return _process_multiple_files(matched_files, p)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["read_operation"]
