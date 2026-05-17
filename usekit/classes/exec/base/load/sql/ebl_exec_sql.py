# Path: usekit.classes.exec.base.load.sql.ebl_exec_sql.py
# -----------------------------------------------------------------------------------------------
#  SQL Exec Operation - SQL-specific logic (v3.0 - Hybrid Interface)
#  Created by: THE Little Prince × ROP × FOP
#
#  Responsibility:
#  - SQL path resolution (inline vs file)
#  - Parameter extraction and delegation to POST layer
#  - Support for hybrid parameter interface (params/args/kwargs)
#
#  Note: SUB layer removed (was unnecessary pass-through after fmt routing in ebl_exec.py)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any
import re

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_keydata_path import search_keydata_paths
from usekit.classes.exec.base.post.act.sql.ebp_exec_sql import exec_sql


SQL_INLINE_KEYWORDS = (
    'SELECT', 'INSERT', 'UPDATE', 'DELETE',
    'WITH', 'CREATE', 'DROP', 'ALTER',
    'PRAGMA', 'EXPLAIN', 'VACUUM', 'ANALYZE',
    'ATTACH', 'DETACH', 'BEGIN', 'COMMIT', 'ROLLBACK',
    'REINDEX', 'SAVEPOINT', 'RELEASE'
)


def _first_sql_token(name: str) -> str:
    """
    Extract the first meaningful SQL token from user input.

    Skips:
    - empty lines
    - leading line comments (-- ...)
    - leading block comments (/* ... */)

    Returns:
        Upper-cased first token, or empty string if not found.
    """
    if not name:
        return ''

    s = name.lstrip()
    n = len(s)
    i = 0

    while i < n:
        # skip whitespace
        while i < n and s[i].isspace():
            i += 1

        if i >= n:
            return ''

        # line comment
        if s.startswith('--', i):
            j = s.find('\n', i)
            if j == -1:
                return ''
            i = j + 1
            continue

        # block comment
        if s.startswith('/*', i):
            j = s.find('*/', i + 2)
            if j == -1:
                return ''
            i = j + 2
            continue

        break

    if i >= n:
        return ''

    m = re.match(r'[A-Za-z_]+', s[i:])
    return m.group(0).upper() if m else ''


def _is_inline_sql(name: str) -> bool:
    """
    Detect whether the input should be treated as inline SQL text.

    Rules:
    - first meaningful token must be a SQL keyword
    - prevents false positives like `select_user_info`
    """
    token = _first_sql_token(name)
    return token in SQL_INLINE_KEYWORDS


@log_and_raise
def exec_sql_operation(p: dict) -> Any:
    """
    SQL execution operation.
    
    SQL-specific complexity:
    - Inline SQL detection (starts with SELECT/INSERT/etc)
    - File-based SQL resolution
    - Hybrid parameter support (params/args/kwargs)
    
    Args:
        p: Normalized parameters from params_for_exec()
        
    Returns:
        Query results (SELECT) or affected rows (DML)
        
    Examples:
        # Inline SQL with direct kwargs
        >>> exec_sql_operation({
        ...     "name": "SELECT * FROM users WHERE id = :id",
        ...     "kwargs_exec": {'id': 10},
        ...     "db": conn,
        ...     ...
        ... })
        
        # File-based SQL with positional args
        >>> exec_sql_operation({
        ...     "name": "select_user_info",
        ...     "args": (10, 20),
        ...     "loc": "base",
        ...     "db": conn,
        ...     ...
        ... })
        
        # File-based SQL with explicit params
        >>> exec_sql_operation({
        ...     "name": "select_user_info",
        ...     "params": {'user_id': 10, 'min_age': 20},
        ...     "loc": "base",
        ...     "db": conn,
        ...     ...
        ... })
    """
    
    if p["debug"]:
        print(f"[EXEC-SQL] Starting SQL operation")
        print(f"[EXEC-SQL] Original pattern: {p.get('name')}")
    
    # Check if inline SQL before treating the input as a file pattern.
    # This is important for commands like:
    #   PRAGMA table_info("users")
    # which are valid SQL but do not look like filenames.
    name = p.get('name', '')
    is_inline = _is_inline_sql(name)

    if p["debug"]:
        first_token = _first_sql_token(name)
        print(f"[EXEC-SQL] First SQL token: {first_token or '<none>'}")
        print(f"[EXEC-SQL] Inline SQL detected: {is_inline}")

    if is_inline:
        # Inline SQL - pass directly to POST layer
        if p["debug"]:
            print(f"[EXEC-SQL] Detected inline SQL")
            print(f"[EXEC-SQL] SQL: {name[:100]}...")
        
        # Delegate to POST with hybrid interface
        return _delegate_to_post(
            sql_or_path=name,
            p=p,
            inline=True
        )
  
    else:
        # File pattern - resolve path first
        if p["debug"]:
            print(f"[EXEC-SQL] Detected file pattern")
        
        target_path = _resolve_sql_path(p)
        
        if p["debug"]:
            print(f"[EXEC-SQL] Resolved: {target_path}")
        
        # Delegate to POST with hybrid interface
        return _delegate_to_post(
            sql_or_path=target_path,
            p=p,
            inline=False
        )


def _resolve_sql_path(p: dict) -> Path:
    """
    Resolve SQL file path.
    
    SQL doesn't need keydata search (no content-based search needed).
    Just find the .sql file by pattern.
    
    Args:
        p: Normalized parameters
        
    Returns:
        Resolved Path object
        
    Raises:
        FileNotFoundError: If SQL file not found
    """
    
    # Strategy 1: Direct path (highest priority)
    if p["path"]:
        path_obj = Path(p["path"]) if isinstance(p["path"], str) else p["path"]
        if not path_obj.is_file():
            raise FileNotFoundError(f"SQL file not found: {path_obj}")
        return path_obj
    
    # Strategy 2: Search by pattern
    pattern = p.get("name") or "*"
    
    if p["debug"]:
        print(f"[EXEC-SQL] Searching: pattern={pattern}")
        print(f"[EXEC-SQL] Location: user_dir={p.get('dir_path')}, cus={p.get('cus')}")
    
    # Use search_keydata_paths for consistency with PYP
    # keydata=None means pure file search (no content filtering)
    paths = search_keydata_paths(
        fmt="sql",
        mod=p["mod"],
        pattern=pattern,
        keydata=None,  # None = file search only, no content filtering
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
            f"No SQL file found{error_desc} "
            f"(loc={p['ov_loc'] or p['loc']}, mod={p['mod']})"
        )
    
    if len(paths) > 1:
        raise ValueError(
            f"Multiple SQL files found for pattern '{pattern}': "
            f"{[str(path) for path in paths]}"
        )
    
    return paths[0]


def _delegate_to_post(sql_or_path: Any, p: dict, inline: bool = False) -> Any:
    """
    Delegate to POST layer with hybrid parameter interface.
    
    Supports 3 parameter modes:
    1. params (explicit) - highest priority
    2. args (positional) - medium priority
    3. kwargs_exec (named) - lowest priority
    
    Args:
        sql_or_path: SQL text or file path
        p: Normalized parameters
        inline: True if sql_or_path is raw SQL text, False if it is a resolved file path
        
    Returns:
        Execution result
    """
    
    debug = p["debug"]
    
    # Extract parameters based on priority
    # Priority 1: explicit params
    if 'params' in p and p['params'] is not None:
        if debug:
            print(f"[EXEC-SQL] Using explicit params: {p['params']}")
        
        return exec_sql(
            sql_or_path,
            params=p['params'],
            db=p.get('db'),
            safe=p.get('safe', True),
            debug=debug,
            inline=inline
        )
    
    # Priority 2: positional args
    elif p.get('args'):
        sql_params = p['args']
        if debug:
            print(f"[EXEC-SQL] Using positional args: {sql_params}")
        
        return exec_sql(
            sql_or_path,
            *sql_params,  # Unpack positional args
            db=p.get('db'),
            safe=p.get('safe', True),
            debug=debug,
            inline=inline
        )
    
    # Priority 3: named kwargs (kwargs_exec or kwargs)
    else:
        # Reserved parameter names (not SQL parameters)
        # These are all USEKIT internal parameters from navi_signature
        reserved = {
            # Core parameters
            'fmt', 'name', 'path', 'raw_name', 'alias',
            
            # Execution parameters
            'db', 'safe', 'debug', 'params', 'args', 'kwargs_exec', 'kwargs',
            
            # Search/Location parameters
            'loc', 'ov_loc', 'mod', 'cus', 'dir_path', 'walk', 
            'case_sensitive', 'keydata', 'from_list',
            
            # Format parameters
            'ov_fmt', 'as_name',
            
            # Loading parameters
            'lazy', 'init_args', 'config_path',
            
            # Key-value search parameters
            'k', 'kv', 'kc', 'kf',
            
            # PYP-specific parameters
            'reload', 'func', 'key_type', 'module_name',
            
            # Search options
            'regex', 'recursive', 'find_all', 'line_numbers', 
            'keydata_exists', 'with_values',
            
            # Execution modes
            'mode', 'mode_sub', 'inline',
            
            # Process execution parameters
            'timeout', 'cwd', 'env',
            
            # Error handling
            'raise_errors', 'fallback'
        }
        
        # Try kwargs_exec first
        if p.get('kwargs_exec'):
            named_params = p['kwargs_exec']
        # Try kwargs second
        elif p.get('kwargs'):
            named_params = p['kwargs']
        # Extract from p dict (exclude reserved)
        else:
            named_params = {k: v for k, v in p.items() if k not in reserved}
        
        if named_params:
            if debug:
                print(f"[EXEC-SQL] Using named params: {named_params}")
        else:
            if debug:
                print(f"[EXEC-SQL] No SQL parameters")
        
        return exec_sql(
            sql_or_path,
            db=p.get('db'),
            safe=p.get('safe', True),
            debug=debug,
            inline=inline,
            **named_params  # Safe to unpack - always a dict
        )


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
