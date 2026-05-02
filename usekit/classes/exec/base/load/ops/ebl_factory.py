# Path: usekit.classes.exec.base.load.ops.ebl_factory.py
# -----------------------------------------------------------------------------------------------
#  Exec Factory - Auto Routing by Format
#  Created by: THE Little Prince × ROP × FOP
#  Version: v1.0 - Following parser_factory pattern
# -----------------------------------------------------------------------------------------------
"""
Ultra-simple architecture:

1. EXTENSION_MAP: format → extension
2. Exec modules: ebl_exec_{format}.py
3. Auto-routing: fmt → exec_{fmt}_operation()

That's it.
"""

import importlib
from functools import lru_cache
from typing import Any, Callable

from usekit.classes.common.utils.helper_const import get_const


# ===============================================================================
# Core: Format → Exec Handler
# ===============================================================================

@lru_cache(maxsize=1)
def _get_exec_formats() -> dict:
    """
    Get executable formats from EXTENSION_MAP.
    
    Returns:
        Dict of format → extension for executable types
    """
    try:
        ext_map = get_const("EXTENSION_MAP")
        # Filter executable formats only
        exec_formats = {
            fmt: ext for fmt, ext in ext_map.items()
            if fmt in {"pyp", "sql", "ddl"}  # Add more as needed
        }
        return exec_formats
    except Exception:
        # Minimal fallback
        return {
            "pyp": ".py",
            "sql": ".sql",
            "ddl": ".sql",
        }


@lru_cache(maxsize=32)
def get_exec_handler(fmt: str) -> Callable:
    """
    Get exec handler function for format.
    
    Logic:
        1. Validate format in exec_formats
        2. Load ebl_exec_{fmt}.py
        3. Return exec_{fmt}_operation function
    
    Args:
        fmt: Format name (pyp, sql, ddl, etc.)
        
    Returns:
        Exec handler function: exec_{fmt}_operation
        
    Raises:
        ValueError: If format not supported
        ImportError: If handler module not found
        
    Examples:
        >>> handler = get_exec_handler("pyp")
        >>> handler(params)  # calls exec_pyp_operation(params)
        
        >>> handler = get_exec_handler("sql")
        >>> handler(params)  # calls exec_sql_operation(params)
    """
    fmt = fmt.lower().strip()
    
    # Validate format
    exec_formats = _get_exec_formats()
    if fmt not in exec_formats:
        raise ValueError(
            f"Format '{fmt}' not executable. "
            f"Supported: {', '.join(sorted(exec_formats.keys()))}"
        )
    
    # Load exec module
    module_name = f"usekit.classes.exec.base.load.{fmt}.ebl_exec_{fmt}"
    func_name = f"exec_{fmt}_operation"
    
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise ImportError(
            f"Exec module not found: {module_name}\n"
            f"Expected file: ebl_exec_{fmt}.py"
        )
    
    # Get handler function
    try:
        handler = getattr(module, func_name)
    except AttributeError:
        raise ImportError(
            f"Function '{func_name}' not found in {module_name}\n"
            f"Expected: def {func_name}(p: dict) -> Any"
        )
    
    return handler


# ===============================================================================
# Utilities
# ===============================================================================

def list_exec_formats() -> list:
    """List all executable formats."""
    return sorted(_get_exec_formats().keys())


def is_exec_format(fmt: str) -> bool:
    """Check if format is executable."""
    return fmt.lower() in _get_exec_formats()


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "get_exec_handler",
    "list_exec_formats",
    "is_exec_format",
]


# ===============================================================================
# Test
# ===============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Exec Factory v1.0 - Auto Routing")
    print("=" * 60)
    print()
    
    # Show all formats
    print("Executable Formats:")
    for fmt in list_exec_formats():
        ext = _get_exec_formats()[fmt]
        print(f"  {fmt:8s} → {ext:8s} → ebl_exec_{fmt}.py")
    print()
    
    # Test handler loading
    print("Handler Loading Test:")
    for fmt in list_exec_formats():
        try:
            handler = get_exec_handler(fmt)
            print(f"  ✓ {fmt:8s} → {handler.__name__}")
        except Exception as e:
            print(f"  ✗ {fmt:8s} → {e}")
    print()
    
    print("=" * 60)
    print("Architecture:")
    print("  EXTENSION_MAP (sys_const.yaml)")
    print("    ↓")
    print("  exec_factory.py")
    print("    ↓")
    print("  ebl_exec_{format}.py")
    print("    ↓")
    print("  exec_{format}_operation()")
    print("=" * 60)
