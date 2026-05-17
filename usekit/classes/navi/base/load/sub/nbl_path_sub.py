# Path: usekit.classes.navi.base.load.sub.nbl_path_sub.py
# -----------------------------------------------------------------------------------------------
#  Path Sub-functions - Directory Management Only
#  Created by: THE Little Prince × ROP × FOP
#  Version: 4.0 - Minimal Directory Operations
#  
#  Philosophy:
#  - Path handles DIRECTORY operations only (create, remove)
#  - Statistics calculated in nbl_path.py using find_data_search results
#  - File operations moved to Find
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Dict, List
import shutil

from usekit.classes.common.errors.helper_debug import log_and_raise


# ===============================================================================
# Directory Creation
# ===============================================================================

@log_and_raise
def proc_make_directory(path: Path, params: dict) -> Path:
    """
    Create directory.
    
    Args:
        path: Directory Path object to create
        params: Operation parameters (for debug)
        
    Returns:
        Original path (unchanged)
        
    Examples:
        >>> proc_make_directory(Path("data/json/"), {"fmt": "json", "debug": True})
        PosixPath('data/json/')
        # Creates 'data/json/' directory
    """
    # Create the directory
    path.mkdir(parents=True, exist_ok=True)
    
    if params.get("debug"):
        print(f"[{params['fmt'].upper()}] Created directory: {path}")
    
    return path


# ===============================================================================
# Directory Removal
# ===============================================================================

@log_and_raise
def proc_remove_directory(
    path: Path,
    params: dict,
    safe: bool = True,
    dry_run: bool = False
) -> Dict:
    """
    Remove directory.
    
    Args:
        path: Directory path to remove
        params: Operation parameters (for debug/fmt)
        safe: Enable safety checks (default: True)
              - Prevents removing project root, home directory
        dry_run: Preview mode (default: False)
        
    Returns:
        Dict with removal results:
        {
            "removed": Path or None,
            "error": str or None,
            "success": bool
        }
        
    Safety:
        - safe=True (default): Prevents removing critical paths
        - safe=False: Allows all removals (use with caution)
        - dry_run=True: Shows what would be removed without deleting
        
    Examples:
        >>> # Dry run
        >>> proc_remove_directory(Path("temp/"), {"fmt": "any"}, dry_run=True)
        {
            "removed": PosixPath('temp/'),
            "error": None,
            "success": True
        }
        
        >>> # Actual removal
        >>> proc_remove_directory(Path("temp/"), {"fmt": "any"})
        {
            "removed": PosixPath('temp/'),
            "error": None,
            "success": True
        }
    """
    try:
        # Safety checks
        if safe:
            # Don't remove critical paths
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
            if params.get("debug"):
                print(f"[DRY-RUN] Would remove DIR: {path}")
            return {
                "removed": path,
                "error": None,
                "success": True
            }
        
        # Actual removal
        if path.is_dir():
            shutil.rmtree(path)
            
            if params.get("debug"):
                print(f"[{params['fmt'].upper()}] Removed DIR: {path}")
            
            return {
                "removed": path,
                "error": None,
                "success": True
            }
        else:
            raise ValueError(f"Path is not a directory: {path}")
        
    except Exception as e:
        if params.get("debug"):
            print(f"[{params['fmt'].upper()}] Failed to remove {path}: {e}")
        
        return {
            "removed": None,
            "error": str(e),
            "success": False
        }


# ===============================================================================
# Batch Directory Removal
# ===============================================================================

@log_and_raise
def proc_remove_directories(
    paths: List[Path],
    params: dict,
    safe: bool = True,
    dry_run: bool = False
) -> Dict:
    """
    Remove multiple directories.
    
    Args:
        paths: List of directory paths to remove
        params: Operation parameters (for debug/fmt)
        safe: Enable safety checks (default: True)
        dry_run: Preview mode (default: False)
        
    Returns:
        Dict with batch removal results:
        {
            "removed": List[Path],
            "failed": List[Dict],
            "total": int,
            "success_count": int,
            "failed_count": int
        }
        
    Examples:
        >>> paths = [Path("temp1/"), Path("temp2/")]
        >>> proc_remove_directories(paths, {"fmt": "any"}, dry_run=True)
        {
            "removed": [PosixPath('temp1/'), PosixPath('temp2/')],
            "failed": [],
            "total": 2,
            "success_count": 2,
            "failed_count": 0
        }
    """
    removed = []
    failed = []
    
    for path in paths:
        result = proc_remove_directory(path, params, safe, dry_run)
        
        if result["success"]:
            removed.append(result["removed"])
        else:
            failed.append({
                "path": path,
                "error": result["error"]
            })
    
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
    # Directory Operations
    "proc_make_directory",
    "proc_remove_directory",
    "proc_remove_directories",
]
