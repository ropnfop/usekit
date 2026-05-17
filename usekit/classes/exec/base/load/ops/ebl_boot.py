# Path: usekit.classes.exec.base.load.ops.ebl_exec.py
# -----------------------------------------------------------------------------------------------
#  Exec Operation - Main Load Layer (OPS)
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Parameter processing + Path resolution + Delegation
#  
#  Philosophy:
#  - OPS layer resolves ALL paths using helper_keydata_path
#  - SUB layer only routes to format-specific executors
#  - No duplicate path resolution logic
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any

from usekit.infra.exec_signature import params_for_exec, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_keydata_path import search_keydata_first
from usekit.classes.exec.base.load.sub.ebl_exec_sub import route_to_executor


# ===============================================================================
# Parameter Filtering
# ===============================================================================

# Parameters used only at ops layer (should NOT be passed to sub/parser)
OPS_ONLY_PARAMS = {
    # Search control
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
    
    # Exec-specific ops params
    'ov_fmt', 'ov_loc', 'func', 'key_type', 'args', 'kwargs_exec'
}


def _extract_exec_kwargs(params: dict) -> dict:
    """
    Extract parameters safe for exec sub/parser layers.
    
    OPS layer removes its own processing params before delegation.
    Also removes params that will be passed explicitly to avoid duplicates.
    
    Args:
        params: All parameters from params_for_exec()
        
    Returns:
        Filtered kwargs for execution
    """
    # Parameters explicitly passed to route_to_executor
    EXPLICIT_PARAMS = {'func', 'args', 'kwargs_exec', 'reload', 'safe', 'debug'}
    
    # Remove both OPS-only and explicitly-passed params
    exclude = OPS_ONLY_PARAMS | EXPLICIT_PARAMS
    
    return {k: v for k, v in params.items() if k not in exclude}


# ===============================================================================
# Universal Path Resolution (Single Source of Truth)
# ===============================================================================

def _resolve_exec_path(p: dict) -> Path:
    """
    Universal path resolution for ALL exec formats.
    
    Single Responsibility: Find the file to execute
    
    Strategy Priority:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. path provided    → Use directly (highest priority)
    2. func provided    → Content-based search (keydata="func_name")
    3. name provided    → Pattern-based search (keydata=None)
    
    Unified Interface (helper_keydata_path):
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - SQL/DDL:  search_keydata_first(pattern="query_name", keydata=None)
    - PYP:      search_keydata_first(pattern="*", keydata="func_name", key_type="def")
    - Hybrid:   search_keydata_first(pattern="utils_*", keydata="process", key_type="def")
    
    Args:
        p: Parameters from params_for_exec()
        
    Returns:
        Resolved Path (guaranteed to exist)
        
    Raises:
        FileNotFoundError: If file cannot be found
        
    Examples:
        # Direct path
        >>> _resolve_exec_path({"path": "/data/script.pyp", ...})
        Path("/data/script.pyp")
        
        # PYP function search
        >>> _resolve_exec_path({"fmt": "pyp", "func": "clean_data", ...})
        Path("/base/helpers.pyp")  # contains "def clean_data"
        
        # SQL name search
        >>> _resolve_exec_path({"fmt": "sql", "name": "get_users", ...})
        Path("/base/get_users.sql")
    """
    
    # Strategy 1: Direct path (highest priority)
    if p["path"]:
        path_obj = Path(p["path"]) if isinstance(p["path"], str) else p["path"]
        if not path_obj.is_file():
            raise FileNotFoundError(f"Exec target not found: {path_obj}")
        return path_obj
    
    # Determine effective format and location
    effective_fmt = p["ov_fmt"] or p["fmt"]
    effective_loc = p["ov_loc"] or p["loc"]
    
    # Determine search parameters
    pattern = p.get("name") or "*"
    keydata = p.get("func")  # None for SQL/DDL, "func_name" for PYP
    
    # Set key_type for PYP content search
    key_type = None
    if effective_fmt == "pyp" and keydata:
        key_type = p.get("key_type") or "def"
        if key_type == "auto":
            key_type = "def"
    
    if p["debug"]:
        print(f"[EXEC-OPS] Path resolution:")
        print(f"  fmt={effective_fmt}, loc={effective_loc}")
        print(f"  pattern={pattern}, keydata={keydata}")
        if key_type:
            print(f"  key_type={key_type}")
    
    # Strategy 2/3: Unified search via helper_keydata_path
    result = search_keydata_first(
        fmt=effective_fmt,
        mod=p["mod"],
        pattern=pattern,
        keydata=keydata,
        loc=effective_loc,
        user_dir=p["cus"],
        walk=p["walk"],
        case_sensitive=p["case_sensitive"],
        key_type=key_type,
        debug=p["debug"]
    )
    
    if result is None:
        # Build descriptive error message
        search_parts = []
        if keydata:
            search_parts.append(f"function '{keydata}'")
        if pattern != "*":
            search_parts.append(f"pattern '{pattern}'")
        
        search_desc = " with " + " and ".join(search_parts) if search_parts else ""
        
        raise FileNotFoundError(
            f"No {effective_fmt} file found{search_desc} "
            f"(loc={effective_loc}, mod={p['mod']})"
        )
    
    return result


# ===============================================================================
# Main Exec Operation (OPS Entry Point)
# ===============================================================================

@log_and_raise
def boot_operation(**kwargs) -> Any:
    """
    Execute code and return result (EXEC MODE ONLY).
    
    Single Responsibility: Resolve path + delegate to format executor
    
    Architecture:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    OPS (this):  Parameter processing + Path resolution
    SUB:         Format routing
    POST:        Format-specific execution
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    exec_operation(fmt="pyp", func="my_func", args=(1, 2))
      → _resolve_exec_path() → Path("/base/utils.pyp")
      → route_to_executor(fmt, path, ...) → ebp_exec_pyp.exec_pyp()
      → return execution result
    
    Args:
        **kwargs: Execution parameters (see exec_signature.py)
        
    Returns:
        Function execution result
        
    Raises:
        FileNotFoundError: If execution file not found
        ValueError: If format not supported
        
    Examples:
        # Execute PYP function
        >>> exec_operation(fmt="pyp", func="clean_data", args=(data,))
        cleaned_data
        
        # Execute SQL query
        >>> exec_operation(fmt="sql", name="get_users", args=(conn,))
        [user_records...]
        
        # Execute with format override
        >>> exec_operation(name="@ps.utils:process", args=(x,))
        # ov_fmt="pyp", ov_loc="sub", func="process"
    """
    
    # Force exec mode (this is exec_operation, not import_operation)
    kwargs["mode"] = "exec"
    
    # Process parameters
    warn_future_features(kwargs)
    p = params_for_exec(**kwargs)
    
    if p["debug"]:
        print(f"[EXEC-OPS] Starting: fmt={p['fmt']}, mode={p['mode']}")
        if p["ov_fmt"]:
            print(f"[EXEC-OPS] Format override: {p['ov_fmt']}")
        if p["ov_loc"]:
            print(f"[EXEC-OPS] Location override: {p['ov_loc']}")
    
    # Resolve path (single source of truth)
    target_path = _resolve_exec_path(p)
    
    if p["debug"]:
        print(f"[EXEC-OPS] Resolved: {target_path}")
    
    # Determine effective format
    effective_fmt = p["ov_fmt"] or p["fmt"]
    
    # Extract execution kwargs (remove OPS-only params)
    exec_kwargs = _extract_exec_kwargs(p)
    
    # Delegate to SUB layer (format routing)
    result = route_to_executor(
        fmt=effective_fmt,
        path=target_path,
        func=p["func"],
        args=p["args"],
        kwargs_exec=p["kwargs_exec"],  # Changed from kwargs to kwargs_exec
        reload=p["reload"],
        safe=p["safe"],
        debug=p["debug"],
        **exec_kwargs
    )
    
    if p["debug"]:
        print(f"[EXEC-OPS] Completed")
    
    return result


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
