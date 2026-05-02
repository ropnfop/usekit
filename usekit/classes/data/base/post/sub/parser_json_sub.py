# Path: usekit.classes.data.base.post.sub.parser_json_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for JSON parser - keydata search and filtering support
# Features:
#   - Keydata search: Find values by keypath
#   - Existence check: Fast keydata presence validation
#   - Value matching: Filter JSON by keydata conditions
#   - Integration: Works with helper_keypath for nested navigation
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, List, Dict
import re


# ===============================================================================
# Keydata Search Operations
# ===============================================================================

def _search_keydata_in_json(
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
    Search for keydata in JSON structure.
    
    This function integrates with helper_keypath for navigation
    and adds value matching capabilities.
    
    Args:
        data: JSON data (dict or list)
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
        >>> _search_keydata_in_json(data, "users[0]/email", keydata_exists=True)
        True
        
        >>> # Get value
        >>> _search_keydata_in_json(data, "users[0]/email")
        "alice@gmail.com"
        
        >>> # Match value
        >>> _search_keydata_in_json(data, "users[0]/email", search_value="gmail")
        "alice@gmail.com"
        
        >>> # Recursive search
        >>> _search_keydata_in_json(data, "email", recursive=True)
        "alice@gmail.com"
    """
    from usekit.classes.common.utils.helper_keypath import resolve_key_path, has_key_path
    
    # Fast existence check
    if keydata_exists:
        exists = has_key_path(data, keydata, recursive=recursive)
        if not exists or search_value is None:
            return exists
        
        # Need to check value too
        value = resolve_key_path(data, keydata, recursive=recursive, find_all=find_all)
        if value is None:
            return False
        
        if find_all and isinstance(value, list):
            # Check if any value matches
            return any(_match_value(v, search_value, case_sensitive, regex) for v in value)
        else:
            return _match_value(value, search_value, case_sensitive, regex)
    
    # Get value(s)
    value = resolve_key_path(data, keydata, recursive=recursive, find_all=find_all)
    
    if value is None:
        return None
    
    # Filter by search_value if provided
    if search_value is not None:
        if find_all and isinstance(value, list):
            matched = [v for v in value if _match_value(v, search_value, case_sensitive, regex)]
            return matched if matched else None
        else:
            if _match_value(value, search_value, case_sensitive, regex):
                return value
            else:
                return None
    
    return value


def _has_keydata_value(
    data: Union[Dict, List],
    keydata: str,
    search_value: Any,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False
) -> bool:
    """
    Check if keydata path exists and matches value.
    
    Optimized for boolean checks without retrieving actual values.
    
    Args:
        data: JSON data
        keydata: Key path
        search_value: Value to match
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        recursive: Search recursively
    
    Returns:
        True if keydata exists and value matches
    
    Examples:
        >>> data = {"config": {"debug": True, "version": "1.0"}}
        
        >>> _has_keydata_value(data, "config/debug", True)
        True
        
        >>> _has_keydata_value(data, "config/version", "1.0")
        True
        
        >>> _has_keydata_value(data, "config/version", "2.0")
        False
    """
    return _search_keydata_in_json(
        data,
        keydata,
        search_value=search_value,
        keydata_exists=True,
        case_sensitive=case_sensitive,
        regex=regex,
        recursive=recursive
    )


# ===============================================================================
# Value Matching Helper
# ===============================================================================

def _match_value(
    value: Any,
    search_value: Any,
    case_sensitive: bool = False,
    regex: bool = False
) -> bool:
    """
    Match value against search criteria.
    
    Supports:
    - Exact match: value == search_value
    - Substring match: search_value in value (for strings)
    - Regex match: pattern matching
    - Case-insensitive: optional
    
    Args:
        value: Actual value to check
        search_value: Expected value/pattern
        case_sensitive: Case-sensitive matching
        regex: Use regex pattern matching
    
    Returns:
        True if value matches criteria
    
    Examples:
        >>> _match_value("alice@gmail.com", "gmail")
        True
        
        >>> _match_value("alice@gmail.com", "^alice", regex=True)
        True
        
        >>> _match_value("Test", "test", case_sensitive=False)
        True
    """
    # Handle None
    if value is None:
        return search_value is None
    
    # Exact type match for non-strings
    if not isinstance(value, str) or not isinstance(search_value, str):
        return value == search_value
    
    # String matching
    if regex:
        # Regex pattern matching
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(str(search_value), flags)
            return bool(pattern.search(str(value)))
        except re.error:
            # Invalid regex, fall back to substring
            pass
    
    # Substring matching
    value_str = str(value)
    search_str = str(search_value)
    
    if case_sensitive:
        return search_str in value_str
    else:
        return search_str.lower() in value_str.lower()


# ===============================================================================
# Batch Operations
# ===============================================================================

def _filter_json_list_by_keydata(
    data_list: List[Dict],
    keydata: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False
) -> List[Dict]:
    """
    Filter a list of JSON objects by keydata condition.
    
    Useful for filtering arrays of objects where each object
    needs to match a specific keydata condition.
    
    Args:
        data_list: List of JSON objects
        keydata: Key path to check in each object
        search_value: Value to match (None = existence check only)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
    
    Returns:
        Filtered list of objects that match condition
    
    Examples:
        >>> users = [
        ...     {"name": "Alice", "email": "alice@gmail.com"},
        ...     {"name": "Bob", "email": "bob@yahoo.com"},
        ...     {"name": "Charlie", "email": "charlie@gmail.com"}
        ... ]
        
        >>> _filter_json_list_by_keydata(users, "email", "gmail")
        [
            {"name": "Alice", "email": "alice@gmail.com"},
            {"name": "Charlie", "email": "charlie@gmail.com"}
        ]
    """
    if not isinstance(data_list, list):
        return []
    
    result = []
    for item in data_list:
        if not isinstance(item, dict):
            continue
        
        if search_value is None:
            # Existence check only
            from usekit.classes.common.utils.helper_keypath import has_key_path
            if has_key_path(item, keydata):
                result.append(item)
        else:
            # Value matching
            if _has_keydata_value(item, keydata, search_value, case_sensitive, regex):
                result.append(item)
    
    return result


def _extract_keydata_values(
    data: Union[Dict, List, List[Dict]],
    keydata: str,
    recursive: bool = False,
    find_all: bool = True
) -> List[Any]:
    """
    Extract all values for a given keydata path.
    
    Useful for collecting specific field values across
    nested structures or arrays.
    
    Args:
        data: JSON data (single object, list, or nested structure)
        keydata: Key path to extract
        recursive: Search recursively
        find_all: Collect all occurrences
    
    Returns:
        List of extracted values
    
    Examples:
        >>> data = {
        ...     "users": [
        ...         {"name": "Alice", "age": 30},
        ...         {"name": "Bob", "age": 25}
        ...     ]
        ... }
        
        >>> _extract_keydata_values(data, "users", recursive=True)
        [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        
        >>> # Extract nested values
        >>> _extract_keydata_values(data, "name", recursive=True, find_all=True)
        ["Alice", "Bob"]
    """
    from usekit.classes.common.utils.helper_keypath import resolve_key_path
    
    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        # List of dicts - extract from each
        values = []
        for item in data:
            value = resolve_key_path(item, keydata, recursive=recursive, find_all=find_all)
            if value is not None:
                if isinstance(value, list):
                    values.extend(value)
                else:
                    values.append(value)
        return values
    else:
        # Single object or nested structure
        value = resolve_key_path(data, keydata, recursive=recursive, find_all=find_all)
        if value is None:
            return []
        if isinstance(value, list):
            return value
        return [value]


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "_search_keydata_in_json",
    "_has_keydata_value",
    "_match_value",
    "_filter_json_list_by_keydata",
    "_extract_keydata_values",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
