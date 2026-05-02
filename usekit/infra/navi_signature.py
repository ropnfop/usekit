# Path: usekit.infra.navi_signature.py
# -----------------------------------------------------------------------------------------------
#  Universal Navigation Signature - Core definitions for all navigation operations
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0 - path/find operation fully integrated
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, Literal, List
import warnings

# ===============================================================================
# Type Definitions
# ===============================================================================

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "cus", "cache"], str]
Op = Union[Literal["cache", "path"], str]
FilterType = Literal["both", "files", "dirs"]
SortBy = Literal["name", "size", "mtime", "ext"]
SearchMode = Literal["value", "key", "path"]

# ===============================================================================
# Layer 1: USER LAYER - Semantic inputs
# ===============================================================================

USER_LAYER = {
    "data": None,
    "name": None,
    "mod": "all",
    "loc": "base",
    "cus": None,
    "dir_path": None,
}

# ===============================================================================
# Layer 2: TARGETING LAYER - Paths & Filters (Extended)
# ===============================================================================

TARGETING_LAYER = {
    # Basic targeting
    "keydata": None,
    "default": None,
    "recursive": False,
    "find_all": False,
    "create_missing": True,
    "walk": False,
    "pattern": None,
    
    # Navigation specific
    "op": "cache",
    "cp": None,
    
    # Path operation - Filter
    "filter_type": "both",
    "min_size": None,
    "max_size": None,
    "ext_filter": None,
    
    # Path operation - Sort
    "sort_by": None,
    "reverse": False,
    
    # Path operation - Output
    "stat": False,
    "mk": False,
    
    # Find operation - Search
    "regex": False,
    "case_sensitive": False,
    "search_mode": "value",
    "column": None,
    
    # TXT operation - Tail
    "tail_all": None,
    "tail_top": None,
    "tail_mid": None,
    "tail_bottom": None,
    
    # Future expansion
    "k": None,
    "kv": None,
    "kc": "eq",
    "kf": None,
}

# ===============================================================================
# Layer 3: SYSTEM LAYER - Execution control
# ===============================================================================

SYSTEM_LAYER = {
    "fmt": "json",
    "act": "path",
    "mode": "get",
    "mode_sub": None,
    "path": None,
    "set_path": None,
    "get_path": None,
    "debug": False,
}

# ===============================================================================
# Unified defaults
# ===============================================================================

ALL_DEFAULTS = {
    **USER_LAYER,
    **TARGETING_LAYER,
    **SYSTEM_LAYER,
}

# ===============================================================================
# Parameter extraction helpers
# ===============================================================================

def get_navi_params(**kwargs) -> dict:
    """
    Extract common parameters for all navigation operations
    Merge user input with defaults
    
    Returns:
        Complete parameter dict with all defaults
    
    Examples:
        >>> p = get_navi_params(name="config", filter_type="files")
        >>> p["fmt"]         # "json" (default)
        >>> p["filter_type"] # "files" (user input)
        >>> p["stat"]        # False (default)
    """
    return {**ALL_DEFAULTS, **kwargs}

def get_user_layer(params: dict) -> dict:
    """Extract USER LAYER parameters only"""
    return {k: params.get(k, USER_LAYER[k]) for k in USER_LAYER.keys()}

def get_targeting_layer(params: dict) -> dict:
    """Extract TARGETING LAYER parameters only"""
    return {k: params.get(k, TARGETING_LAYER[k]) for k in TARGETING_LAYER.keys()}

def get_system_layer(params: dict) -> dict:
    """Extract SYSTEM LAYER parameters only"""
    return {k: params.get(k, SYSTEM_LAYER[k]) for k in SYSTEM_LAYER.keys()}

# ===============================================================================
# Convenience functions: operation-specific parameter extraction
# ===============================================================================

def params_for_get(**kwargs) -> dict:
    """
    Get operation parameters
    
    Examples:
        >>> p = params_for_get(name="config", op="cache")
        >>> p["mode"]  # "get"
    """
    return get_navi_params(mode="get", **kwargs)

def params_for_set(**kwargs) -> dict:
    """
    Set operation parameters
    
    Examples:
        >>> p = params_for_set(data={"key": "value"}, name="config")
        >>> p["mode"]  # "set"
    """
    return get_navi_params(mode="set", **kwargs)

def params_for_path(**kwargs) -> dict:
    """
    Path operation parameters
    
    Examples:
        >>> p = params_for_path(name="*.json", filter_type="files")
        >>> p["mode"]  # "path"
    """
    return get_navi_params(mode="path", **kwargs)

def params_for_find(**kwargs) -> dict:
    """
    Find operation parameters
    
    Examples:
        >>> p = params_for_find(name="config.json", keydata="email")
        >>> p["mode"]  # "find"
    """
    return get_navi_params(mode="find", **kwargs)

def params_for_list(**kwargs) -> dict:
    """
    List operation parameters
    
    Examples:
        >>> p = params_for_list(name="configs", walk=True)
        >>> p["mode"]  # "list"
    """
    return get_navi_params(mode="list", **kwargs)

# ===============================================================================
# Operation validation
# ===============================================================================

VALID_OPS = {"cache", "path"}

def validate_op(op: str) -> bool:
    """
    Validate if operation type is supported
    
    Args:
        op: Operation type to validate
        
    Returns:
        True if valid, False otherwise
        
    Examples:
        >>> validate_op("cache")
        True
        >>> validate_op("invalid")
        False
    """
    return op in VALID_OPS

def get_valid_ops() -> set:
    """
    Get set of valid operation types
    
    Returns:
        Set of valid operation names
        
    Examples:
        >>> ops = get_valid_ops()
        >>> "cache" in ops
        True
    """
    return VALID_OPS.copy()

# ===============================================================================
# Future features detection
# ===============================================================================

def has_future_features(params: dict) -> bool:
    """
    Check if any future/reserved parameters are being used
    
    Returns:
        True if any of k, kv, kc, kf are not at default values
    """
    return (
        params.get("k") is not None or
        params.get("kv") is not None or
        params.get("kc") != "eq" or
        params.get("kf") is not None
    )

def warn_future_features(params: dict):
    """
    Warn if future features are being used
    """
    if has_future_features(params):
        warnings.warn(
            "Future features (k, kv, kc, kf) are not yet implemented. "
            "These parameters will be ignored in the current version.",
            FutureWarning,
            stacklevel=2
        )

# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    # Types
    "Loc",
    "Op",
    "FilterType",
    "SortBy",
    "SearchMode",
    
    # Layer definitions
    "USER_LAYER",
    "TARGETING_LAYER",
    "SYSTEM_LAYER",
    "ALL_DEFAULTS",
    
    # Parameter extractors
    "get_navi_params",
    "get_user_layer",
    "get_targeting_layer",
    "get_system_layer",
    
    # Operation helpers
    "params_for_get",
    "params_for_set",
    "params_for_path",
    "params_for_find",
    "params_for_list",
    
    # Validation
    "validate_op",
    "get_valid_ops",
    "VALID_OPS",
    
    # Future features
    "has_future_features",
    "warn_future_features",
]
