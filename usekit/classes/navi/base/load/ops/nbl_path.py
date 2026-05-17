# Path: usekit.classes.navi.base.load.ops.nbl_path.py
# -----------------------------------------------------------------------------------------------
#  Path Operation - find_data_search Based Architecture
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - Path = Directory-Only Navigation
#  - find_data_search handles ALL file discovery
#  - Path just processes results (stat or unique dirs)
#  - name parameter is SYSTEM-USE ONLY
#  - Positional argument auto-binds to dp (dir_path)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Union

from usekit.infra.navi_signature import params_for_path, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_search import find_data_search
from usekit.classes.common.utils.helper_path import get_smart_path
from usekit.classes.navi.base.load.sub.nbl_path_sub import (
    proc_make_directory,
    proc_remove_directory,
    proc_remove_directories
)


# ===============================================================================
# Validation
# ===============================================================================

def _validate_path_params(p: dict) -> bool:
    """
    Validate Path-specific parameters and detect mode.
    
    Args:
        p: Parameters dict from params_for_path()
        
    Returns:
        bool: True if file search mode (name != "path_default"), False for directory mode
        
    Notes:
        - name="path_default" → Directory navigation mode
        - name=something else → File search mode (get absolute path of file)
    """
    # If name is provided and not default, switch to file search mode
    if p["name"] and p["name"] != "path_default":
        return True  # File search mode
    
    return False  # Directory mode


# ===============================================================================
# Directory Extraction
# ===============================================================================

def _extract_unique_dirs(files: List[Path]) -> List[Path]:
    """
    Extract unique parent directories from file list.
    
    Args:
        files: List of file Path objects
        
    Returns:
        Sorted list of unique directory paths
        
    Examples:
        >>> files = [
        ...     Path("/data/json/a.json"),
        ...     Path("/data/json/b.json"),
        ...     Path("/data/yaml/c.yaml")
        ... ]
        >>> _extract_unique_dirs(files)
        [PosixPath('/data/json'), PosixPath('/data/yaml')]
    """
    if not files:
        return []
    
    # Extract parent directories and make unique
    dirs = set(f.parent for f in files)
    
    # Sort for consistent output
    return sorted(dirs)


# ===============================================================================
# Statistics Calculation
# ===============================================================================

def _calculate_directory_stats(
    files: List[Path],
    base_path: Path,
    walk: bool = False,
    debug: bool = False
) -> Dict:
    """
    Calculate directory statistics from file list.
    
    Args:
        files: List of file Path objects from find_data_search
        base_path: Base directory path for reference
        walk: Whether subdirectories were included
        debug: Debug output
        
    Returns:
        Dict with directory statistics
        
    Examples:
        >>> files = [Path("a.json"), Path("b.yaml"), Path("c.txt")]
        >>> _calculate_directory_stats(files, Path("/data"))
        {
            "path": PosixPath('/data'),
            "total_files": 3,
            "total_dirs": 1,
            "total_size": 1024,
            "total_size_str": "1.0 KB",
            "by_format": {"json": 1, "yaml": 1, "txt": 1}
        }
    """
    
    total_files = len(files)
    total_size = 0
    format_counts = {}
    subdirs = set()
    
    # Process each file
    for f in files:
        try:
            # Calculate size
            total_size += f.stat().st_size
            
            # Count by extension
            ext = f.suffix.lower()
            if ext:
                fmt_key = ext[1:] if ext.startswith(".") else ext
                format_counts[fmt_key] = format_counts.get(fmt_key, 0) + 1
            else:
                format_counts["no_extension"] = format_counts.get("no_extension", 0) + 1
            
            # Collect subdirectories if walk=True
            if walk:
                subdirs.add(f.parent)
                
        except Exception as e:
            if debug:
                print(f"[STAT] Error processing {f}: {e}")
            continue
    
    # Format size for readability
    def format_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # Count unique directories
    total_dirs = len(subdirs) if walk else 0
    
    if debug:
        walk_status = "with subdirectories" if walk else "current level only"
        print(f"[STAT] Base: {base_path} ({walk_status})")
        print(f"[STAT] Files: {total_files}, Dirs: {total_dirs}, Size: {format_size(total_size)}")
        if format_counts:
            print(f"[STAT] Formats: {format_counts}")
    
    result = {
        "path": base_path,
        "total_files": total_files,
        "total_dirs": total_dirs,
        "total_size": total_size,
        "total_size_str": format_size(total_size),
        "by_format": format_counts
    }
    
    # Add subdirs list only when walk=True
    if walk and subdirs:
        result["subdirs"] = sorted(subdirs)
    
    return result


# ===============================================================================
# File Path Search
# ===============================================================================

def _search_file_path(filename: str, p: dict) -> Union[Path, List[Path], None]:
    """
    Search for file and return its parent directory path.
    
    Philosophy: Path returns DIRECTORY, Find returns FILE.
    
    Args:
        filename: Filename or pattern to search
        p: Parameters dict from params_for_path()
        
    Returns:
        Path: Single directory path if only one match
        List[Path]: Multiple directory paths if multiple matches (unique directories)
        None: No matches found
        
    Examples:
        >>> _search_file_path("test", {"fmt": "json", "loc": "base"})
        PosixPath('/data/json/')
        
        >>> _search_file_path("user_*", {"fmt": "json", "loc": "base", "walk": True})
        [PosixPath('/data/json/'), PosixPath('/data/json/subdir/')]
    """
    # Use find_data_search to get files matching the name
    files = find_data_search(
        format_type=p["fmt"],
        mod=p.get("mod"),
        pattern=filename,
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        walk=p.get("walk", True),  # Default to walk=True for file search
        case_sensitive=False,
        debug=p.get("debug", False)
    )
    
    if p.get("debug"):
        search_scope = "recursive" if p.get("walk", True) else "current directory"
        print(f"[FILE-SEARCH] Searching '{filename}' in {p['loc']} ({search_scope})")
        print(f"[FILE-SEARCH] Found {len(files)} file(s)")
    
    # No matches
    if not files:
        if p.get("debug"):
            print(f"[FILE-SEARCH] No files found matching '{filename}'")
        return None
    
    # Extract unique parent directories
    unique_dirs = _extract_unique_dirs(files)
    
    if p.get("debug"):
        print(f"[FILE-SEARCH] Extracted {len(unique_dirs)} unique directory(s)")
    
    # Single directory - return Path object
    if len(unique_dirs) == 1:
        return unique_dirs[0]
    
    # Multiple directories - return list
    return unique_dirs


# ===============================================================================
# Main Path Operation
# ===============================================================================

@log_and_raise
def path_operation(**kwargs) -> Any:
    """
    Directory-only path navigation powered by find_data_search.
    Also supports file path search when name is provided.
    
    Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Path = Directory Navigation (Find = File Search)
    - find_data_search: Handles ALL file discovery logic
    - Path: Processes results (stat or unique dirs)
    - name parameter: 
      * "path_default" → Directory mode
      * Actual filename → File search mode (returns absolute path)
    - Positional input: Auto-binds to dp (dir_path)
    
    Modes:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. DIRECTORY MODE (name="path_default"):
       - Returns directory paths
       - Supports stat, walk, mk, rm operations
    
    2. FILE SEARCH MODE (name=filename):
       - Searches for file by name
       - Returns DIRECTORY PATH where file is located
       - Returns Path object (single dir) or List[Path] (multiple dirs)
       - Philosophy: Path = Directory, Find = File
    
    Architecture:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. find_data_search: Get files (with walk support)
    2. Process results:
       - stat=True: Calculate statistics
       - stat=False: Extract unique directories
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Directory mode
    use.path.json.base(walk=True, stat=True)
      → find_data_search(fmt="json", walk=True)
      → files = [a.json, b.json, ...]
      → calculate_stats(files)
      → {total_files: 10, by_format: {...}, subdirs: [...]}
    
    # File search mode - returns directory containing the file
    u.pjb("test")
      → find_data_search(pattern="test")
      → files = [/data/json/test.json]
      → extract_unique_dirs(files)
      → PosixPath('/data/json/')
    
    u.pjb("user_*")
      → find_data_search(pattern="user_*")
      → files = [/data/json/user_001.json, /data/json/sub/user_002.json]
      → extract_unique_dirs(files)
      → [PosixPath('/data/json/'), PosixPath('/data/json/sub/')]
    
    Args:
        **kwargs: Common Navigation parameters
        
        # Core (AUTO-MANAGED)
        fmt: File format (json/yaml/txt/csv/any)
        name: "path_default" for directory mode, filename for file search
        loc: Location (base/sub/dir/now/tmp/cus/cache)
        
        # User Input
        dp (dir_path): Custom directory path (from positional)
        
        # Format options
        mod: When fmt="any", specify format (default: all)
        
        # Output options
        stat: Include directory statistics (default: False)
        walk: Recursive subdirectory traversal (default: False for dir, True for file)
        
        # Operations
        mk: Create directory (default: False)
        rm: Remove directories (default: False)
        safe: Safety checks for rm (default: True)
        dry_run: Preview rm without deleting (default: False)
        
        debug: Debug mode
    
    Returns:
        DIRECTORY MODE:
        - Without stat: Path object (single dir) or List[Path] (multiple dirs)
        - With stat: Dict with directory statistics
        
        FILE SEARCH MODE:
        - Path object (directory containing the file) if single location
        - List[Path] (multiple directories) if files in multiple locations
        - None if no files found
        
        Note: Path ALWAYS returns directory paths, never file paths.
              Use Find operation for file paths.
    
    Examples:
        # Directory mode
        >>> path_operation(fmt="json")
        PosixPath('/path/data/json/')
        
        >>> u.pjb()
        PosixPath('/path/data/json/')
        
        # File search mode - returns directory containing file
        >>> u.pjb("test")
        PosixPath('/data/json/')
        
        >>> u.pjb("user_*")
        [
            PosixPath('/data/json/'),
            PosixPath('/data/json/subdir/')
        ]
        
        >>> u.ptd("myconfig")  # Search any format, return directory
        PosixPath('/data/')
        
        # Comparison: Path vs Find
        >>> u.pjb("test")  # Path - returns directory
        PosixPath('/data/json/')
        
        >>> u.fjb("test")  # Find - returns file
        PosixPath('/data/json/test.json')
        
        # With custom directory
        >>> u.pjb("mydata")
        PosixPath('/path/mydata/data/json/')
        
        # Directory stats (current level)
        >>> path_operation(fmt="json", stat=True)
        {
            "path": PosixPath('/path/data/json/'),
            "total_files": 45,
            "total_dirs": 0,
            "total_size": 1048576,
            "total_size_str": "1.0 MB",
            "by_format": {"json": 45}
        }
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract & Validate Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_path(**kwargs)
    
    # Warn about future features
    warn_future_features(p)
    
    # Check mode: directory or file search
    is_file_search_mode = _validate_path_params(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [FILE SEARCH MODE]
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if is_file_search_mode:
        return _search_file_path(p["name"], p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [DIRECTORY MODE] - Original logic
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # [2] Get Base Directory Path
    base_path = get_smart_path(
        fmt=p["fmt"],
        filename=None,
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        cus=p["cus"],
        ensure_ext=False,
    )
    
    # [3] Create Directory if mk=True
    if p.get("mk"):
        proc_make_directory(base_path, p)
        # Continue to normal flow (don't return early)
    
    # [4] Use find_data_search to Get Files
    files = find_data_search(
        format_type=p["fmt"],
        mod=p.get("mod"),
        pattern="*",  # All files
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        walk=p.get("walk", False),  # Pass walk parameter
        case_sensitive=False,
        debug=p.get("debug", False)
    )
    
    if p.get("debug"):
        walk_status = f"walk={p.get('walk', False)}"
        print(f"[{p['fmt'].upper()}] Base: {base_path} [{walk_status}]")
        print(f"[{p['fmt'].upper()}] Found {len(files)} files via find_data_search")
    
    # [5] Process Results
    
    # No files found - return base path or empty stats
    if not files:
        if p.get("stat"):
            return {
                "path": base_path,
                "total_files": 0,
                "total_dirs": 0,
                "total_size": 0,
                "total_size_str": "0 B",
                "by_format": {}
            }
        else:
            return base_path
    
    # Extract unique directories from files
    unique_dirs = _extract_unique_dirs(files)
    
    # rm=True: Remove directories
    if p.get("rm"):
        return proc_remove_directories(
            unique_dirs,
            p,
            safe=p.get("safe", True),
            dry_run=p.get("dry_run", False)
        )
    
    # stat=True: Calculate statistics
    if p.get("stat"):
        return _calculate_directory_stats(
            files,
            base_path,
            walk=p.get("walk", False),
            debug=p.get("debug", False)
        )
    
    # stat=False: Return unique directories
    
    # Single directory: return Path object
    if len(unique_dirs) == 1:
        return unique_dirs[0]
    
    # Multiple directories: return list
    return unique_dirs


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["path_operation"]
