# Path: usekit.classes.navi.base.load.sub.nbl_common_sub.py
# -----------------------------------------------------------------------------------------------
#  Common Sub-functions - Shared utilities for navi operations
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0
# -----------------------------------------------------------------------------------------------

from typing import List
from usekit.classes.common.utils.helper_const import get_const


# ===============================================================================
# Pattern Detection
# ===============================================================================

def has_pattern(name: str) -> bool:
    """
    Check if name contains pattern characters.
    
    Pattern characters: *, ?, %, [, ]
    
    Args:
        name: Filename or pattern string
        
    Returns:
        True if name contains pattern characters
        
    Examples:
        >>> has_pattern("config.json")
        False
        >>> has_pattern("*.json")
        True
        >>> has_pattern("user_??.txt")
        True
        >>> has_pattern("%test%")
        True
    """
    if not name or not isinstance(name, str):
        return False
    
    pattern_chars = ["*", "?", "%", "[", "]"]
    return any(ch in name for ch in pattern_chars)


# ===============================================================================
# Format Resolution
# ===============================================================================

def resolve_formats(fmt: str, mod: str = None) -> List[str]:
    """
    Resolve format list from fmt/mod combination.
    
    Logic:
    - fmt != "any"              → [fmt]
    - fmt == "any", mod in (None, "all") → ALL registered formats
    - fmt == "any", mod=<value> → [mod]
    
    Args:
        fmt: Format type (json/yaml/txt/csv/any)
        mod: Modifier for fmt="any" (default: None)
        
    Returns:
        List of format strings
        
    Raises:
        ValueError: If mod is not in EXTENSION_MAP
        
    Examples:
        >>> resolve_formats("json")
        ['json']
        
        >>> resolve_formats("any")
        ['json', 'yaml', 'txt', 'csv', ...]
        
        >>> resolve_formats("any", mod="json")
        ['json']
        
        >>> resolve_formats("any", mod="invalid")
        ValueError: Unsupported mod 'invalid'
    """
    if fmt != "any":
        return [fmt]
    
    # Get all registered formats from EXTENSION_MAP
    ext_map = get_const("EXTENSION_MAP")
    
    # All formats
    if mod is None or mod == "all":
        return list(ext_map.keys())
    
    # Specific format
    if mod not in ext_map:
        raise ValueError(
            f"Unsupported mod '{mod}' (not in EXTENSION_MAP). "
            f"Available: {', '.join(ext_map.keys())}"
        )
    
    return [mod]


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "has_pattern",
    "resolve_formats",
]
