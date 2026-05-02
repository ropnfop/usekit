# Path: usekit.classes.exec.base.load.pyp.ebl_exec_pyp.py
# -----------------------------------------------------------------------------------------------
#  PYP Exec Operation - PYP-specific logic
#  Created by: THE Little Prince × ROP × FOP
#
#  Responsibility:
#  - PYP path resolution (func-based search)
#  - Direct POST layer execution
#
#  Note: SUB layer removed (was unnecessary pass-through after fmt routing in ebl_exec.py)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_keydata_path import search_keydata_first
from usekit.classes.exec.base.post.act.pyp.ebp_exec_pyp import exec_pyp


@log_and_raise
def exec_pyp_operation(p: dict) -> Any:
    """
    PYP execution operation.
    
    PYP-specific complexity:
    - Function-based search (keydata = func name)
    - Path resolution with content search
    - Module reload handling
    
    Args:
        p: Normalized parameters from params_for_exec()
        
    Returns:
        Execution result
        
    Examples:
        >>> exec_pyp_operation({
        ...     "name": "test01",
        ...     "dir_path": "test",
        ...     "func": "add",
        ...     "args": (1, 2),
        ...     ...
        ... })
        3
    """
    
    if p["debug"]:
        print(f"[EXEC-PYP] Starting PYP operation")
        if p.get("func"):
            print(f"[EXEC-PYP] Function: {p['func']}")
    
    # Resolve PYP path
    target_path = _resolve_pyp_path(p)
    
    if p["debug"]:
        print(f"[EXEC-PYP] Resolved: {target_path}")
    
    # Direct POST execution (SUB layer removed)
    return exec_pyp(
        path=target_path,
        func=p.get("func"),
        args=p.get("args", ()),
        kwargs_exec=p.get("kwargs_exec") or p.get("kwargs", {}),
        reload=p.get("reload", False),
        safe=p.get("safe", True),
        debug=p["debug"]
    )


def _resolve_pyp_path(p: dict) -> Path:
    """
    Resolve PYP file path using function-based search.
    
    PYP needs keydata search because:
    - Must find specific function in file
    - Cannot rely on filename alone
    
    Args:
        p: Normalized parameters
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If PYP file or function not found
    """
    
    # Strategy 1: Direct path (highest priority)
    if p["path"]:
        path_obj = Path(p["path"]) if isinstance(p["path"], str) else p["path"]
        if not path_obj.is_file():
            raise FileNotFoundError(f"PYP file not found: {path_obj}")
        return path_obj
    
    # Strategy 2: Search with function name (keydata)
    pattern = p.get("name") or "*"
    keydata = p.get("func")  # Function name for content search
    
    # Determine key_type
    key_type = p.get("key_type") or "def"
    if key_type == "auto":
        key_type = "def"
    
    if p["debug"]:
        print(f"[EXEC-PYP] Searching: pattern={pattern}, func={keydata}")
        print(f"[EXEC-PYP] Location: dir_path={p.get('dir_path')}, cus={p.get('cus')}")
    
    # Search for PYP file containing function
    result = search_keydata_first(
        fmt="pyp",
        mod=p["mod"],
        pattern=pattern,
        keydata=keydata,
        loc=p["ov_loc"] or p["loc"],
        user_dir=p.get("dir_path"),
        cus=p.get("cus"),
        walk=p["walk"],
        case_sensitive=p["case_sensitive"],
        key_type=key_type,
        debug=p["debug"]
    )
    
    if result is None:
        # Build descriptive error
        error_parts = []
        if keydata:
            error_parts.append(f"function '{keydata}'")
        if pattern != "*":
            error_parts.append(f"pattern '{pattern}'")
        if p.get("dir_path"):
            error_parts.append(f"dir_path '{p['dir_path']}'")
        if p.get("cus"):
            error_parts.append(f"cus '{p['cus']}'")
        
        error_desc = " with " + " and ".join(error_parts) if error_parts else ""
        
        raise FileNotFoundError(
            f"No PYP file found{error_desc} "
            f"(loc={p['ov_loc'] or p['loc']}, mod={p['mod']})"
        )
    
    return result

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
