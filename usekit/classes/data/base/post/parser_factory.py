# Path: usekit.classes.data.base.post.parser_factory.py
# -----------------------------------------------------------------------------------------------
#  Parser Factory - Extreme Simplicity
#  Created by: THE Little Prince × ROP × FOP'
#  Version: v4.0 - Maximum simplicity: EXTENSION_MAP → Parser
# -----------------------------------------------------------------------------------------------
"""
Ultra-simple architecture:

1. EXTENSION_MAP: object → extension
2. Parser files: parser_{object}.py
3. Special case: parser_any.py → calls parser_txt.py

That's it.
"""

import importlib
from functools import lru_cache
from typing import Any

from usekit.classes.common.utils.helper_const import get_const


# ===============================================================================
# Core: EXTENSION_MAP → Parser Module
# ===============================================================================

@lru_cache(maxsize=1)
def _get_extension_map() -> dict:
    """Get EXTENSION_MAP from sys_const.yaml."""
    try:
        return get_const("EXTENSION_MAP")
    except Exception:
        # Minimal fallback
        return {
            "json": ".json",
            "yaml": ".yaml",
            "txt": ".txt",
            "csv": ".csv",
            "md": ".md",
            "pkl": ".pkl",
            "pyp": ".py",
            "ddl": ".sql",
            "sql": ".sql",
            "any": ".log",
        }


@lru_cache(maxsize=32)
def get_parser_by_format(fmt: str) -> Any:
    """
    Get parser for format.
    
    Logic:
        1. Check EXTENSION_MAP
        2. Load parser_{fmt}.py
        3. Special: parser_any.py → parser_txt.py
    
    Args:
        fmt: Format name from EXTENSION_MAP
        
    Returns:
        Parser module
        
    Example:
        parser = get_parser_by_format("json")  # → parser_json
        parser = get_parser_by_format("any")   # → parser_txt (via parser_any)
    """
    fmt = fmt.lower().strip()
    
    # Validate format exists in EXTENSION_MAP
    ext_map = _get_extension_map()
    if fmt not in ext_map:
        raise ValueError(
            f"Format '{fmt}' not in EXTENSION_MAP. "
            f"Available: {', '.join(sorted(ext_map.keys()))}"
        )
   
    # Load parser module
    module_name = f"usekit.classes.data.base.post.parser.parser_{fmt}"
    
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        raise ImportError(
            f"Parser module not found: {module_name}\n"
            f"Expected file: parser_{fmt}.py"
        )


# ===============================================================================
# Utilities
# ===============================================================================

def list_formats() -> list:
    """List all formats in EXTENSION_MAP."""
    return sorted(_get_extension_map().keys())


def get_extension(fmt: str) -> str:
    """Get extension for format from EXTENSION_MAP."""
    ext_map = _get_extension_map()
    if fmt not in ext_map:
        raise ValueError(f"Format '{fmt}' not in EXTENSION_MAP")
    return ext_map[fmt]


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "get_parser_by_format",
    "list_formats",
    "get_extension",
]


# ===============================================================================
# Test
# ===============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Parser Factory v4.0 - Extreme Simplicity")
    print("=" * 60)
    print()
    
    # Show all formats
    print("Formats in EXTENSION_MAP:")
    for fmt in list_formats():
        ext = get_extension(fmt)
        print(f"  {fmt:8s} → {ext:8s} → parser_{fmt}.py")
    print()
    
    # Test parser loading
    print("Parser Loading Test:")
    test_formats = ["json", "txt", "any"]
    for fmt in test_formats:
        try:
            parser = get_parser_by_format(fmt)
            print(f"  ✓ {fmt:8s} → {parser.__name__}")
        except Exception as e:
            print(f"  ✗ {fmt:8s} → {e}")
    print()
    
    print("=" * 60)
    print("Architecture:")
    print("  EXTENSION_MAP (sys_const.yaml)")
    print("    ↓")
    print("  parser_factory.py")
    print("    ↓")
    print("  parser_{object}.py")
    print()
    print("Special case:")
    print("  parser_any.py → calls parser_txt.py")
    print("=" * 60)
