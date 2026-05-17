# Path: usekit.classes.data.base.post.sub.parser_csv_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for CSV parser - keydata search and filtering support
# Features:
#   - Column search: Extract values from specific columns
#   - Row filtering: Filter rows by column value conditions
#   - Value matching: Support substring, regex, case-sensitive matching
#   - Multi-condition: Filter by multiple column criteria
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, List, Dict, Union
import re


# ===============================================================================
# Column Operations
# ===============================================================================

def _extract_column(
    data: List[Dict],
    column_name: str,
    default: Any = None
) -> List[Any]:
    """
    Extract all values from a specific column.
    
    Args:
        data: List of dicts (CSV rows with headers)
        column_name: Name of column to extract
        default: Default value if column missing
    
    Returns:
        List of column values
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "age": 30},
        ...     {"name": "Bob", "age": 25}
        ... ]
        
        >>> _extract_column(data, "name")
        ["Alice", "Bob"]
        
        >>> _extract_column(data, "age")
        [30, 25]
    """
    return [row.get(column_name, default) for row in data]


def _has_column(
    data: List[Dict],
    column_name: str
) -> bool:
    """
    Check if column exists in CSV data.
    
    Args:
        data: List of dicts
        column_name: Column name to check
    
    Returns:
        True if column exists
    """
    if not data:
        return False
    return column_name in data[0]


# ===============================================================================
# Row Filtering
# ===============================================================================

def _filter_rows_by_column(
    data: List[Dict],
    column_name: str,
    search_value: Any = None,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False
) -> Union[bool, List[Dict]]:
    """
    Filter CSV rows by column value condition.
    
    Args:
        data: List of dicts (CSV rows)
        column_name: Column to check
        search_value: Value to match (None = existence check only)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        keydata_exists: Return True/False instead of rows
    
    Returns:
        - bool: if keydata_exists=True
        - List[Dict]: filtered rows
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "email": "alice@gmail.com"},
        ...     {"name": "Bob", "email": "bob@yahoo.com"},
        ...     {"name": "Charlie", "email": "charlie@gmail.com"}
        ... ]
        
        >>> # Filter rows with gmail
        >>> _filter_rows_by_column(data, "email", "gmail")
        [
            {"name": "Alice", "email": "alice@gmail.com"},
            {"name": "Charlie", "email": "charlie@gmail.com"}
        ]
        
        >>> # Check existence only
        >>> _filter_rows_by_column(data, "email", "gmail", keydata_exists=True)
        True
    """
    if not data:
        return False if keydata_exists else []
    
    # Check column exists
    if column_name not in data[0]:
        return False if keydata_exists else []
    
    # Existence check only (no value matching)
    if search_value is None:
        if keydata_exists:
            return any(column_name in row and row[column_name] for row in data)
        return data  # All rows have the column
    
    # Filter by value
    matched_rows = []
    for row in data:
        if column_name not in row:
            continue
        
        value = row[column_name]
        if _match_value(value, search_value, case_sensitive, regex):
            if keydata_exists:
                return True
            matched_rows.append(row)
    
    if keydata_exists:
        return False
    
    return matched_rows


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
# Multi-column Operations
# ===============================================================================

def _filter_rows_by_multiple_columns(
    data: List[Dict],
    filters: Dict[str, Any],
    match_all: bool = True,
    case_sensitive: bool = False,
    regex: bool = False
) -> List[Dict]:
    """
    Filter rows by multiple column conditions.
    
    Args:
        data: List of dicts
        filters: Dict of {column_name: search_value}
        match_all: If True, all conditions must match (AND logic)
                   If False, any condition matches (OR logic)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
    
    Returns:
        Filtered rows
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "age": 30, "city": "Seoul"},
        ...     {"name": "Bob", "age": 25, "city": "Busan"},
        ...     {"name": "Charlie", "age": 30, "city": "Seoul"}
        ... ]
        
        >>> # AND logic: age=30 AND city=Seoul
        >>> _filter_rows_by_multiple_columns(
        ...     data,
        ...     {"age": 30, "city": "Seoul"},
        ...     match_all=True
        ... )
        [
            {"name": "Alice", "age": 30, "city": "Seoul"},
            {"name": "Charlie", "age": 30, "city": "Seoul"}
        ]
        
        >>> # OR logic: age=30 OR city=Busan
        >>> _filter_rows_by_multiple_columns(
        ...     data,
        ...     {"age": 30, "city": "Busan"},
        ...     match_all=False
        ... )
        # Returns Alice, Bob, Charlie (all match at least one condition)
    """
    if not data or not filters:
        return data
    
    matched_rows = []
    for row in data:
        if match_all:
            # AND logic - all conditions must match
            if all(
                column in row and _match_value(row[column], value, case_sensitive, regex)
                for column, value in filters.items()
            ):
                matched_rows.append(row)
        else:
            # OR logic - any condition matches
            if any(
                column in row and _match_value(row[column], value, case_sensitive, regex)
                for column, value in filters.items()
            ):
                matched_rows.append(row)
    
    return matched_rows


# ===============================================================================
# Search Operations
# ===============================================================================

def _search_in_csv(
    data: List[Dict],
    keydata: str,
    search_value: Any = None,
    key_type: Optional[str] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False
) -> Union[bool, List[Any], List[Dict]]:
    """
    Generic search in CSV data.
    
    Args:
        data: List of dicts (CSV with headers)
        keydata: Column name to search
        search_value: Value to match (optional)
        key_type: Search type
            - "column": Extract column values
            - "row": Filter rows by condition
            - None: Auto-detect (default to row filtering)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        keydata_exists: Return True/False only
    
    Returns:
        - bool: if keydata_exists=True
        - List[Any]: if key_type="column"
        - List[Dict]: if key_type="row" or None
    
    Examples:
        >>> data = [
        ...     {"name": "Alice", "email": "alice@gmail.com", "age": 30},
        ...     {"name": "Bob", "email": "bob@yahoo.com", "age": 25}
        ... ]
        
        >>> # Extract column
        >>> _search_in_csv(data, "name", key_type="column")
        ["Alice", "Bob"]
        
        >>> # Filter rows
        >>> _search_in_csv(data, "email", search_value="gmail", key_type="row")
        [{"name": "Alice", "email": "alice@gmail.com", "age": 30}]
        
        >>> # Existence check
        >>> _search_in_csv(data, "email", search_value="gmail", keydata_exists=True)
        True
    """
    if not data:
        return False if keydata_exists else []
    
    # Auto-detect key_type
    if key_type is None:
        if search_value is None:
            key_type = "column"  # Extract column values
        else:
            key_type = "row"  # Filter rows
    
    # Column extraction
    if key_type == "column":
        if keydata_exists:
            return _has_column(data, keydata)
        
        values = _extract_column(data, keydata)
        
        # Filter by search_value if provided
        if search_value is not None:
            values = [
                v for v in values
                if _match_value(v, search_value, case_sensitive, regex)
            ]
        
        return values
    
    # Row filtering
    elif key_type == "row":
        return _filter_rows_by_column(
            data,
            column_name=keydata,
            search_value=search_value,
            case_sensitive=case_sensitive,
            regex=regex,
            keydata_exists=keydata_exists
        )
    
    else:
        raise ValueError(f"Invalid key_type: {key_type}. Use 'column', 'row', or None")


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "_extract_column",
    "_has_column",
    "_filter_rows_by_column",
    "_match_value",
    "_filter_rows_by_multiple_columns",
    "_search_in_csv",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
