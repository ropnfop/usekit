# Path: usekit.classes.data.base.post.sub.parser_yaml_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for YAML parser - keydata search and filtering support
# Features:
#   - Keydata search: Find values by keypath
#   - Existence check: Fast keydata presence validation
#   - Value matching: Filter YAML by keydata conditions
#   - Integration: Works with helper_keypath for nested navigation
# Note: YAML and JSON share identical data structures (dict/list), so we reuse JSON sub logic
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, List, Dict

# Import all keydata helpers from JSON sub module
# YAML and JSON have identical data structures, so we can reuse the same logic
from usekit.classes.data.base.post.sub.parser_json_sub import (
    _search_keydata_in_json,
    _has_keydata_value,
    _match_value,
    _filter_json_list_by_keydata,
    _extract_keydata_values,
)


# ===============================================================================
# YAML-Specific Aliases (for clarity in code)
# ===============================================================================

def _search_keydata_in_yaml(
    data: Union[Dict, List],
    keydata: str,
    search_value: Any = None,
    keydata_exists: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    case_sensitive: bool = False,
    regex: bool = False
) -> Union[bool, Any, List[Any]]:
    """
    Search for keydata in YAML structure.
    
    This is an alias for _search_keydata_in_json since YAML and JSON
    share identical data structures (dict/list).
    
    Args:
        data: YAML data (dict or list)
        keydata: Key path to search (e.g., "user/email", "items[0]/id")
        search_value: Optional value to match against
        keydata_exists: Return True/False instead of values (performance)
        recursive: Search recursively through entire structure
        find_all: Return all matches (when recursive=True)
        case_sensitive: Case-sensitive value matching
        regex: Use regex for value matching
    
    Returns:
        - bool: if keydata_exists=True
        - Any: single value
        - List[Any]: if find_all=True
        - None: if not found
    
    Examples:
        >>> data = {"users": [{"name": "Alice", "email": "alice@gmail.com"}]}
        
        >>> # Check existence
        >>> _search_keydata_in_yaml(data, "users[0]/email", keydata_exists=True)
        True
        
        >>> # Get value
        >>> _search_keydata_in_yaml(data, "users[0]/email")
        "alice@gmail.com"
        
        >>> # Match value
        >>> _search_keydata_in_yaml(data, "users[0]/email", search_value="gmail")
        "alice@gmail.com"
        
        >>> # Recursive search
        >>> _search_keydata_in_yaml(data, "email", recursive=True)
        "alice@gmail.com"
    """
    return _search_keydata_in_json(
        data=data,
        keydata=keydata,
        search_value=search_value,
        keydata_exists=keydata_exists,
        recursive=recursive,
        find_all=find_all,
        case_sensitive=case_sensitive,
        regex=regex
    )


def _has_keydata_value_yaml(
    data: Union[Dict, List],
    keydata: str,
    search_value: Any,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False
) -> bool:
    """
    Check if keydata path exists and matches value in YAML.
    
    Alias for JSON version since structures are identical.
    
    Args:
        data: YAML data
        keydata: Key path
        search_value: Value to match
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        recursive: Search recursively
    
    Returns:
        True if keydata exists and value matches
    
    Examples:
        >>> data = {"config": {"debug": True, "version": "1.0"}}
        
        >>> _has_keydata_value_yaml(data, "config/debug", True)
        True
        
        >>> _has_keydata_value_yaml(data, "config/version", "1.0")
        True
    """
    return _has_keydata_value(
        data=data,
        keydata=keydata,
        search_value=search_value,
        case_sensitive=case_sensitive,
        regex=regex,
        recursive=recursive
    )


def _filter_yaml_list_by_keydata(
    data_list: List[Dict],
    keydata: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False
) -> List[Dict]:
    """
    Filter a list of YAML objects by keydata condition.
    
    Alias for JSON version since structures are identical.
    
    Args:
        data_list: List of YAML objects
        keydata: Key path to check in each object
        search_value: Value to match (None = existence check only)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
    
    Returns:
        Filtered list of objects that match condition
    
    Examples:
        >>> users = [
        ...     {"name": "Alice", "role": "admin"},
        ...     {"name": "Bob", "role": "user"},
        ...     {"name": "Charlie", "role": "admin"}
        ... ]
        
        >>> _filter_yaml_list_by_keydata(users, "role", "admin")
        [
            {"name": "Alice", "role": "admin"},
            {"name": "Charlie", "role": "admin"}
        ]
    """
    return _filter_json_list_by_keydata(
        data_list=data_list,
        keydata=keydata,
        search_value=search_value,
        case_sensitive=case_sensitive,
        regex=regex
    )


def _extract_keydata_values_yaml(
    data: Union[Dict, List, List[Dict]],
    keydata: str,
    recursive: bool = False,
    find_all: bool = True
) -> List[Any]:
    """
    Extract all values for a given keydata path in YAML.
    
    Alias for JSON version since structures are identical.
    
    Args:
        data: YAML data (single object, list, or nested structure)
        keydata: Key path to extract
        recursive: Search recursively
        find_all: Collect all occurrences
    
    Returns:
        List of extracted values
    
    Examples:
        >>> data = {
        ...     "servers": [
        ...         {"name": "web1", "port": 8080},
        ...         {"name": "web2", "port": 8081}
        ...     ]
        ... }
        
        >>> _extract_keydata_values_yaml(data, "port", recursive=True)
        [8080, 8081]
    """
    return _extract_keydata_values(
        data=data,
        keydata=keydata,
        recursive=recursive,
        find_all=find_all
    )


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    # YAML-specific names (aliases)
    "_search_keydata_in_yaml",
    "_has_keydata_value_yaml",
    "_filter_yaml_list_by_keydata",
    "_extract_keydata_values_yaml",
    
    # Re-export JSON helpers (same logic)
    "_search_keydata_in_json",
    "_has_keydata_value",
    "_match_value",
    "_filter_json_list_by_keydata",
    "_extract_keydata_values",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
