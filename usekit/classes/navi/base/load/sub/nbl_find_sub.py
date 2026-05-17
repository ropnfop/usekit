# Path: usekit.classes.navi.base.load.sub.nbl_path_sub.py
# -----------------------------------------------------------------------------------------------
#  Path Sub-functions - Processing utilities
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0 - Following dbl_read_sub.py pattern
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import List, Dict, Optional, Literal, Union
from datetime import datetime
import shutil

from usekit.classes.common.errors.helper_debug import log_and_raise


# ===============================================================================
# Statistics
# ===============================================================================

def proc_get_stat(path: Path) -> Dict:
    """
    Get file/directory statistics.
    
    Args:
        path: Path object to get stats for
        
    Returns:
        Dict with path info (exists, is_file, is_dir, size, mtime, ext)
        
    Examples:
        >>> proc_get_stat(Path("config.json"))
        {
            "path": PosixPath(...),
            "exists": True,
            "is_file": True,
            "is_dir": False,
            "size": 1024,
            "mtime": 1234567890.0,
            "mtime_str": "2024-11-15 10:30:00",
            "ext": ".json"
        }
    """
    try:
        stat = path.stat()
        return {
            "path": path,
            "exists": True,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "size": stat.st_size,
            "mtime": stat.st_mtime,
            "mtime_str": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            "ext": path.suffix,
        }
    except Exception:
        return {
            "path": path,
            "exists": False,
            "is_file": False,
            "is_dir": False,
            "size": None,
            "mtime": None,
            "mtime_str": None,
            "ext": path.suffix,
        }


# ===============================================================================
# Filtering
# ===============================================================================

def proc_filter_paths(
    paths: List[Path],
    filter_type: Literal["both", "files", "dirs"] = "both",
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    ext_filter: Optional[List[str]] = None
) -> List[Path]:
    """
    Filter paths by type, size, extension.
    
    Args:
        paths: List of Path objects to filter
        filter_type: "files", "dirs", or "both"
        min_size: Minimum file size in bytes
        max_size: Maximum file size in bytes
        ext_filter: List of extensions to include (e.g., [".json", ".yaml"])
        
    Returns:
        Filtered list of Path objects
        
    Examples:
        >>> paths = [Path("a.json"), Path("b.txt"), Path("dir/")]
        >>> proc_filter_paths(paths, filter_type="files", ext_filter=[".json"])
        [PosixPath('a.json')]
    """
    result = []
    
    for path in paths:
        # Type filter
        if filter_type == "files" and not path.is_file():
            continue
        if filter_type == "dirs" and not path.is_dir():
            continue
        
        # Size filter (files only)
        if path.is_file() and (min_size is not None or max_size is not None):
            try:
                size = path.stat().st_size
                if min_size is not None and size < min_size:
                    continue
                if max_size is not None and size > max_size:
                    continue
            except Exception:
                continue
        
        # Extension filter
        if ext_filter and path.suffix not in ext_filter:
            continue
        
        result.append(path)
    
    return result


# ===============================================================================
# Sorting
# ===============================================================================

def proc_sort_paths(
    paths: List[Path],
    sort_by: Literal["name", "size", "mtime", "ext"] = "name",
    reverse: bool = False
) -> List[Path]:
    """
    Sort paths by various criteria.
    
    Args:
        paths: List of Path objects to sort
        sort_by: Sort criteria - "name", "size", "mtime", or "ext"
        reverse: Reverse sort order (default: False)
        
    Returns:
        Sorted list of Path objects
        
    Examples:
        >>> paths = [Path("b.json"), Path("a.json")]
        >>> proc_sort_paths(paths, sort_by="name")
        [PosixPath('a.json'), PosixPath('b.json')]
        
        >>> proc_sort_paths(paths, sort_by="name", reverse=True)
        [PosixPath('b.json'), PosixPath('a.json')]
    """
    
    if sort_by == "name":
        return sorted(paths, key=lambda p: p.name, reverse=reverse)
    
    elif sort_by == "size":
        def size_key(p: Path) -> int:
            try:
                return p.stat().st_size if p.is_file() else 0
            except Exception:
                return 0
        return sorted(paths, key=size_key, reverse=reverse)
    
    elif sort_by == "mtime":
        def mtime_key(p: Path) -> float:
            try:
                return p.stat().st_mtime
            except Exception:
                return 0.0
        return sorted(paths, key=mtime_key, reverse=reverse)
    
    elif sort_by == "ext":
        return sorted(paths, key=lambda p: p.suffix, reverse=reverse)
    
    else:
        return paths


# ===============================================================================
# Directory Operations
# ===============================================================================

@log_and_raise
def proc_make_directory(path: Path, params: dict) -> Path:
    """
    Create directory if mk=True.
    
    For file paths, creates parent directory.
    For directory paths, creates the directory itself.
    
    Args:
        path: Path object (file or directory)
        params: Operation parameters (for debug)
        
    Returns:
        Original path (unchanged)
        
    Examples:
        >>> proc_make_directory(Path("data/config.json"), {"fmt": "json", "debug": True})
        PosixPath('data/config.json')
        # Creates 'data/' directory
    """
    # For file paths, create parent directory
    # For directory paths, create the directory itself
    target = path.parent if path.suffix else path
    
    target.mkdir(parents=True, exist_ok=True)
    
    if params.get("debug"):
        print(f"[{params['fmt'].upper()}] Created directory: {target}")
    
    return path


# ===============================================================================
# Remove Operations (NEW)
# ===============================================================================

@log_and_raise
def proc_remove_paths(
    paths: List[Path],
    params: dict,
    safe: bool = True,
    dry_run: bool = False
) -> Dict:
    """
    Remove files/directories.
    
    Args:
        paths: List of paths to remove
        params: Operation parameters (for debug/fmt)
        safe: Enable safety checks (default: True)
              - Prevents removing project root, home directory
              - Can be disabled for advanced use
        dry_run: Preview mode - show what would be deleted without deleting (default: False)
        
    Returns:
        Dict with removal results:
        {
            "removed": List[Path],      # Successfully removed paths
            "failed": List[Dict],        # Failed removals with errors
            "total": int,                # Total paths attempted
            "success_count": int,        # Number of successful removals
            "failed_count": int          # Number of failed removals
        }
        
    Safety:
        - safe=True (default): Prevents removing critical paths
        - safe=False: Allows all removals (use with caution)
        - dry_run=True: Shows what would be removed without actually deleting
        
    Examples:
        >>> # Dry run - preview only
        >>> proc_remove_paths([Path("temp1.txt"), Path("temp2.txt")], 
        ...                   {"fmt": "txt", "debug": True}, dry_run=True)
        {
            "removed": [PosixPath('temp1.txt'), PosixPath('temp2.txt')],
            "failed": [],
            "total": 2,
            "success_count": 2,
            "failed_count": 0
        }
        
        >>> # Actual removal
        >>> proc_remove_paths([Path("temp.txt")], {"fmt": "txt"}, dry_run=False)
        {
            "removed": [PosixPath('temp.txt')],
            "failed": [],
            "total": 1,
            "success_count": 1,
            "failed_count": 0
        }
    """
    removed = []
    failed = []
    
    for path in paths:
        try:
            # Safety checks
            if safe:
                # Don't remove project root or system paths
                if path == Path.cwd():
                    raise ValueError(f"Refusing to remove project root: {path}")
                if path == Path.home():
                    raise ValueError(f"Refusing to remove home directory: {path}")
                if path == Path("/"):
                    raise ValueError(f"Refusing to remove system root: {path}")
                
                # Check if path is parent of current directory
                try:
                    Path.cwd().relative_to(path)
                    raise ValueError(f"Refusing to remove parent of current directory: {path}")
                except ValueError:
                    pass  # Not a parent, safe to continue
            
            # Dry run mode
            if dry_run:
                removed.append(path)
                if params.get("debug"):
                    path_type = "DIR" if path.is_dir() else "FILE"
                    print(f"[DRY-RUN] Would remove {path_type}: {path}")
                continue
            
            # Actual removal
            if path.is_file():
                path.unlink()
                path_type = "FILE"
            elif path.is_dir():
                shutil.rmtree(path)
                path_type = "DIR"
            else:
                raise ValueError(f"Path does not exist: {path}")
            
            removed.append(path)
            
            if params.get("debug"):
                print(f"[{params['fmt'].upper()}] Removed {path_type}: {path}")
            
        except Exception as e:
            failed.append({
                "path": path,
                "error": str(e)
            })
            if params.get("debug"):
                print(f"[{params['fmt'].upper()}] Failed to remove {path}: {e}")
    
    return {
        "removed": removed,
        "failed": failed,
        "total": len(paths),
        "success_count": len(removed),
        "failed_count": len(failed)
    }


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    # Statistics
    "proc_get_stat",
    
    # Filtering & Sorting
    "proc_filter_paths",
    "proc_sort_paths",
    
    # Operations
    "proc_make_directory",
    "proc_remove_paths",
]
