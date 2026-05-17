# Path: usekit.classes.exec.base.load.ddl.ebl_exec_ddl.py
# -----------------------------------------------------------------------------------------------
#  DDL Exec Operation - DDL-specific logic with auto-save
#  Created by: THE Little Prince × ROP × FOP
#
#  Responsibility:
#  - DDL path resolution (inline vs file)
#  - Raw DDL detection (CREATE/ALTER/DROP/TRUNCATE)
#  - Auto-save flag for POST layer
#  - Parameter delegation to POST layer
#
#  Based on: ebl_exec_sql.py
#  Key difference: DDL auto-saves raw statements
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_keydata_path import search_keydata_paths
from usekit.classes.exec.base.post.act.ddl.ebp_exec_ddl import exec_ddl


@log_and_raise
def exec_ddl_operation(p: dict) -> Any:
    """
    DDL execution operation with auto-save for raw DDL.
    
    DDL-specific features:
    - Inline DDL detection (CREATE/ALTER/DROP/TRUNCATE)
    - File-based DDL resolution
    - Auto-save raw DDL to schema files
    
    Args:
        p: Normalized parameters from params_for_exec()
        
    Returns:
        Execution result (affected rows)
        
    Examples:
        # Inline DDL with auto-save
        >>> exec_ddl_operation({
        ...     "name": "CREATE TABLE users (id INT, name TEXT)",
        ...     "db": conn,
        ...     ...
        ... })
        # → Saves to users.sql + executes
        
        # File-based DDL (no save)
        >>> exec_ddl_operation({
        ...     "name": "users",
        ...     "loc": "base",
        ...     "db": conn,
        ...     ...
        ... })
        # → Loads users.sql + executes
    """
    
    if p["debug"]:
        print(f"[EXEC-DDL] Starting DDL operation")
        print(f"[EXEC-DDL] Original pattern: {p.get('name')}")
    
    # Check if inline DDL (starts with DDL keywords)
    name = p.get('name', '')
    
    # For multiline DDL, check first non-empty line
    first_line = ''
    for line in name.split('\n'):
        stripped = line.strip()
        if stripped:
            first_line = stripped
            break
    
    # DDL keywords (schema operations only)
    ddl_keywords = (
        'CREATE', 'ALTER', 'DROP', 'TRUNCATE'
    )
    
    # Check if first line starts with DDL keyword
    first_line_upper = first_line.upper()
    is_inline = any(
        first_line_upper.startswith(keyword + ' ') or first_line_upper == keyword
        for keyword in ddl_keywords
    )
    
    if is_inline:
        # Inline DDL - pass directly to POST layer with auto-save
        if p["debug"]:
            print(f"[EXEC-DDL] Detected inline DDL")
            print(f"[EXEC-DDL] DDL: {name[:100]}...")
        
        # Delegate to POST with auto-save enabled
        return _delegate_to_post(
            ddl_or_path=name,
            p=p,
            is_raw_ddl=True  # Enable auto-save
        )
    
    else:
        # File pattern - resolve path first
        if p["debug"]:
            print(f"[EXEC-DDL] Detected file pattern")
        
        target_path = _resolve_ddl_path(p)
        
        if p["debug"]:
            print(f"[EXEC-DDL] Resolved: {target_path}")
        
        # Delegate to POST (no auto-save for file)
        return _delegate_to_post(
            ddl_or_path=target_path,
            p=p,
            is_raw_ddl=False  # File mode, no save
        )


def _resolve_ddl_path(p: dict) -> Path:
    """
    Resolve DDL file path.
    
    DDL doesn't need keydata search (no content-based search needed).
    Just find the .sql file by pattern.
    
    Args:
        p: Normalized parameters
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If DDL file not found
    """
    
    # Strategy 1: Direct path (highest priority)
    if p["path"]:
        path_obj = Path(p["path"]) if isinstance(p["path"], str) else p["path"]
        if not path_obj.is_file():
            raise FileNotFoundError(f"DDL file not found: {path_obj}")
        return path_obj
    
    # Strategy 2: Search by pattern
    pattern = p.get("name") or "*"
    
    if p["debug"]:
        print(f"[EXEC-DDL] Searching: pattern={pattern}")
        print(f"[EXEC-DDL] Location: user_dir={p.get('dir_path')}, cus={p.get('cus')}")
    
    # Use search_keydata_paths for consistency
    # keydata=None means pure file search (no content filtering)
    paths = search_keydata_paths(
        fmt="ddl",
        mod=p["mod"],
        pattern=pattern,
        keydata=None,  # None = file search only
        loc=p["ov_loc"] or p["loc"],
        user_dir=p.get("dir_path"),
        cus=p.get("cus"),
        walk=p["walk"],
        case_sensitive=p["case_sensitive"],
        debug=p["debug"]
    )
    
    if not paths:
        # Build descriptive error
        error_parts = []
        if pattern != "*":
            error_parts.append(f"pattern '{pattern}'")
        if p.get("dir_path"):
            error_parts.append(f"user_dir '{p['dir_path']}'")
        if p.get("cus"):
            error_parts.append(f"cus '{p['cus']}'")
        
        error_desc = " with " + " and ".join(error_parts) if error_parts else ""
        
        raise FileNotFoundError(
            f"No DDL file found{error_desc} "
            f"(loc={p['ov_loc'] or p['loc']}, mod={p['mod']})"
        )
    
    if len(paths) > 1:
        raise ValueError(
            f"Multiple DDL files found for pattern '{pattern}': "
            f"{[str(path) for path in paths]}"
        )
    
    return paths[0]


def _delegate_to_post(ddl_or_path: Any, p: dict, is_raw_ddl: bool) -> Any:
    """
    Delegate to POST layer.
    
    Args:
        ddl_or_path: DDL text or file path
        p: Normalized parameters
        is_raw_ddl: True if raw DDL (enable auto-save)
        
    Returns:
        Execution result
    """
    
    debug = p["debug"]
    
    if debug:
        if is_raw_ddl:
            print(f"[EXEC-DDL] Raw DDL mode: auto-save enabled")
        else:
            print(f"[EXEC-DDL] File mode: loading from path")
    
    # Call POST layer
    return exec_ddl(
        ddl_or_path,
        db=p.get('db'),
        auto_save=is_raw_ddl,  # Auto-save only for raw DDL
        safe=p.get('safe', True),
        debug=debug
    )


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
