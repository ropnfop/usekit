# Path: usekit.classes.exec.base.load.sub.ebl_import_sub.py
# -----------------------------------------------------------------------------------------------
#  Import SUB Layer - Format Routing ONLY
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Route to format-specific importer
#  
#  Similar to ebl_exec_sub.py but for import operations
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Optional

from usekit.classes.common.errors.helper_debug import log_and_raise


# ===============================================================================
# Format Routing (Single Responsibility)
# ===============================================================================

@log_and_raise
def route_to_importer(
    fmt: str,
    path: Path,
    func_list: List[str] | None = None,
    from_list: List[str] | None = None,
    as_name: str | None = None,
    lazy: bool = False,
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Route to format-specific importer.
    
    Single Responsibility: Dispatch to correct POST layer based on format
    
    OPS layer guarantees:
    - path exists and is valid
    - fmt is validated
    - All parameters are processed
    - func_list is parsed (["f1", "f2", "f3"] or None)
    
    SUB layer responsibility:
    - Route to correct importer ONLY
    - No path resolution
    - No parameter processing
    
    Args:
        fmt: Format type (pyp, sql, ddl)
        path: Resolved file path (guaranteed to exist)
        func_list: List of function names to import (None = import module)
        from_list: For future "from X import Y" syntax
        as_name: For future "import X as Y" syntax
        lazy: Lazy import (defer until first use)
        debug: Debug mode
        **kwargs: Additional importer-specific options
        
    Returns:
        Import result from POST layer:
        - If func_list is None: module object
        - If func_list provided: dict of {func_name: function_obj}
        
    Raises:
        ValueError: If format not supported
        
    Examples:
        >>> route_to_importer("pyp", Path("utils.pyp"))
        <module 'utils'>
        
        >>> route_to_importer("pyp", Path("utils.pyp"), func_list=["add", "sub"])
        {'add': <function>, 'sub': <function>}
    """
    
    if debug:
        print(f"[IMPORT-SUB] Routing: {fmt} → {path.name}")
        if func_list:
            print(f"[IMPORT-SUB] Functions: {func_list}")
    
    # Route to format-specific POST layer
    if fmt == "pyp":
        from usekit.classes.exec.base.post.act.pyp.ebp_import_pyp import import_pyp
        return import_pyp(
            path=path,
            func_list=func_list,
            from_list=from_list,
            as_name=as_name,
            lazy=lazy,
            debug=debug,
            **kwargs
        )
    
    elif fmt == "sql":
        from usekit.classes.exec.base.post.act.sql.ebp_import_sql import import_sql
        return import_sql(
            path=path,
            func_list=func_list,
            debug=debug,
            **kwargs
        )
    
    elif fmt == "ddl":
        from usekit.classes.exec.base.post.act.ddl.ebp_import_ddl import import_ddl
        return import_ddl(
            path=path,
            func_list=func_list,
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
    "route_to_importer",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
