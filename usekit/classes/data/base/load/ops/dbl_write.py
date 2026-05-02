# Path: usekit.classes.data.base.load.ops.dbl_write.py
# -----------------------------------------------------------------------------------------------
#  Write Operation - Refactored with Parser Options
#  Created by: THE Little Prince × ROP × FOP
#  [REFACTORED] Format-specific option filtering + keypath support
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional

from usekit.infra.io_signature import params_for_write, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_path import get_smart_path
from usekit.classes.common.utils.helper_keypath import set_key_path
from usekit.classes.data.base.load.sub.dbl_a_index_sub import proc_write_data , proc_read_data
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
    'dir_path', 'mod'
}


def _extract_parser_kwargs(params: dict, fmt: str, for_file: bool = True) -> dict:
    """
    Extract parameters for parser using format-specific whitelist.
    
    Delegates to _filter_dump_kwargs from dbl_common_sub which handles
    format-specific filtering (e.g., JSON gets wrap/indent, TXT doesn't).
    
    Args:
        params: All parameters from params_for_write()
        fmt: Format name (json, txt, csv, etc.)
        for_file: If True, include 'encoding' for file I/O
        
    Returns:
        Filtered kwargs safe for the specific format's parser
    """
    # First remove ops-only params
    candidate_params = {k: v for k, v in params.items() if k not in OPS_ONLY_PARAMS}
    
    # Then apply format-specific whitelist
    filtered_params = _filter_dump_kwargs(fmt, for_file=for_file, **candidate_params)
    
    # Special case: DDL format needs debug parameter
    # Add it AFTER filtering because _filter_dump_kwargs doesn't know about debug
    if fmt == "ddl" and "debug" in params:
        filtered_params["debug"] = params["debug"]
    
    return filtered_params


# ===============================================================================
# Main Write Operation
# ===============================================================================

@log_and_raise
def write_operation(**kwargs) -> Optional[Path]:
    """
    Write operation with keypath support and dump mode.
    
    Architecture:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - Smart path resolution via helper_path
    - Parser options: Automatically forwarded (wrap, indent, encoding, etc.)
    - Format-specific filtering: JSON gets wrap/indent, TXT doesn't
    - Keypath support: Merge with existing data
    - DDL exception: name=None allowed (parser extracts table name)
    
    Features:
    - Full data write to file
    - Write to specific keydata path (merges with existing)
    - Dump mode (no file, just serialize/display)
    - Auto-forward: All parser options passed through automatically
    - DDL smart naming: Auto-extract table name when name=None
    
    Safety:
    - Pattern matching NOT supported (prevents accidental overwrites)
    - Must specify exact filename (except DDL with extractable table name)
    
    Args:
        **kwargs: Common I/O parameters (see io_signature)
        
    Returns:
        Path object if file written successfully
        None if dump mode (no filename)
        
    Examples:
        # Full write (new or overwrite)
        >>> write_operation(fmt="json", data={"key": "value"}, name="config")
        PosixPath('/path/to/config.json')
        
        # Write to keydata path (merge with existing)
        >>> write_operation(fmt="json", data=100, name="config", keydata="user/score")
        PosixPath('/path/to/config.json')
        # File now contains: {...existing..., "user": {"score": 100}}
        
        # Create nested structure
        >>> write_operation(
        ...     fmt="json", 
        ...     data="value", 
        ...     name="config", 
        ...     keydata="a/b/c/d",
        ...     create_missing=True
        ... )
        PosixPath('/path/to/config.json')
        
        # Dump mode (display without saving)
        >>> write_operation(fmt="json", data={"key": "value"})
        # Prints formatted JSON to console
        None
        
        # DDL smart naming (auto-extract table name)
        >>> write_operation(fmt="ddl", data="CREATE TABLE users (id INT);")
        PosixPath('/path/to/users.sql')  # Table name auto-extracted
        
        >>> write_operation(fmt="ddl", data={"table": "products", "records": [...]})
        PosixPath('/path/to/products.sql')  # Table name from dict
        
        # Write with format options (auto-forwarded to parser)
        >>> write_operation(
        ...     fmt="json", 
        ...     data={"key": "value"}, 
        ...     name="config",
        ...     indent=4,
        ...     sort_keys=True,
        ...     ensure_ascii=False
        ... )
        PosixPath('/path/to/config.json')
        
        # TXT append mode
        >>> write_operation(
        ...     fmt="txt",
        ...     data="new line",
        ...     name="log",
        ...     append=True,
        ...     append_newline=True
        ... )
        PosixPath('/path/to/log.txt')
    """
    
    # Extract parameters
    p = params_for_write(**kwargs)
    
    # Warn about future features (k, kv, kc, kf)
    warn_future_features(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [0] Handle fmt=any for write operations
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # fmt=any requires mod parameter to determine file extension
    # Validates mod using helper_format functions
    fmt_parser = p["fmt"]
    if p["fmt"] == "any" and p["name"]:  # File write mode only
        if not p["mod"]:
            from usekit.classes.common.utils.helper_format import get_supported_formats
            available_mods = ", ".join(sorted(get_supported_formats()))
            
            raise ValueError(
                "fmt='any' requires 'mod' parameter for write operations.\n"
                f"Available mod values: {available_mods}\n\n"
                "Examples:\n"
                "  u.write(data, name='config', fmt='any', mod='toml')\n"
                "  u.write(data, name='app', fmt='any', mod='ini')\n"
                "  u.write(data, name='settings', fmt='any', mod='json')\n\n"
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
      
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Dump mode check (DDL exception)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not p["name"] and p["fmt"] != "ddl":
        # Non-DDL formats: dump mode (no file)
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Write (dump mode - display only)")
        
        # Determine physical format (cache uses pkl)
        fmt_actual = "pkl" if p["loc"] == "cache" else fmt_parser
        
        # Extract parser kwargs (for_file=False for dump mode)
        parser_kwargs = _extract_parser_kwargs(p, fmt_actual, for_file=False)
        
        # Dump without file
        result = proc_write_data(fmt_actual, None, p["data"] or {}, dump_mode=True, **parser_kwargs)
        return result
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Build file path using helper_path
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DDL: name=None allowed (parser will extract table name or fallback to base_dir)
    # Other formats: name required at this point
    path = get_smart_path(
        fmt=p["fmt"],
        mod=p["mod"],
        filename=p["name"],  # Can be None for DDL
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        cus=p["cus"]
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Keydata path write (merge with existing)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["keydata"] is not None:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Write to keydata path: {p['keydata']}")
        
        # Read existing data if file exists
        if path.exists():
            # Determine physical format (cache uses pkl)
            fmt_actual = "pkl" if p["loc"] == "cache" else fmt_parser
            existing_data = proc_read_data(fmt_actual, path)
        else:
            existing_data = {}
        
        # Set value at keydata path
        success = set_key_path(
            existing_data,
            p["keydata"],
            p["data"],
            create_missing=p["create_missing"],
            recursive=p["recursive"]
        )
        
        if not success:
            if p["debug"]:
                print(f"[{p['fmt'].upper()}] Failed to set keydata: {p['keydata']}")
            return None
        
        data = existing_data
    else:
        # Full write mode
        data = p["data"]
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4] Write file with parser options
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Writing to: {path}")
    
    # Determine physical format (cache uses pkl)
    fmt_actual = "pkl" if p["loc"] == "cache" else fmt_parser
    
    # Extract parser kwargs (format-specific filtering)
    parser_kwargs = _extract_parser_kwargs(p, fmt_actual, for_file=True)
    
    # Perform write operation with parser options
    result = proc_write_data(fmt_actual, path, data or {}, **parser_kwargs)
    
    return path if result else None


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["write_operation"]
