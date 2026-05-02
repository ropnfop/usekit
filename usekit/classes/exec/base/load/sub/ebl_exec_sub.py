# Path: usekit.classes.exec.base.load.sub.ebl_exec_sub.py
# -----------------------------------------------------------------------------------------------
#  Exec SUB Layer - Format Routing ONLY
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Route to format-specific executor
#  
#  Changes from original:
#  - REMOVED: proc_resolve_exec_path() - now handled by OPS layer
#  - REMOVED: proc_exec_function() - merged into route_to_executor()
#  - KEPT: Simple format routing logic
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any

from usekit.classes.common.errors.helper_debug import log_and_raise


# ===============================================================================
# Format Routing (Single Responsibility)
# ===============================================================================

@log_and_raise
def route_to_executor(
    fmt: str,
    path: Path,
    func: str = None,
    args: tuple = (),
    kwargs_exec: dict = None,
    reload: bool = False,
    safe: bool = True,
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Route to format-specific executor.
    
    Single Responsibility: Dispatch to correct POST layer based on format
    
    OPS layer guarantees:
    - path exists and is valid
    - fmt is validated
    - All parameters are processed
    
    SUB layer responsibility:
    - Route to correct executor ONLY
    - No path resolution
    - No parameter processing
    
    Args:
        fmt: Format type (pyp, sql, ddl)
        path: Resolved file path (guaranteed to exist)
        func: Function name to execute
        args: Positional arguments
        kwargs_exec: Keyword arguments
        reload: Reload module before execution
        safe: Safe execution mode
        debug: Debug mode
        **kwargs: Additional executor-specific options
        
    Returns:
        Execution result from POST layer
        
    Raises:
        ValueError: If format not supported
        
    Examples:
        >>> route_to_executor("pyp", Path("utils.pyp"), func="clean", args=(x,))
        cleaned_data
        
        >>> route_to_executor("sql", Path("query.sql"), args=(conn,))
        query_results
    """
    
    if kwargs_exec is None:
        kwargs_exec = {}
    
    if debug:
        print(f"[EXEC-SUB] Routing: {fmt} → {path.name}")
        if func:
            print(f"[EXEC-SUB] Function: {func}")
    
    # Route to format-specific POST layer
    if fmt == "pyp":
        from usekit.classes.exec.base.post.act.ebp_exec_pyp import exec_pyp
        return exec_pyp(
            path=path,
            func=func,
            args=args,
            kwargs_exec=kwargs_exec,
            reload=reload,
            safe=safe,
            debug=debug,
            **kwargs
        )
    
    elif fmt == "sql":
        from usekit.classes.exec.base.post.act.ebp_exec_sql import exec_sql
        return exec_sql(
            path=path,
            func=func,  # For SQL, this might be query name
            args=args,
            kwargs_exec=kwargs_exec,
            debug=debug,
            **kwargs
        )
    
    elif fmt == "ddl":
        from usekit.classes.exec.base.post.act.ebp_exec_ddl import exec_ddl
        return exec_ddl(
            path=path,
            func=func,
            args=args,
            kwargs_exec=kwargs_exec,
            debug=debug,
            **kwargs
        )
    
    else:
        raise ValueError(
            f"Unsupported format: '{fmt}'. "
            f"Expected: pyp, sql, ddl"
        )


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "route_to_executor",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
