# Path: usekit.infra.params_alias.py
# -----------------------------------------------------------------------------------------------
#  Parameter Alias System - Core definitions for short names
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0
#  
#  Core principle: "4+ chars = alias available, 3 or less = original only"
# -----------------------------------------------------------------------------------------------

# ===============================================================================
# Alias mapping (original → short)
# ===============================================================================

ALIAS_MAP = {
    # Data related
    "data": "dt",
    "name": "nm",
    "keydata": "kd",
    "default": "df",
    
    # Path related
    "path": "pt",
    "dir_path": "dp",
    "pattern": "pn",
    "set_path": "sp",
    "get_path": "gp",
    
    # Operation flags
    "recursive": "rc",
    "find_all": "fa",
    "create_missing": "cm",
    "walk": "wk",
    
    # Output control
    "tail_all": "ta",
    "tail_top": "tt",
    "tail_mid": "tm",
    "tail_bottom": "tb",
    
    # System
    "debug": "dbg",
    
    # Exec / function related
    "func": "fn", 
    
    # Parameter
    "params": "p",
    "params_all": "pa",   
    
    # No alias (3 chars or less)
    # fmt, loc, act, mod, cus, op, cp
}

# Reverse mapping (short → original)
REVERSE_ALIAS = {v: k for k, v in ALIAS_MAP.items()}

# ===============================================================================
# Core helper functions
# ===============================================================================

def get_alias(param: str) -> str:
    """
    Get short alias for parameter name
    
    Parameters
    ----------
    param : str
        Parameter name
        
    Returns
    -------
    str
        Alias if exists, otherwise original name
        
    Examples
    --------
    >>> get_alias("keydata")
    'kd'
    >>> get_alias("fmt")
    'fmt'
    """
    return ALIAS_MAP.get(param, param)

def get_fullname(alias: str) -> str:
    """
    Get original parameter name from alias
    
    Parameters
    ----------
    alias : str
        Short alias
        
    Returns
    -------
    str
        Original parameter name if exists, otherwise returns alias
        
    Examples
    --------
    >>> get_fullname("kd")
    'keydata'
    >>> get_fullname("fmt")
    'fmt'
    """
    return REVERSE_ALIAS.get(alias, alias)

def normalize_params(**kwargs) -> dict:
    """
    Convert all aliases to full parameter names
    
    Parameters
    ----------
    **kwargs
        Mixed original and alias parameters
        
    Returns
    -------
    dict
        Dictionary with all parameters in original form
        
    Examples
    --------
    >>> normalize_params(nm="config", kd="user", fmt="json")
    {'name': 'config', 'keydata': 'user', 'fmt': 'json'}
    """
    result = {}
    for key, value in kwargs.items():
        full_key = get_fullname(key)
        result[full_key] = value
    return result

def get_all_aliases() -> dict:
    """
    Get complete alias mapping
    
    Returns
    -------
    dict
        Dictionary of all original → alias mappings
    """
    return ALIAS_MAP.copy()

def get_all_originals() -> dict:
    """
    Get complete reverse mapping
    
    Returns
    -------
    dict
        Dictionary of all alias → original mappings
    """
    return REVERSE_ALIAS.copy()

def has_alias(param: str) -> bool:
    """
    Check if parameter has an alias
    
    Parameters
    ----------
    param : str
        Parameter name
        
    Returns
    -------
    bool
        True if alias exists
        
    Examples
    --------
    >>> has_alias("keydata")
    True
    >>> has_alias("fmt")
    False
    """
    return param in ALIAS_MAP

def is_alias(text: str) -> bool:
    """
    Check if text is a known alias
    
    Parameters
    ----------
    text : str
        Text to check
        
    Returns
    -------
    bool
        True if it's a known alias
        
    Examples
    --------
    >>> is_alias("kd")
    True
    >>> is_alias("keydata")
    False
    """
    return text in REVERSE_ALIAS

# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    # Mapping dictionaries
    "ALIAS_MAP",
    "REVERSE_ALIAS",
    
    # Core functions
    "get_alias",
    "get_fullname",
    "normalize_params",
    
    # Query functions
    "get_all_aliases",
    "get_all_originals",
    "has_alias",
    "is_alias",
]
