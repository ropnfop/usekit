# Path: usekit.classes.navi.base.load.ops.nbl_find.py
# -----------------------------------------------------------------------------------------------
#  Find Operation - File Search with Content Filtering
#  Created by: THE Little Prince × ROP × FOP
#  
#  Philosophy:
#  - Find = Read-Only subset of Update
#  - find_data_search: Get file candidates
#  - proc_read_data: Read file contents
#  - Filter by keydata/content (optional)
#  - walk=True by default (search everywhere)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, List, Dict, Union

from usekit.infra.navi_signature import params_for_find, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_search import find_data_search, detect_format_from_file
from usekit.classes.common.utils.helper_format import get_format_parser
from usekit.classes.common.utils.helper_keypath import resolve_key_path
from usekit.classes.data.base.load.sub.dbl_a_index_sub import proc_read_data


# ===============================================================================
# File Content Filtering
# ===============================================================================

def _filter_by_keydata(
    file_path: Path,
    p: dict
) -> bool:
    """
    Check if file matches keydata filter.
    
    Args:
        file_path: Path to file
        p: Parameters dict from params_for_find()
        
    Returns:
        True if file matches filter, False otherwise
    """
    try:
        # Detect format and read file
        fmt_actual = detect_format_from_file(file_path)
        fmt_actual = get_format_parser(fmt_actual)
        
        if not fmt_actual:
            return False
        
        # Cache location uses pkl
        if p["loc"] == "cache":
            fmt_actual = "pkl"
        
        # Read file content
        data = proc_read_data(fmt_actual, file_path)
        
        # Navigate to keydata path
        value = resolve_key_path(
            data,
            p["keydata"],
            default=None,
            recursive=p.get("recursive", False)
        )
        
        # Check if value exists
        if value is None:
            return False
        
        # If search value specified, check match
        if p.get("search_value") is not None:
            search_val = p["search_value"]
            
            # String contains check
            if isinstance(value, str) and isinstance(search_val, str):
                if p.get("case_sensitive", False):
                    return search_val in value
                else:
                    return search_val.lower() in value.lower()
            
            # Exact match
            return value == search_val
        
        # keydata exists (no specific value check)
        return True
        
    except Exception as e:
        if p.get("debug"):
            print(f"[FIND] Error filtering {file_path}: {e}")
        return False


def _filter_by_content(
    file_path: Path,
    search_text: str,
    case_sensitive: bool = False
) -> bool:
    """
    Check if file contains search text.
    
    Simple text search for any file type.
    
    Args:
        file_path: Path to file
        search_text: Text to search for
        case_sensitive: Case-sensitive search
        
    Returns:
        True if file contains text, False otherwise
    """
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        
        if case_sensitive:
            return search_text in content
        else:
            return search_text.lower() in content.lower()
            
    except Exception:
        return False


# ===============================================================================
# Main Find Operation
# ===============================================================================

@log_and_raise
def find_operation(**kwargs) -> Union[List[Path], List[Dict[str, Any]]]:
    """
    File search operation with optional content filtering.
    
    Philosophy:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    Find = Read-Only subset of Update
    - find_data_search: Get file candidates (by name/pattern)
    - proc_read_data: Read file contents (when filtering needed)
    - Filter by keydata or content (optional)
    - walk=True by default: Search everywhere
    
    Architecture:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. find_data_search: Get candidate files
    2. Optional filtering:
       - keydata: Filter by field value
       - content: Filter by text content
    3. Return file list or file list with values
    
    Flow:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Simple name search
    use.find.json.base("config")
      → find_data_search(pattern="config")
      → [config.json]
    
    # Pattern search
    use.find.json.base("user_*")
      → find_data_search(pattern="user_*")
      → [user_001.json, user_002.json, ...]
    
    # keydata filter
    use.find.json.base("user_*", keydata="email", search="gmail")
      → find_data_search(pattern="user_*")
      → filter by email field containing "gmail"
      → [user_001.json, user_005.json]
    
    # Content search
    use.find.txt.base("*.log", content="ERROR")
      → find_data_search(pattern="*.log")
      → filter by text containing "ERROR"
      → [app.log, error.log]
    
    Args:
        **kwargs: Common Navigation parameters
        
        # Core
        fmt: File format (json/yaml/txt/csv/any)
        name: Filename or pattern (wildcards: *, ?)
        loc: Location (base/sub/dir/now/tmp/cus/cache)
        
        # Format options
        mod: When fmt="any", specify format (default: all)
        
        # Search options
        walk: Recursive search (default: True)
        case_sensitive: Case-sensitive matching (default: False)
        
        # Content filtering
        keydata: Field path to check (e.g., "user/email")
        search: Value to search for in keydata field
        content: Text to search in file content
        
        # Output options
        with_values: Return file paths with keydata values (default: False)
        stat: Include file statistics (size, mtime, etc.) (default: False)
        
        # Parser options (for keydata filtering)
        recursive: Recursive keydata navigation
        tail_top: Read from top N lines (TXT)
        tail_bottom: Read from bottom N lines (TXT)
        regex: Use regex for TXT pattern matching
        
        debug: Debug mode
    
    Returns:
        List[Path]: List of matching file paths (default)
        List[Dict]: List of {path, value} dicts (if with_values=True)
        Empty list if no files found
    
    Examples:
        # Basic search
        >>> find_operation(fmt="json", name="config")
        [PosixPath('/path/config.json')]
        
        >>> u.fjb("config")
        [PosixPath('/path/config.json')]
        
        # Pattern search
        >>> u.fjb("user_*")
        [
            PosixPath('/path/user_001.json'),
            PosixPath('/path/user_002.json'),
            PosixPath('/path/user_123.json')
        ]
        
        # keydata filter
        >>> u.fjb("user_*", keydata="email", search="gmail")
        [
            PosixPath('/path/user_001.json'),  # email contains "gmail"
            PosixPath('/path/user_005.json')
        ]
        
        # keydata with values
        >>> u.fjb("user_*", keydata="email", with_values=True)
        [
            {"path": PosixPath(...), "value": "user1@example.com"},
            {"path": PosixPath(...), "value": "user2@gmail.com"}
        ]
        
        # With file statistics
        >>> u.fjb("user_*", stat=True)
        [
            {
                "path": PosixPath('/path/user_001.json'),
                "size": 1024,
                "size_str": "1.0 KB",
                "mtime": "2024-11-27 10:30:00",
                "ext": ".json"
            },
            {
                "path": PosixPath('/path/user_002.json'),
                "size": 2048,
                "size_str": "2.0 KB",
                "mtime": "2024-11-26 15:20:00",
                "ext": ".json"
            }
        ]
        
        # stat + keydata combination
        >>> u.fjb("config*", stat=True, keydata="version")
        [
            {
                "path": PosixPath(...),
                "size": 512,
                "size_str": "512.0 B",
                "mtime": "2024-11-27 10:30:00",
                "ext": ".json",
                "value": "1.0.0"
            }
        ]
        
        # Content search
        >>> u.ftb("*.log", content="ERROR")
        [
            PosixPath('/path/app.log'),
            PosixPath('/path/error.log')
        ]
        
        # TXT with tail
        >>> u.ftb("app.log", keydata="ERROR", tail_bottom=100)
        [PosixPath('/path/app.log')]  # If ERROR in last 100 lines
        
        # Any format
        >>> u.fab(mod="all", name="config")
        [
            PosixPath('/path/config.json'),
            PosixPath('/path/config.yaml'),
            PosixPath('/path/config.txt')
        ]
        
        # Specific format filter with keydata
        >>> u.fab(mod="json", name="*", keydata="api_key")
        [PosixPath(...)]  # Only JSON files with api_key field
        
        # Current level only
        >>> u.fjb("config", wk=False)
        [PosixPath('/path/config.json')]
        
        # Case-sensitive
        >>> u.fjb("Config", case_sensitive=True)
        [PosixPath('/path/Config.json')]
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] Extract Parameters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    p = params_for_find(**kwargs)
    
    # Warn about future features
    warn_future_features(p)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [2] Set Default: walk=True
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if "walk" not in kwargs:
        p["walk"] = True
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [3] Get Candidate Files
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not p.get("name"):
        raise ValueError(
            "[FIND] search pattern is required. "
            "Pass name='*', nm='*', or a glob pattern like 'test*'."
        )
    
    pattern = p.get("name", "*")
    
    files = find_data_search(
        format_type=p["fmt"],
        mod=p["mod"],
        pattern=pattern,
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        walk=p["walk"],
        case_sensitive=p.get("case_sensitive", False),
        debug=p.get("debug", False)
    )
    
    if p.get("debug"):
        print(f"[{p['fmt'].upper()}] Found {len(files)} candidate files")
    
    if not files:
        return []
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [4] Apply Content Filters
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Filter by content (simple text search)
    if p.get("content"):
        if p.get("debug"):
            print(f"[{p['fmt'].upper()}] Filtering by content: {p['content']}")
        
        files = [
            f for f in files
            if _filter_by_content(f, p["content"], p.get("case_sensitive", False))
        ]
        
        if p.get("debug"):
            print(f"[{p['fmt'].upper()}] After content filter: {len(files)} files")
    
    # Filter by keydata
    if p.get("keydata"):
        if p.get("debug"):
            search_info = f" = {p.get('search_value')}" if p.get("search_value") else ""
            print(f"[{p['fmt'].upper()}] Filtering by keydata: {p['keydata']}{search_info}")
        
        # Store search value in params
        p["search_value"] = p.get("search")
        
        filtered_files = []
        for f in files:
            if _filter_by_keydata(f, p):
                filtered_files.append(f)
        
        files = filtered_files
        
        if p.get("debug"):
            print(f"[{p['fmt'].upper()}] After keydata filter: {len(files)} files")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [5] Return Results
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Helper function for size formatting
    def format_size(size_bytes: int) -> str:
        """Convert bytes to human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    # Return with statistics
    if p.get("stat"):
        from datetime import datetime
        
        results = []
        for f in files:
            try:
                stat_info = f.stat()
                
                result = {
                    "path": f,
                    "size": stat_info.st_size,
                    "size_str": format_size(stat_info.st_size),
                    "mtime": datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "ext": f.suffix
                }
                
                # Add value if keydata was used
                if p.get("keydata"):
                    try:
                        fmt_actual = get_format_parser(detect_format_from_file(f))
                        if p["loc"] == "cache":
                            fmt_actual = "pkl"
                        
                        data = proc_read_data(fmt_actual, f)
                        value = resolve_key_path(
                            data,
                            p["keydata"],
                            default=None,
                            recursive=p.get("recursive", False)
                        )
                        result["value"] = value
                    except Exception:
                        pass
                
                results.append(result)
                
            except Exception as e:
                if p.get("debug"):
                    print(f"[{p['fmt'].upper()}] Error getting stats for {f}: {e}")
        
        return results
    
    # Return with values if requested
    if p.get("with_values") and p.get("keydata"):
        results = []
        for f in files:
            try:
                fmt_actual = get_format_parser(detect_format_from_file(f))
                if p["loc"] == "cache":
                    fmt_actual = "pkl"
                
                data = proc_read_data(fmt_actual, f)
                value = resolve_key_path(
                    data,
                    p["keydata"],
                    default=None,
                    recursive=p.get("recursive", False)
                )
                
                results.append({
                    "path": f,
                    "value": value
                })
            except Exception as e:
                if p.get("debug"):
                    print(f"[{p['fmt'].upper()}] Error reading {f}: {e}")
        
        return results
    
    # Return just file paths
    if p.get("debug") and files:
        print(f"[{p['fmt'].upper()}] Final result: {len(files)} files")
        if len(files) <= 10:
            for f in files:
                print(f"[{p['fmt'].upper()}]   - {f}")
    
    return files


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["find_operation"]
