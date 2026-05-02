# Path: usekit.classes.data.base.post.sub.parser_txt_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for TXT parser sub
# Features:
#   - Path utilities: atomic writes, path handling
#   - Data utilities: type wrapping, conversion
#   - Tail operations: mode detection, line cutting
#   - Search operations: grep-like functionality
#   - Replace operations: sed-like functionality
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
import re
import warnings
from typing import Any, Union, Optional, List, Tuple


# ===============================================================================
# Constants
# ===============================================================================

DEFAULT_TAIL_VALUES = {
    "tail_all": None,   # None = show all lines
    "tail_top": 10,
    "tail_mid": 10,
    "tail_bottom": 10,
}


# ===============================================================================
# Path & I/O Utilities
# ===============================================================================

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Safe write: write to a temp file then atomically replace target.
    Works across most POSIX-like filesystems (and is fine on Colab).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


# ===============================================================================
# Data Conversion Utilities
# ===============================================================================

def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """Auto-wrap non-string values if needed."""
    if not wrap:
        return data
    
    # Convert to string if not already
    if not isinstance(data, str):
        if isinstance(data, (dict, list)):
            # For complex types, use repr for readability
            return repr(data)
        else:
            return str(data)
    
    return data


# ===============================================================================
# Tail Mode Detection & Operations
# ===============================================================================

def _detect_tail_mode(**kwargs) -> tuple[str, dict]:
    """
    Auto-detect tail mode from provided options.
    Upper wrapper already resolved aliases - we only receive full names.
    
    Returns:
        (tail_mode, filtered_opts)
    """
    
    # Collect tail_* options
    tail_opts = {
        k: v for k, v in kwargs.items()
        if k.startswith("tail_") and isinstance(v, int) and v > 0
    }
    
    # Auto-detect mode (first wins)
    tail_mode = None
    for mode in ("tail_all", "tail_top", "tail_mid", "tail_bottom"):
        if mode in tail_opts:
            tail_mode = mode
            break
    
    # Default: tail_all (show all)
    if tail_mode is None:
        tail_mode = "tail_all"
    
    return tail_mode, tail_opts


def _apply_tail_cut(
    lines: List[str],
    tail_mode: str,
    opts: dict,
    warn_large: bool = True
) -> Tuple[List[str], int, int]:
    """
    Apply tail-style line cutting.
    
    Returns:
        (cut_lines, start_index, end_index)
        - Indices are needed for replace to update correct lines
    """
    
    if not lines:
        return [], 0, 0
    
    size = len(lines)
    
    # Get values with defaults
    all_n = opts.get("tail_all", size)
    top_n = opts.get("tail_top", DEFAULT_TAIL_VALUES["tail_top"])
    mid_n = opts.get("tail_mid", DEFAULT_TAIL_VALUES["tail_mid"])
    bot_n = opts.get("tail_bottom", DEFAULT_TAIL_VALUES["tail_bottom"])
    
    # Validation
    for name, val in [("all", all_n), ("top", top_n), ("mid", mid_n), ("bot", bot_n)]:
        if val < 0:
            raise ValueError(f"tail_{name} must be non-negative, got {val}")
        # if warn_large and val > size * 2:
        #   warnings.warn(f"tail_{name}={val} exceeds file size ({size})")
    
    # Apply mode and track indices
    if tail_mode == "tail_top":
        end = min(top_n, size)
        return lines[:end], 0, end
    
    if tail_mode == "tail_mid":
        mid = size // 2
        half_before = mid_n // 2
        half_after = mid_n - half_before
        start = max(0, mid - half_before)
        end = min(size, mid + half_after)
        return lines[start:end], start, end
    
    if tail_mode == "tail_bottom":
        start = max(0, size - bot_n)
        return lines[start:], start, size
    
    # tail_all (default)
    end = min(all_n, size) if all_n else size
    return lines[:end], 0, end


# ===============================================================================
# Search Operations
# ===============================================================================

def _search_keydata(
    lines: List[str],
    keydata: str,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    keydata_exists: bool = False
) -> Union[List[str], bool]:
    """
    Search lines for keydata pattern (grep-like functionality).
    
    Args:
        lines: List of text lines to search
        keydata: Search pattern (string or regex)
        regex: Treat keydata as regular expression
        case_sensitive: Case-sensitive matching
        invert_match: Return lines that do NOT match
        keydata_exists: Return True/False instead of matched lines (performance optimization)
    
    Returns:
        List of matching lines or bool (if keydata_exists=True)
    """
    
    if not keydata:
        return lines if not keydata_exists else True
    
    # Regex mode
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(keydata, flags)
            
            if keydata_exists:
                # Early return for existence check
                for ln in lines:
                    if pattern.search(ln):
                        return not invert_match
                return invert_match
            else:
                matches = [ln for ln in lines if pattern.search(ln)]
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{keydata}': {e}")
    else:
        # Simple substring search
        if keydata_exists:
            # Early return for existence check
            if case_sensitive:
                for ln in lines:
                    if keydata in ln:
                        return not invert_match
            else:
                kd_lower = keydata.lower()
                for ln in lines:
                    if kd_lower in ln.lower():
                        return not invert_match
            return invert_match
        else:
            if case_sensitive:
                matches = [ln for ln in lines if keydata in ln]
            else:
                kd_lower = keydata.lower()
                matches = [ln for ln in lines if kd_lower in ln.lower()]
    
    # Invert match (only when not keydata_exists mode)
    if invert_match:
        matches = [ln for ln in lines if ln not in matches]
    
    return matches


# ===============================================================================
# Replace Operations
# ===============================================================================

def _replace_in_lines(
    lines: List[str],
    keydata: str,
    data: str,
    regex: bool = False,
    case_sensitive: bool = False,
    replace_all: bool = True,
    max_count: Optional[int] = None
) -> Tuple[List[str], int]:
    """
    Replace keydata with data in lines (sed-like functionality).
    
    Args:
        lines: List of text lines
        keydata: Pattern to search for (old value)
        data: Replacement string (new value)
        regex: Use regex for keydata
        case_sensitive: Case-sensitive matching
        replace_all: Replace all occurrences (False = first only)
        max_count: Maximum number of replacements (None = unlimited)
    
    Returns:
        (modified_lines, replacement_count)
    """
    
    if not keydata:
        return lines, 0
    
    result = []
    count = 0
    max_reached = False
    
    # Regex mode
    if regex:
        flags = 0 if case_sensitive else re.IGNORECASE
        try:
            pattern = re.compile(keydata, flags)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{keydata}': {e}")
        
        for line in lines:
            if max_count and count >= max_count:
                result.append(line)
                continue
            
            if replace_all:
                new_line, n = pattern.subn(data, line)
            else:
                new_line, n = pattern.subn(data, line, count=1)
            
            result.append(new_line)
            count += n
            
            if not replace_all and n > 0:
                max_reached = True
            
            if max_reached:
                result.extend(lines[len(result):])
                break
    
    # Simple string mode
    else:
        for line in lines:
            if max_count and count >= max_count:
                result.append(line)
                continue
            
            if case_sensitive:
                match = keydata in line
            else:
                match = keydata.lower() in line.lower()
            
            if not match:
                result.append(line)
                continue
            
            # Perform replacement
            if replace_all:
                if case_sensitive:
                    new_line = line.replace(keydata, data)
                    n = line.count(keydata)
                else:
                    # Case-insensitive replace (preserve original case boundaries)
                    pattern = re.compile(re.escape(keydata), re.IGNORECASE)
                    new_line = pattern.sub(data, line)
                    n = len(pattern.findall(line))
            else:
                # Replace first occurrence only
                if case_sensitive:
                    new_line = line.replace(keydata, data, 1)
                    n = 1 if keydata in line else 0
                else:
                    pattern = re.compile(re.escape(keydata), re.IGNORECASE)
                    new_line = pattern.sub(data, line, count=1)
                    n = 1 if pattern.search(line) else 0
                
                max_reached = True
            
            result.append(new_line)
            count += n
            
            if max_reached:
                result.extend(lines[len(result):])
                break
    
    return result, count


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "DEFAULT_TAIL_VALUES",
    "_atomic_write_text",
    "_ensure_path",
    "_wrap_if_needed",
    "_detect_tail_mode",
    "_apply_tail_cut",
    "_search_keydata",
    "_replace_in_lines",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
