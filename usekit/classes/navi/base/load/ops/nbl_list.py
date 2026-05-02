# Path: usekit.classes.navi.base.load.ops.nbl_list.py
# -----------------------------------------------------------------------------------------------
#  List Operation - Directory Listing
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - List = Simple Directory Listing
#  - Shows what's in a directory (files + subdirs)
#  - walk=True: Show hierarchical structure
#  - stat=True: Show summary statistics
#  - Simplest way to answer: "What's in here?"
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Union

from usekit.infra.navi_signature import params_for_list, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_path import get_smart_path
from usekit.classes.common.utils.helper_search import find_data_search


# ===============================================================================
# Helper Functions
# ===============================================================================

def _format_size(size_bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


# ===============================================================================
# Direct Directory Listing (walk=False)
# ===============================================================================

def _list_directory_simple(directory: Path) -> List[str]:
    """
    List items in a single directory directly.
    Shows all items including empty subdirectories.
    
    Args:
        directory: Directory path to list
        
    Returns:
        List of filenames and subdirectory names (with trailing '/')
        
    Examples:
        ['config.json', 'user.json', 'empty_dir/', 'tests/']
    """
    items = []
    
    try:
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                items.append(f"{item.name}/")
            else:
                items.append(item.name)
    except Exception:
        pass
    
    return items


def _list_directory_stat(directory: Path) -> Dict[str, Any]:
    """
    List directory with statistics (current level only).
    
    Args:
        directory: Directory to analyze
        
    Returns:
        Dict with files, dirs, counts, and size
        
    Examples:
        {
            'files': ['a.json', 'b.json'],
            'dirs': ['empty_dir/', 'tests/'],
            'total_files': 2,
            'total_dirs': 2,
            'total_size': 2048,
            'total_size_str': '2.0 KB'
        }
    """
    files = []
    dirs = []
    total_size = 0
    
    try:
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                dirs.append(f"{item.name}/")
            else:
                files.append(item.name)
                try:
                    total_size += item.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    
    return {
        'files': files,
        'dirs': dirs,
        'total_files': len(files),
        'total_dirs': len(dirs),
        'total_size': total_size,
        'total_size_str': _format_size(total_size)
    }


# ===============================================================================
# File-Based Listing (walk=True, uses find_data_search)
# ===============================================================================

def _list_from_files_walk(files: List[Path]) -> List[Dict[str, Any]]:
    """
    Build hierarchical structure from file list.
    Only shows directories that contain files.
    
    Groups files by directory and returns path + items for each.
    """
    from collections import defaultdict
    
    # Group files by parent directory
    dirs_dict = defaultdict(list)
    all_dirs = set()
    
    for f in files:
        dirs_dict[f.parent].append(f.name)
        all_dirs.add(f.parent)
        
        # Add all parent directories
        current = f.parent
        while current.parent != current:
            all_dirs.add(current.parent)
            current = current.parent
    
    # Build result
    result = []
    for dir_path in sorted(all_dirs):
        items = []
        
        # Add files in this directory
        if dir_path in dirs_dict:
            items.extend(sorted(dirs_dict[dir_path]))
        
        # Add subdirectories
        subdirs = [d for d in all_dirs if d.parent == dir_path]
        for subdir in sorted(subdirs):
            items.append(f"{subdir.name}/")
        
        if items:
            result.append({
                'path': str(dir_path),
                'items': items
            })
    
    return result


def _list_from_files_walk_stat(files: List[Path]) -> List[Dict[str, Any]]:
    """
    Build hierarchical structure with statistics from file list.
    Only shows directories that contain files.
    """
    from collections import defaultdict
    
    # Group files by parent directory
    dirs_dict = defaultdict(list)
    all_dirs = set()
    
    for f in files:
        dirs_dict[f.parent].append(f)
        all_dirs.add(f.parent)
        
        # Add all parent directories
        current = f.parent
        while current.parent != current:
            all_dirs.add(current.parent)
            current = current.parent
    
    # Build result with stats
    result = []
    for dir_path in sorted(all_dirs):
        items = []
        file_names = []
        dir_names = []
        total_size = 0
        
        # Process files in this directory
        if dir_path in dirs_dict:
            for f in sorted(dirs_dict[dir_path], key=lambda x: x.name):
                items.append(f.name)
                file_names.append(f.name)
                try:
                    total_size += f.stat().st_size
                except Exception:
                    pass
        
        # Add subdirectories
        subdirs = [d for d in all_dirs if d.parent == dir_path]
        for subdir in sorted(subdirs):
            items.append(f"{subdir.name}/")
            dir_names.append(f"{subdir.name}/")
        
        if items:
            result.append({
                'path': str(dir_path),
                'items': items,
                'files': file_names,
                'dirs': dir_names,
                'file_count': len(file_names),
                'dir_count': len(dir_names),
                'size': total_size,
                'size_str': _format_size(total_size)
            })
    
    return result


# ===============================================================================
# Main List Operation
# ===============================================================================

@log_and_raise
def list_operation(**kwargs) -> Union[List[str], Dict[str, Any], List[Dict[str, Any]]]:
    """
    List files and directories in a location.
    
    Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    List = Simple Directory Listing
    - Default: Show what's in directory
    - walk=True: Show hierarchical structure
    - stat=True: Show summary statistics
    - Simplest way to answer: "What's in here?"
    
    Architecture:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Resolve directory path
    2. List based on options:
       - Default: Simple list of items
       - walk: Hierarchical structure
       - stat: Statistics summary
       - walk+stat: Full details
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Simple list
    use.list.json.base()
      → ['config.json', 'user.json', 'tests/']
    
    # With walk
    use.list.json.base(walk=True)
      → [
          {'path': 'data/json/base', 'items': ['a.json', 'tests/']},
          {'path': 'data/json/base/tests', 'items': ['t.json']}
        ]
    
    # With stat
    use.list.json.base(stat=True)
      → {
          'files': ['a.json', 'b.json'],
          'dirs': ['tests/'],
          'total_files': 2,
          'total_dirs': 1,
          'total_size': 2048,
          'total_size_str': '2.0 KB'
        }
    
    # With walk + stat
    use.list.json.base(walk=True, stat=True)
      → [
          {
            'path': 'data/json/base',
            'items': ['a.json', 'tests/'],
            'files': ['a.json'],
            'dirs': ['tests/'],
            'file_count': 1,
            'dir_count': 1,
            'size': 1024,
            'size_str': '1.0 KB'
          }
        ]
    
    Args:
        **kwargs: Common Navigation parameters
        
        # Core
        fmt: File format (json/yaml/txt/csv/any)
        name: Not used for list (reserved for consistency)
        loc: Location (base/sub/dir/now/tmp/cache)
        
        # Format options
        mod: When fmt="any", specify format (default: all)
        
        # Output options
        walk: Recursive subdirectory listing (default: False)
        stat: Include statistics (default: False)
        
        # Path options
        dir_path: Custom directory path (for loc="dir")
        cus: Custom path flag
        
        debug: Debug mode
    
    Returns:
        Default: List[str] - Simple list of items
        walk=True: List[Dict] - Hierarchical structure
        stat=True: Dict - Statistics summary
        walk+stat: List[Dict] - Full details
    
    Examples:
        # Simple list
        >>> list_operation(fmt="json", loc="base")
        ['config.json', 'user.json', 'data.json', 'tests/']
        
        >>> u.ljb()
        ['config.json', 'user.json', 'data.json', 'tests/']
        
        # Walk structure
        >>> u.ljb(walk=True)
        [
            {
                'path': 'data/json/base',
                'items': ['config.json', 'user.json', 'tests/']
            },
            {
                'path': 'data/json/base/tests',
                'items': ['test1.json', 'test2.json']
            }
        ]
        
        # With statistics
        >>> u.ljb(stat=True)
        {
            'files': ['config.json', 'user.json', 'data.json'],
            'dirs': ['tests/'],
            'total_files': 3,
            'total_dirs': 1,
            'total_size': 2048,
            'total_size_str': '2.0 KB'
        }
        
        # Full details
        >>> u.ljb(walk=True, stat=True)
        [
            {
                'path': 'data/json/base',
                'items': ['config.json', 'user.json', 'tests/'],
                'files': ['config.json', 'user.json'],
                'dirs': ['tests/'],
                'file_count': 2,
                'dir_count': 1,
                'size': 1024,
                'size_str': '1.0 KB'
            },
            {
                'path': 'data/json/base/tests',
                'items': ['test1.json', 'test2.json'],
                'files': ['test1.json', 'test2.json'],
                'dirs': [],
                'file_count': 2,
                'dir_count': 0,
                'size': 512,
                'size_str': '512 B'
            }
        ]
        
        # Other locations
        >>> u.ljs()  # sub
        >>> u.ljt()  # tmp
        >>> u.ljc()  # cache
        
        # Any format
        >>> u.lab()  # All formats
        >>> u.lab(mod="json")  # Only JSON
        
        # Custom directory
        >>> u.ljd(dir_path="/custom/path")
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_list(**kwargs)
    
    # Warn about future features
    warn_future_features(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Resolve Directory Path
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    base_path = get_smart_path(
        fmt=p["fmt"],
        filename=None,
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        cus=p["cus"],
        ensure_ext=False,
    )
    
    # Create directory if it doesn't exist
    if not base_path.exists():
        base_path.mkdir(parents=True, exist_ok=True)
    
    walk = p.get("walk", False)
    stat = p.get("stat", False)
    
    if p.get("debug"):
        print(f"[{p['fmt'].upper()}] Listing: {base_path}")
        print(f"[{p['fmt'].upper()}] walk={walk}, stat={stat}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Branch by walk
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # walk=False: Direct directory listing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not walk:
        # Shows all items including empty subdirectories
        
        if not stat:
            # Simple list
            result = _list_directory_simple(base_path)
            if p.get("debug"):
                print(f"[{p['fmt'].upper()}] Result: {len(result)} items")
            return result
        else:
            # With statistics
            result = _list_directory_stat(base_path)
            if p.get("debug"):
                print(f"[{p['fmt'].upper()}] Result: {result['total_files']} files, {result['total_dirs']} dirs")
            return result
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # walk=True: File-based listing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        # Uses find_data_search to get files
        # Only shows directories that contain files
        
        files = find_data_search(
            format_type=p["fmt"],
            mod=p.get("mod"),
            pattern="*",  # All files
            loc=p["loc"],
            user_dir=p.get("dir_path"),
            walk=True,  # Recursive search
            case_sensitive=False,
            debug=p.get("debug", False)
        )
        
        if p.get("debug"):
            print(f"[{p['fmt'].upper()}] Found {len(files)} files via find_data_search")
        
        # No files found
        if not files:
            if stat:
                return []
            else:
                return []
        
        if not stat:
            # Hierarchical structure
            result = _list_from_files_walk(files)
            if p.get("debug"):
                print(f"[{p['fmt'].upper()}] Result: {len(result)} directories")
            return result
        else:
            # Hierarchical structure with statistics
            result = _list_from_files_walk_stat(files)
            if p.get("debug"):
                print(f"[{p['fmt'].upper()}] Result: {len(result)} directories")
            return result


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["list_operation"]
