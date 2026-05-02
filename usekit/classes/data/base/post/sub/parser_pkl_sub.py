# Path: usekit.classes.data.base.post.parser.parser_pkl_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: PKL parser sub-module for keydata search functionality
# Philosophy: PKL stores Python objects (dict/list) → reuse JSON search logic
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, List
from pathlib import Path
import pickle

# Import JSON sub-module for dict/list navigation
from usekit.classes.data.base.post.parser.parser_json_sub import (
    _search_keydata_in_json,
    _has_keydata_value,
    _filter_json_list_by_keydata,
    _extract_keydata_values,
)


# ===============================================================================
# Keydata Search (Reuse JSON Logic)
# ===============================================================================

def _search_keydata_in_pkl(
    data: Any,
    keydata: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
) -> Any:
    """
    Search keydata in pickled Python object.
    
    Strategy:
        - If data is dict/list → use JSON search logic (keypath navigation)
        - If data is other type → convert to string and search
    
    Args:
        data: Unpickled Python object
        keydata: Keypath for dict/list (e.g., "user/email", "items[0]/id")
        search_value: Optional value to match
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        recursive: Search recursively in nested structures
        find_all: Return all matches (recursive mode)
    
    Returns:
        - Found value(s) or None
        - For recursive mode: list of values
    
    Examples:
        >>> # PKL contains dict
        >>> data = {"user": {"name": "Alice", "email": "alice@gmail.com"}}
        >>> result = _search_keydata_in_pkl(data, "user/email")
        "alice@gmail.com"
        
        >>> # PKL contains list
        >>> data = [{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]
        >>> result = _search_keydata_in_pkl(data, "name", search_value="A")
        {"id": 1, "name": "A"}
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Strategy 1: Dict/List → Use JSON search logic
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if isinstance(data, (dict, list)):
        return _search_keydata_in_json(
            data=data,
            keydata=keydata,
            search_value=search_value,
            case_sensitive=case_sensitive,
            regex=regex,
            recursive=recursive,
            find_all=find_all,
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Strategy 2: Other types → String search
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    data_str = str(data)
    
    if regex:
        import re
        pattern = re.compile(keydata, re.IGNORECASE if not case_sensitive else 0)
        if pattern.search(data_str):
            return data
    else:
        key = keydata if case_sensitive else keydata.lower()
        content = data_str if case_sensitive else data_str.lower()
        if key in content:
            return data
    
    return None


def _has_keydata_pkl(
    data: Any,
    keydata: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False,
) -> bool:
    """
    Fast check if keydata exists in pickled object.
    
    Args:
        data: Unpickled Python object
        keydata: Keypath or search string
        search_value: Optional value to match
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
    
    Returns:
        True if keydata exists, False otherwise
    
    Examples:
        >>> data = {"user": {"email": "test@gmail.com"}}
        >>> _has_keydata_pkl(data, "user/email")
        True
        
        >>> _has_keydata_pkl(data, "user/phone")
        False
    """
    
    # Dict/List → Use JSON logic
    if isinstance(data, (dict, list)):
        return _has_keydata_value(
            data=data,
            keydata=keydata,
            search_value=search_value,
            case_sensitive=case_sensitive,
            regex=regex,
        )
    
    # Other types → String search
    data_str = str(data)
    
    if regex:
        import re
        pattern = re.compile(keydata, re.IGNORECASE if not case_sensitive else 0)
        return bool(pattern.search(data_str))
    else:
        key = keydata if case_sensitive else keydata.lower()
        content = data_str if case_sensitive else data_str.lower()
        return key in content


def _filter_pkl_list(
    data: Any,
    keydata: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False,
) -> List[Any]:
    """
    Filter list items by keydata condition.
    
    Only works if pickled data is a list of dict-like objects.
    
    Args:
        data: Unpickled list
        keydata: Key to filter by
        search_value: Value to match
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
    
    Returns:
        Filtered list of items
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "email": "alice@gmail.com"},
        ...     {"name": "Bob", "email": "bob@yahoo.com"}
        ... ]
        >>> _filter_pkl_list(data, "email", search_value="gmail")
        [{"name": "Alice", "email": "alice@gmail.com"}]
    """
    
    if not isinstance(data, list):
        return []
    
    # Use JSON list filtering logic
    return _filter_json_list_by_keydata(
        data=data,
        keydata=keydata,
        search_value=search_value,
        case_sensitive=case_sensitive,
        regex=regex,
    )


def _extract_pkl_values(
    data: Any,
    keydata: str,
    recursive: bool = False,
) -> List[Any]:
    """
    Extract all values for a given keydata.
    
    Args:
        data: Unpickled Python object
        keydata: Keypath to extract
        recursive: Search recursively
    
    Returns:
        List of extracted values
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "age": 30},
        ...     {"name": "Bob", "age": 25}
        ... ]
        >>> _extract_pkl_values(data, "name")
        ["Alice", "Bob"]
    """
    
    if not isinstance(data, (dict, list)):
        return []
    
    # Use JSON extraction logic
    return _extract_keydata_values(
        data=data,
        keydata=keydata,
        recursive=recursive,
    )


# ===============================================================================
# Integration Helpers
# ===============================================================================

def _load_and_search(
    file_path: Union[str, Path],
    keydata: str,
    search_value: Any = None,
    keydata_exists: bool = False,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    **kwargs
) -> Any:
    """
    Load PKL file and search for keydata.
    
    This is the main integration point called from parser_pkl.load().
    
    Args:
        file_path: Path to PKL file
        keydata: Keypath or search string
        search_value: Optional value to match
        keydata_exists: Return bool instead of data
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        recursive: Search recursively
        find_all: Return all matches
        **kwargs: Additional pickle.load() options
    
    Returns:
        - bool: if keydata_exists=True
        - Any: found value(s)
        - None: if no match
    """
    
    # Load pickled data
    path = Path(file_path) if isinstance(file_path, str) else file_path
    
    with path.open("rb") as f:
        data = pickle.load(f)
    
    # Fast existence check
    if keydata_exists:
        return _has_keydata_pkl(
            data=data,
            keydata=keydata,
            search_value=search_value,
            case_sensitive=case_sensitive,
            regex=regex,
        )
    
    # Search and return value
    return _search_keydata_in_pkl(
        data=data,
        keydata=keydata,
        search_value=search_value,
        case_sensitive=case_sensitive,
        regex=regex,
        recursive=recursive,
        find_all=find_all,
    )


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "_search_keydata_in_pkl",
    "_has_keydata_pkl",
    "_filter_pkl_list",
    "_extract_pkl_values",
    "_load_and_search",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
