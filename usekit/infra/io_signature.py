# Path: usekit.infra.io_signature.py
# -----------------------------------------------------------------------------------------------
#  Universal I/O Signature - Core definitions for all data I/O operations
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0 - TXT Parser advanced features
#  Three-layer structure for future expansion
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, Literal
import warnings

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "cus", "cache"], str]

# ===============================================================================
# Layer 1: USER LAYER - Semantic inputs
# ===============================================================================

USER_LAYER = {
    "data": None,
    "name": None,
    "mod": "all",
    "dir_path": None,
    "cus": None,
    "keydata": None,
}

# ===============================================================================
# Layer 2: TARGETING LAYER - Paths & Filters (Extended)
# ===============================================================================

TARGETING_LAYER = {
    # Basic targeting (all formats)
    "default": None,
    "recursive": False,
    "find_all": False,
    "create_missing": True,
    "walk": False,
    
    # TXT-specific: Search & Replace
    "regex": False,
    "case_sensitive": False,
    "invert_match": False,
    
    # TXT-specific: Tail modes (head/tail functionality)
    "tail_all": None,
    "tail_top": None,
    "tail_mid": None,
    "tail_bottom": None,
    
    # TXT-specific: Line operations
    "lines": False,
    "line_numbers": False,
    "strip": False,
    "strip_empty": False,
    
    # TXT-specific: Write & Replace options
    "append": False,
    "append_newline": True,
    "replace_all": True,
    "max_count": None,
    
    # [Future] Reserved for expansion
    "k": None,
    "kv": None,
    "kc": "eq",
    "kf": None,
}

# ===============================================================================
# Layer 3: SYSTEM LAYER - Execution control (Extended)
# ===============================================================================

SYSTEM_LAYER = {
    # Core system params
    "fmt": "json",
    "loc": "base",
    "mode": "read",
    "mode_sub": None,
    "path": None,
    "debug": False,
    
    # TXT-specific: Encoding & Safety
    "encoding": "utf-8",
    "newline": None,
    "wrap": True,
    "overwrite": True,
    "safe": True,
    
    # Emit-specific: Output type
    "type": "s",
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

def get_io_params(**kwargs) -> dict:
    """
    Extract common parameters for all I/O operations
    Merge user input with defaults
    
    Examples:
        >>> p = get_io_params(name="config", mode="read")
        >>> p["fmt"]  # "json" (default)
        >>> p["name"]  # "config" (user input)
        
        >>> # TXT-specific
        >>> p = get_io_params(fmt="txt", tail_bottom=100)
        >>> p["tail_bottom"]  # 100
        >>> p["encoding"]     # "utf-8" (default)
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

def params_for_read(**kwargs) -> dict:
    """Read operation parameters"""
    return get_io_params(mode="read", **kwargs)

def params_for_write(**kwargs) -> dict:
    """Write operation parameters"""
    return get_io_params(mode="write", **kwargs)

def params_for_emit(**kwargs) -> dict:
    """Emit operation parameters (memory-only serialization)"""
    return get_io_params(mode="emit", **kwargs)

def params_for_update(**kwargs) -> dict:
    """Update operation parameters"""
    return get_io_params(mode="update", **kwargs)

def params_for_delete(**kwargs) -> dict:
    """Delete operation parameters"""
    return get_io_params(mode="delete", **kwargs)

def params_for_has(**kwargs) -> dict:
    """Has operation parameters (existence check)"""
    return get_io_params(mode="has", **kwargs)

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
    
    # Layer definitions
    "USER_LAYER",
    "TARGETING_LAYER",
    "SYSTEM_LAYER",
    "ALL_DEFAULTS",
    
    # Parameter extractors
    "get_io_params",
    "get_user_layer",
    "get_targeting_layer",
    "get_system_layer",
    
    # Operation helpers
    "params_for_read",
    "params_for_write",
    "params_for_emit",
    "params_for_update",
    "params_for_delete",
    "params_for_has",
    
    # Future features
    "has_future_features",
    "warn_future_features",
]