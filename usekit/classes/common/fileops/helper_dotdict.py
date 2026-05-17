# Path: usekit.classes.common.fileops.helper_dotdict.py
# -----------------------------------------------------------------------------------
#  DotDict - Dictionary with dot notation access
#
#  Core Features
#  -------------
#  1. Dual access modes:
#     - Dot notation: obj.key
#     - Dict notation: obj["key"]
#
#  2. Full dict compatibility:
#     - Inherits from dict
#     - JSON serializable
#     - All dict methods (.get(), .items(), .keys(), etc.)
#
#  3. Use cases:
#     - SQL query results
#     - JSON API responses
#     - Configuration objects
#     - Any dict that benefits from attribute access
#
#  Design Philosophy
#  -----------------
#  Combines the convenience of dot notation with the flexibility of dict access.
#  Users can choose the style that fits their context:
#  - Static fields: obj.user_key (cleaner, IDE-friendly)
#  - Dynamic fields: obj[field_name] (loops, variables)
#
#  Safety Features
#  ---------------
#  - Prevents conflicts with dict methods (keys, items, get, etc.)
#  - Clear error messages for missing attributes
#  - Immutable behavior optional (can be extended)
#
#  Designed by: Little Prince × ROP × USEKIT
# -----------------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, Iterator


# Reserved names that cannot be accessed via dot notation
# (conflicts with dict built-in methods)
DICT_RESERVED = frozenset({
    'clear', 'copy', 'fromkeys', 'get', 'items', 'keys', 
    'pop', 'popitem', 'setdefault', 'update', 'values'
})


class DotDict(dict):
    """
    Dictionary with dot notation access.
    
    Supports both attribute-style and dict-style access:
    - obj.key
    - obj["key"]
    
    Examples
    --------
    Basic usage:
    >>> row = DotDict({"user_key": "aaa", "age": 25})
    >>> row.user_key
    'aaa'
    >>> row["user_key"]
    'aaa'
    
    Dict methods still work:
    >>> row.get("user_key", "default")
    'aaa'
    >>> list(row.keys())
    ['user_key', 'age']
    
    Dynamic access:
    >>> field = "age"
    >>> row[field]
    25
    
    List comprehension:
    >>> rows = [DotDict({"id": i, "value": i*10}) for i in range(3)]
    >>> [r.value for r in rows]
    [0, 10, 20]
    
    SQL query results:
    >>> raw = exec_sql("SELECT * FROM users WHERE id = :id", id=1)
    >>> raw[0].user_key  # Clean!
    >>> raw[0]["user_key"]  # Also works!
    
    Notes
    -----
    - Field names that are Python keywords (e.g., 'class', 'for') 
      must use dict notation: obj["class"]
    - Field names that conflict with dict methods (e.g., 'keys', 'items')
      must use dict notation: obj["keys"]
    - Whitespace/special chars in field names require dict notation
    """
    
    def __getattr__(self, key: str) -> Any:
        """
        Enable dot notation access: obj.key
        
        Parameters
        ----------
        key : str
            Attribute name to access
            
        Returns
        -------
        Any
            Value associated with the key
            
        Raises
        ------
        AttributeError
            If key doesn't exist or conflicts with dict methods
            
        Examples
        --------
        >>> d = DotDict({"user_key": "aaa"})
        >>> d.user_key
        'aaa'
        """
        # Prevent accessing dict methods via dot notation
        # This avoids confusion like: obj.keys vs obj["keys"]
        if key in DICT_RESERVED:
            raise AttributeError(
                f"Cannot access '{key}' via dot notation "
                f"(conflicts with dict method). "
                f"Use dict notation: obj['{key}']"
            )
        
        # Normal attribute access
        try:
            return self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )
    
    def __setattr__(self, key: str, value: Any) -> None:
        """
        Enable dot notation assignment: obj.key = value
        
        Parameters
        ----------
        key : str
            Attribute name to set
        value : Any
            Value to assign
            
        Examples
        --------
        >>> d = DotDict()
        >>> d.user_key = "aaa"
        >>> d.user_key
        'aaa'
        
        Notes
        -----
        Internal attributes (starting with '_') are handled separately
        to avoid interfering with dict's internal state.
        """
        # Handle internal attributes (e.g., __dict__, _internal_state)
        if key.startswith("_"):
            object.__setattr__(self, key, value)
            return
        
        if key in DICT_RESERVED:
            raise AttributeError(
                f"Cannot set '{key}' via dot notation "
                f"(conflicts with dict method). "
                f"Use dict notation: obj['{key}'] = value"
            )
        self[key] = value
    
    def __delattr__(self, key: str) -> None:
        """
        Enable dot notation deletion: del obj.key
        
        Parameters
        ----------
        key : str
            Attribute name to delete
            
        Raises
        ------
        AttributeError
            If key doesn't exist or conflicts with dict methods
            
        Examples
        --------
        >>> d = DotDict({"user_key": "aaa"})
        >>> del d.user_key
        >>> "user_key" in d
        False
        
        Notes
        -----
        Internal attributes (starting with '_') are handled separately
        to avoid interfering with dict's internal state.
        """
        # Handle internal attributes
        if key.startswith("_"):
            object.__delattr__(self, key)
            return
        
        if key in DICT_RESERVED:
            raise AttributeError(
                f"Cannot delete '{key}' via dot notation "
                f"(conflicts with dict method). "
                f"Use dict notation: del obj['{key}']"
            )
        try:
            del self[key]
        except KeyError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{key}'"
            )
    
    def __repr__(self) -> str:
        """
        Pretty print for debugging.
        
        Returns
        -------
        str
            String representation
            
        Examples
        --------
        >>> d = DotDict({"user_key": "aaa", "age": 25})
        >>> d
        DotDict({'user_key': 'aaa', 'age': 25})
        """
        return f"{type(self).__name__}({dict.__repr__(self)})"
    
    def __dir__(self) -> list[str]:
        """
        Enable IDE autocomplete for both dict methods and keys.
        
        Returns
        -------
        list[str]
            List of available attributes
            
        Examples
        --------
        >>> d = DotDict({"user_key": "aaa", "age": 25})
        >>> "user_key" in dir(d)
        True
        >>> "keys" in dir(d)  # dict method
        True
        """
        # Combine dict methods with actual keys
        dict_methods = dir(dict)
        keys = [k for k in self.keys() if isinstance(k, str)]
        return sorted(set(dict_methods + keys))
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get value with optional default (dict.get() override for clarity).
        
        This is technically redundant since DotDict inherits from dict,
        but explicitly defined here for documentation and IDE support.
        
        Parameters
        ----------
        key : str
            Key to retrieve
        default : Any, optional
            Default value if key doesn't exist (default: None)
            
        Returns
        -------
        Any
            Value associated with key, or default if not found
            
        Examples
        --------
        >>> d = DotDict({"user_key": "aaa"})
        >>> d.get("user_key")
        'aaa'
        >>> d.get("missing", "default")
        'default'
        >>> d.get("missing")  # Returns None
        """
        return super().get(key, default)


def dotdict_from_rows(columns: list[str], rows: list[tuple]) -> list[DotDict]:
    """
    Convert SQL cursor results to list of DotDict.
    
    Parameters
    ----------
    columns : list[str]
        Column names from cursor.description
    rows : list[tuple]
        Row data from cursor.fetchall()
        
    Returns
    -------
    list[DotDict]
        List of DotDict objects, one per row
        
    Examples
    --------
    >>> columns = ["id", "user_key", "age"]
    >>> rows = [(1, "aaa", 25), (2, "bbb", 30)]
    >>> result = dotdict_from_rows(columns, rows)
    >>> result[0].user_key
    'aaa'
    >>> result[1].age
    30
    """
    return [DotDict(zip(columns, row)) for row in rows]


__all__ = [
    "DotDict",
    "dotdict_from_rows",
]
