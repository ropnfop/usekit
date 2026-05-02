# Path: usekit.classes.exec.base.load.ops.ebl_exec.py
# -----------------------------------------------------------------------------------------------
#  Exec Entry Point - Ultra Lightweight with Factory Pattern
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Format routing via factory
#  Following parser_factory.py pattern
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Any

from usekit.infra.exec_signature import params_for_exec, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.exec.base.load.ops.ebl_factory import get_exec_handler


@log_and_raise
def exec_operation(**kwargs) -> Any:
    """
    Exec entry point - Routes to format-specific operation via factory.
    
    Ultra lightweight architecture:
    1. Parameter normalization
    2. Format detection
    3. Auto-routing via exec_factory
    
    The factory automatically loads:
    - ebl_exec_pyp.py → exec_pyp_operation()
    - ebl_exec_sql.py → exec_sql_operation()
    - ebl_exec_ddl.py → exec_ddl_operation()
    
    Examples:
        >>> exec_operation(name="test.utils:clean", fmt="pyp", x=data)
        # Factory routes to → exec_pyp_operation()
        
        >>> exec_operation(name="SELECT * FROM users", fmt="sql", db=conn)
        # Factory routes to → exec_sql_operation()
        
        >>> exec_operation(name="@q:user_query", fmt="sql", db=conn)
        # Factory routes to → exec_sql_operation()
    """
    
    # Force exec mode
    kwargs["mode"] = "exec"
    
    # Process parameters (common for all formats)
    warn_future_features(kwargs)
    p = params_for_exec(**kwargs)
    
    # Get effective format
    effective_fmt = p["ov_fmt"] or p["fmt"]
    
    if p["debug"]:
        print(f"[EXEC-ENTRY] Routing to {effective_fmt.upper()} handler")
        if p.get("name"):
            print(f"[EXEC-ENTRY] Target: {p['name']}")
    
    # Auto-route via factory
    try:
        handler = get_exec_handler(effective_fmt)
        return handler(p)
    except ValueError as e:
        # Format not supported
        from usekit.classes.exec.base.load.ops.ebl_factory import list_exec_formats
        raise ValueError(
            f"Unsupported format: '{effective_fmt}'. "
            f"Supported: {', '.join(list_exec_formats())}"
        ) from e
    except ImportError as e:
        # Handler module not found
        raise ImportError(
            f"Handler for '{effective_fmt}' not available: {e}"
        ) from e


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------