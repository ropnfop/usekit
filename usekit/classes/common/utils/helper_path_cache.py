# Path: usekit.classes.common.utils.helper_path_cache.py
# -----------------------------------------------------------------------------------------------
#  Runtime Path Cache - 런타임 경로 설정 캐시
#  Created by: THE Little Prince × ROP × FOP
#  세션 중 동적 경로 변경을 위한 메모리 캐시
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

# ===============================================================================
# Global Path Cache
# ===============================================================================

_PATH_CACHE: Dict[str, Path] = {}

"""
Structure:
{
    "json.base": Path("/custom/path"),
    "yaml.sub": Path("/another/path"),
}
"""


# ===============================================================================
# Cache Operations
# ===============================================================================

def set_path_cache(fmt: str, loc: str, path: str | Path) -> Path:
    """
    Set runtime path cache
    
    Args:
        fmt: Format name (json, yaml, txt, etc.)
        loc: Location (base, sub, now, dir, tmp, cus)
        path: Path to cache
        
    Returns:
        Cached Path object
        
    Examples:
        >>> set_path_cache("json", "base", "custom/json")
        PosixPath('custom/json')
        
        >>> set_path_cache("txt", "base", "/abs/path/txt")
        PosixPath('/abs/path/txt')
    """
    key = f"{fmt}.{loc}"
    path_obj = Path(path).resolve()
    _PATH_CACHE[key] = path_obj
    
    logger.debug(f"[PATH_CACHE] Set: {key} -> {path_obj}")
    return path_obj


def get_path_cache(fmt: str, loc: str) -> Optional[Path]:
    """
    Get path from runtime cache
    
    Args:
        fmt: Format name
        loc: Location
        
    Returns:
        Cached Path or None if not found
        
    Examples:
        >>> set_path_cache("json", "base", "custom/json")
        >>> get_path_cache("json", "base")
        PosixPath('custom/json')
        
        >>> get_path_cache("yaml", "sub")
        None
    """
    key = f"{fmt}.{loc}"
    return _PATH_CACHE.get(key)


def has_path_cache(fmt: str, loc: str) -> bool:
    """
    Check if path cache exists
    
    Args:
        fmt: Format name
        loc: Location
        
    Returns:
        True if cache exists
    """
    key = f"{fmt}.{loc}"
    return key in _PATH_CACHE


def delete_path_cache(fmt: str, loc: str) -> bool:
    """
    Delete path from cache
    
    Args:
        fmt: Format name
        loc: Location
        
    Returns:
        True if deleted, False if not found
    """
    key = f"{fmt}.{loc}"
    if key in _PATH_CACHE:
        del _PATH_CACHE[key]
        logger.debug(f"[PATH_CACHE] Deleted: {key}")
        return True
    return False


def clear_path_cache(fmt: Optional[str] = None):
    """
    Clear path cache
    
    Args:
        fmt: If provided, clear only this format. If None, clear all.
        
    Examples:
        >>> clear_path_cache("json")  # Clear json.* only
        >>> clear_path_cache()         # Clear all
    """
    global _PATH_CACHE
    
    if fmt is None:
        _PATH_CACHE.clear()
        logger.debug("[PATH_CACHE] Cleared all")
    else:
        prefix = f"{fmt}."
        to_delete = [k for k in _PATH_CACHE if k.startswith(prefix)]
        for key in to_delete:
            del _PATH_CACHE[key]
        logger.debug(f"[PATH_CACHE] Cleared {fmt}.* ({len(to_delete)} entries)")


def list_path_cache(fmt: Optional[str] = None) -> Dict[str, Path]:
    """
    List all cached paths
    
    Args:
        fmt: If provided, list only this format
        
    Returns:
        Dict of cached paths
        
    Examples:
        >>> list_path_cache()
        {'json.base': PosixPath('...'), 'yaml.sub': PosixPath('...')}
        
        >>> list_path_cache("json")
        {'json.base': PosixPath('...'), 'json.sub': PosixPath('...')}
    """
    if fmt is None:
        return _PATH_CACHE.copy()
    
    prefix = f"{fmt}."
    return {k: v for k, v in _PATH_CACHE.items() if k.startswith(prefix)}


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
    for key in _PATH_CACHE:
        fmt = key.split(".")[0]
        by_format[fmt] = by_format.get(fmt, 0) + 1
    
    return {
        "total": len(_PATH_CACHE),
        "by_format": by_format,
        "keys": list(_PATH_CACHE.keys())
    }


def print_cache_stats():
    """Print cache statistics"""
    stats = get_cache_stats()
    print("=" * 60)
    print("Path Cache Statistics")
    print("=" * 60)
    print(f"Total entries: {stats['total']}")
    print("\nBy format:")
    for fmt, count in stats['by_format'].items():
        print(f"  {fmt}: {count}")
    print("\nCached keys:")
    for key in stats['keys']:
        print(f"  {key} -> {_PATH_CACHE[key]}")
    print("=" * 60)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "set_path_cache",
    "get_path_cache",
    "has_path_cache",
    "delete_path_cache",
    "clear_path_cache",
    "list_path_cache",
    "get_cache_stats",
    "print_cache_stats",
]


if __name__ == "__main__":
    # Test
    print("Testing path_cache...")
    
    # Set
    set_path_cache("json", "base", "custom/json")
    set_path_cache("yaml", "sub", "/abs/yaml")
    set_path_cache("txt", "base", "ext/txt")
    
    # Get
    print(f"json.base: {get_path_cache('json', 'base')}")
    print(f"yaml.sub: {get_path_cache('yaml', 'sub')}")
    print(f"csv.base (not exists): {get_path_cache('csv', 'base')}")
    
    # List
    print("\nAll cache:")
    print(list_path_cache())
    
    print("\nJSON only:")
    print(list_path_cache("json"))
    
    # Stats
    print("\n")
    print_cache_stats()
    
    # Clear
    clear_path_cache("json")
    print("\nAfter clearing json:")
    print_cache_stats()
    
    clear_path_cache()
    print("\nAfter clearing all:")
    print_cache_stats()