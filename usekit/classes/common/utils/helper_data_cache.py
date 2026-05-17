# Path: usekit.classes.common.utils.helper_data_cache.py
# -----------------------------------------------------------------------------------------------
#  Runtime Data Cache - 런타임 데이터 캐시
#  Created by: THE Little Prince × ROP × FOP
#  세션 중 데이터를 메모리에 캐시
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Dict
import logging

logger = logging.getLogger(__name__)

# ===============================================================================
# Global Data Cache
# ===============================================================================

_DATA_CACHE: Dict[str, Any] = {}

"""
Structure:
{
    "json.base.config": {"key": "value"},
    "yaml.sub.settings": {"setting": "value"},
}
"""


# ===============================================================================
# Cache Operations
# ===============================================================================

def set_data_cache(fmt: str, loc: str, name: str, data: Any) -> Any:
    """
    Set data to runtime cache
    
    Args:
        fmt: Format name (json, yaml, etc.)
        loc: Location (base, sub, etc.)
        name: Cache key name
        data: Data to cache
        
    Returns:
        Cached data
        
    Examples:
        >>> set_data_cache("json", "base", "config", {"key": "value"})
        {'key': 'value'}
    """
    key = f"{fmt}.{loc}.{name}"
    _DATA_CACHE[key] = data
    
    logger.debug(f"[DATA_CACHE] Set: {key} ({type(data).__name__})")
    return data


def get_data_cache(fmt: str, loc: str, name: str, default: Any = None) -> Any:
    """
    Get data from runtime cache
    
    Args:
        fmt: Format name
        loc: Location
        name: Cache key name
        default: Default value if not found
        
    Returns:
        Cached data or default
        
    Examples:
        >>> set_data_cache("json", "base", "temp", {"test": 1})
        >>> get_data_cache("json", "base", "temp")
        {'test': 1}
        
        >>> get_data_cache("json", "base", "notfound", default={})
        {}
    """
    key = f"{fmt}.{loc}.{name}"
    return _DATA_CACHE.get(key, default)


def has_data_cache(fmt: str, loc: str, name: str) -> bool:
    """
    Check if data cache exists
    
    Args:
        fmt: Format name
        loc: Location
        name: Cache key name
        
    Returns:
        True if cache exists
    """
    key = f"{fmt}.{loc}.{name}"
    return key in _DATA_CACHE


def delete_data_cache(fmt: str, loc: str, name: str) -> bool:
    """
    Delete data from cache
    
    Args:
        fmt: Format name
        loc: Location
        name: Cache key name
        
    Returns:
        True if deleted, False if not found
    """
    key = f"{fmt}.{loc}.{name}"
    if key in _DATA_CACHE:
        del _DATA_CACHE[key]
        logger.debug(f"[DATA_CACHE] Deleted: {key}")
        return True
    return False


def clear_data_cache(fmt: Optional[str] = None, loc: Optional[str] = None):
    """
    Clear data cache
    
    Args:
        fmt: If provided, clear only this format
        loc: If provided (with fmt), clear only this location
        
    Examples:
        >>> clear_data_cache()                  # Clear all
        >>> clear_data_cache("json")            # Clear json.*
        >>> clear_data_cache("json", "base")    # Clear json.base.*
    """
    global _DATA_CACHE
    
    if fmt is None and loc is None:
        _DATA_CACHE.clear()
        logger.debug("[DATA_CACHE] Cleared all")
        return
    
    if fmt and loc:
        prefix = f"{fmt}.{loc}."
    elif fmt:
        prefix = f"{fmt}."
    else:
        return
    
    to_delete = [k for k in _DATA_CACHE if k.startswith(prefix)]
    for key in to_delete:
        del _DATA_CACHE[key]
    
    logger.debug(f"[DATA_CACHE] Cleared {prefix}* ({len(to_delete)} entries)")


def list_data_cache(fmt: Optional[str] = None, loc: Optional[str] = None) -> Dict[str, Any]:
    """
    List all cached data
    
    Args:
        fmt: If provided, list only this format
        loc: If provided (with fmt), list only this location
        
    Returns:
        Dict of cached data
        
    Examples:
        >>> list_data_cache()                # All
        >>> list_data_cache("json")          # json.*
        >>> list_data_cache("json", "base")  # json.base.*
    """
    if fmt is None and loc is None:
        return _DATA_CACHE.copy()
    
    if fmt and loc:
        prefix = f"{fmt}.{loc}."
    elif fmt:
        prefix = f"{fmt}."
    else:
        return _DATA_CACHE.copy()
    
    return {k: v for k, v in _DATA_CACHE.items() if k.startswith(prefix)}


# ===============================================================================
# Update Operations
# ===============================================================================

def update_data_cache(fmt: str, loc: str, name: str, updates: Any, merge: bool = True) -> Any:
    """
    Update existing cached data
    
    Args:
        fmt: Format name
        loc: Location
        name: Cache key name
        updates: Data to merge/update
        merge: If True, merge with existing data
        
    Returns:
        Updated data
        
    Examples:
        >>> set_data_cache("json", "base", "config", {"a": 1})
        >>> update_data_cache("json", "base", "config", {"b": 2})
        {'a': 1, 'b': 2}
    """
    key = f"{fmt}.{loc}.{name}"
    
    if not merge or key not in _DATA_CACHE:
        _DATA_CACHE[key] = updates
        return updates
    
    current = _DATA_CACHE[key]
    
    # Merge logic
    if isinstance(current, dict) and isinstance(updates, dict):
        current.update(updates)
        updated = current
    elif isinstance(current, list) and isinstance(updates, list):
        updated = current + updates
    else:
        updated = updates
    
    _DATA_CACHE[key] = updated
    logger.debug(f"[DATA_CACHE] Updated: {key}")
    
    return updated


# ===============================================================================
# Statistics
# ===============================================================================

def get_cache_stats() -> dict:
    """
    Get cache statistics
    
    Returns:
        Dict with cache stats
    """
    by_format = {}
    by_type = {}
    
    for key, value in _DATA_CACHE.items():
        fmt = key.split(".")[0]
        by_format[fmt] = by_format.get(fmt, 0) + 1
        
        type_name = type(value).__name__
        by_type[type_name] = by_type.get(type_name, 0) + 1
    
    return {
        "total": len(_DATA_CACHE),
        "by_format": by_format,
        "by_type": by_type,
        "keys": list(_DATA_CACHE.keys())
    }


def print_cache_stats(show_data: bool = False):
    """
    Print cache statistics
    
    Args:
        show_data: If True, show cached data preview
    """
    stats = get_cache_stats()
    print("=" * 60)
    print("Data Cache Statistics")
    print("=" * 60)
    print(f"Total entries: {stats['total']}")
    
    print("\nBy format:")
    for fmt, count in stats['by_format'].items():
        print(f"  {fmt}: {count}")
    
    print("\nBy type:")
    for type_name, count in stats['by_type'].items():
        print(f"  {type_name}: {count}")
    
    print("\nCached keys:")
    for key in stats['keys']:
        data = _DATA_CACHE[key]
        type_name = type(data).__name__
        
        if show_data:
            preview = str(data)[:50]
            if len(str(data)) > 50:
                preview += "..."
            print(f"  {key} ({type_name}): {preview}")
        else:
            print(f"  {key} ({type_name})")
    
    print("=" * 60)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "set_data_cache",
    "get_data_cache",
    "has_data_cache",
    "delete_data_cache",
    "clear_data_cache",
    "list_data_cache",
    "update_data_cache",
    "get_cache_stats",
    "print_cache_stats",
]


if __name__ == "__main__":
    # Test
    print("Testing data_cache...")
    
    # Set
    set_data_cache("json", "base", "config", {"key": "value"})
    set_data_cache("yaml", "sub", "settings", {"setting": "test"})
    set_data_cache("json", "base", "list", [1, 2, 3])
    
    # Get
    print(f"json.base.config: {get_data_cache('json', 'base', 'config')}")
    print(f"yaml.sub.settings: {get_data_cache('yaml', 'sub', 'settings')}")
    print(f"notfound: {get_data_cache('json', 'base', 'notfound', default='N/A')}")
    
    # Update
    update_data_cache("json", "base", "config", {"new": "value"})
    print(f"After update: {get_data_cache('json', 'base', 'config')}")
    
    # List
    print("\nAll cache:")
    print(list_data_cache())
    
    print("\nJSON only:")
    print(list_data_cache("json"))
    
    # Stats
    print("\n")
    print_cache_stats(show_data=True)
    
    # Clear
    clear_data_cache("json", "base")
    print("\nAfter clearing json.base:")
    print_cache_stats()
    
    clear_data_cache()
    print("\nAfter clearing all:")
    print_cache_stats()