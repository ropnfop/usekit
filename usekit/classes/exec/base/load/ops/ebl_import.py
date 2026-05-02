# Path: usekit.classes.exec.base.load.ops.ebl_import.py
# -----------------------------------------------------------------------------------------------
#  Import Operation - Main Load Layer (OPS)
#  Created by: THE Little Prince × ROP × FOP
#
#  Philosophy:
#  - OPS layer resolves ALL paths using helper_keydata_path
#  - Handles multiple function imports (mod:f1,f2,f3)
#  - SUB layer only routes to format-specific importers
#  - No duplicate path resolution logic
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List

from usekit.infra.exec_signature import params_for_import, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_keydata_path import search_keydata_first
from usekit.classes.exec.base.load.sub.ebl_import_sub import route_to_importer


# ===============================================================================
# Parameter Filtering
# ===============================================================================

# Parameters used only at ops layer (should NOT be passed to sub/parser)
OPS_ONLY_PARAMS = {
    # Pattern parsing results
    'raw_name', 'alias',
    
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
    
    # Import-specific ops params
    'ov_fmt', 'ov_loc', 'func', 'key_type', 'from_list', 'as_name'
}


def _extract_import_kwargs(params: dict) -> dict:
    """Extract parameters safe for import sub/parser layers."""
    EXPLICIT_PARAMS = {'func', 'from_list', 'as_name', 'lazy', 'debug'}
    exclude = OPS_ONLY_PARAMS | EXPLICIT_PARAMS
    return {k: v for k, v in params.items() if k not in exclude}


# ===============================================================================
# Function List Parsing
# ===============================================================================

def _parse_func_list(func_spec: str | None) -> List[str] | None:
    """
    Parse comma-separated function list.
    
    Args:
        func_spec: "f1,f2,f3" or "f1" or None
        
    Returns:
        ["f1", "f2", "f3"] or ["f1"] or None
        
    Examples:
        >>> _parse_func_list("add,sub,mul")
        ['add', 'sub', 'mul']
        >>> _parse_func_list("add")
        ['add']
        >>> _parse_func_list(None)
        None
    """
    if func_spec is None:
        return None
    
    if ',' in func_spec:
        return [f.strip() for f in func_spec.split(',') if f.strip()]
    else:
        return [func_spec.strip()]


# ===============================================================================
# Universal Path Resolution (Single Source of Truth)
# ===============================================================================

def _resolve_import_path(p: dict) -> Path:
    """
    Universal path resolution for ALL import formats.
    
    Similar to _resolve_exec_path but no content search needed.
    Import only needs file-level resolution.
    
    Args:
        p: Normalized parameters from params_for_import
        
    Returns:
        Resolved file path
        
    Raises:
        FileNotFoundError: If file not found
        
    Examples:
        >>> _resolve_import_path({"name": "utils", "loc": "base", ...})
        Path("/base/utils.pyp")
        
        >>> _resolve_import_path({"name": "helpers", "dir_path": "lib", ...})
        Path("/base/lib/helpers.pyp")
    """
    
    # Strategy 1: Direct path provided
    if p.get("path"):
        path_obj = Path(p["path"]) if isinstance(p["path"], str) else p["path"]
        if not path_obj.is_file():
            raise FileNotFoundError(f"Import target not found: {path_obj}")
        return path_obj
    
    # Determine effective format and location
    effective_fmt = p["ov_fmt"] or p["fmt"]
    effective_loc = p["ov_loc"] or p["loc"]
    
    # Determine search parameters
    pattern = p.get("name") or "*"
    keydata = None  # Import doesn't need content search
    
    if p["debug"]:
        print(f"[IMPORT-OPS] Path resolution:")
        print(f"  fmt={effective_fmt}, loc={effective_loc}")
        print(f"  pattern={pattern}")
        print(f"  dir_path={p.get('dir_path')}, cus={p.get('cus')}")
        if p.get("func"):
            print(f"  functions={p.get('func')}")
    
    # Strategy 2/3: Unified search via helper_keydata_path
    result = search_keydata_first(
        fmt=effective_fmt,
        mod=p["mod"],
        pattern=pattern,
        keydata=keydata,  # No content search for import
        loc=effective_loc,
        user_dir=p.get("dir_path"),
        cus=p.get("cus"),
        walk=p["walk"],
        case_sensitive=p["case_sensitive"],
        key_type=None,  # Not needed for file-level search
        debug=p["debug"]
    )
    
    if result is None:
        # Build descriptive error message
        search_parts = []
        if pattern != "*":
            search_parts.append(f"pattern '{pattern}'")
        if p.get("dir_path"):
            search_parts.append(f"dir_path '{p['dir_path']}'")
        if p.get("cus"):
            search_parts.append(f"cus '{p['cus']}'")
        
        search_desc = " with " + " and ".join(search_parts) if search_parts else ""
        
        raise FileNotFoundError(
            f"No {effective_fmt} file found{search_desc} "
            f"(loc={effective_loc}, mod={p['mod']})"
        )
    
    return result


# ===============================================================================
# Main Import Operation (OPS Entry Point)
# ===============================================================================

@log_and_raise
def import_operation(**kwargs) -> Any:
    """
    Import module/functions (IMPORT MODE ONLY).
    
    Core responsibilities:
    1. Normalize parameters via params_for_import
    2. Resolve target file path (single source of truth)
    3. Parse function list if provided (mod:f1,f2,f3)
    4. Delegate to SUB layer for format-specific import
    
    Key differences from exec_operation:
    - Handles multiple function imports (f1,f2,f3)
    - No args/kwargs_exec (import doesn't execute)
    - Returns imported objects (module or function dict)
    
    Single Responsibility: Resolve path + delegate to format importer
    
    Examples (After implementation):
        # Single module
        >>> import_operation(name="utils")
        <module 'utils'>
        
        # Multiple functions
        >>> import_operation(name="utils", func="add,sub,mul")
        {'add': <function>, 'sub': <function>, 'mul': <function>}
        
        # Nested path
        >>> import_operation(name="utils", dir_path="helpers")
        # Searches: /base/helpers/utils.pyp
        
        # Custom preset
        >>> import_operation(name="utils", cus="job01")
        # Searches: /custom/jobs/job01/utils.pyp
        
        # Combined
        >>> import_operation(name="utils", dir_path="lib", func="clean,parse", cus="job01")
        # Searches: /custom/jobs/job01/lib/utils.pyp
        # Returns: {'clean': <function>, 'parse': <function>}
    """
    
    # Force import mode
    kwargs["mode"] = "import"
    
    # Process parameters
    warn_future_features(kwargs)
    p = params_for_import(**kwargs)
    
    if p["debug"]:
        print(f"[IMPORT-OPS] Starting: fmt={p['fmt']}, mode={p['mode']}")
        if p.get("raw_name"):
            print(f"[IMPORT-OPS] Original pattern: {p['raw_name']}")
        if p["ov_fmt"]:
            print(f"[IMPORT-OPS] Format override: {p['ov_fmt']}")
        if p["ov_loc"]:
            print(f"[IMPORT-OPS] Location override: {p['ov_loc']}")
        if p.get("name"):
            print(f"[IMPORT-OPS] Target name: {p['name']}")
        if p.get("func"):
            print(f"[IMPORT-OPS] Functions: {p['func']}")
        if p.get("dir_path"):
            print(f"[IMPORT-OPS] Directory: {p['dir_path']}")
        if p.get("cus"):
            print(f"[IMPORT-OPS] Custom preset: {p['cus']}")
    
    # Resolve path (single source of truth)
    target_path = _resolve_import_path(p)
    
    if p["debug"]:
        print(f"[IMPORT-OPS] Resolved: {target_path}")
    
    # Parse function list (mod:f1,f2,f3 → ["f1", "f2", "f3"])
    func_list = _parse_func_list(p.get("func"))
    
    if p["debug"] and func_list:
        print(f"[IMPORT-OPS] Function list: {func_list}")
    
    # Determine effective format
    effective_fmt = p["ov_fmt"] or p["fmt"]
    
    # Extract import kwargs (remove OPS-only params)
    import_kwargs = _extract_import_kwargs(p)
    
    # Delegate to SUB layer (format routing)
    result = route_to_importer(
        fmt=effective_fmt,
        path=target_path,
        func_list=func_list,
        from_list=p.get("from_list"),
        as_name=p.get("as_name"),
        lazy=p.get("lazy", False),
        debug=p["debug"],
        **import_kwargs
    )
    
    if p["debug"]:
        print(f"[IMPORT-OPS] Completed")
    
    return result


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "import_operation",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
