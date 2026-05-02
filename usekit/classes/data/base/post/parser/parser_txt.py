# Path: usekit.classes.data.base.post.parser.parser_txt.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready TXT parser with comprehensive text processing capabilities
# Features:
#   - Basic I/O: load/loads/dump/dumps with atomic writes
#   - Advanced search: grep-like with regex support
#   - Tail operations: head/tail/mid viewing modes
#   - Replace: sed-like in-place text replacement
#   - Safe writes: atomic operations, append modes
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Union, Optional, TextIO

# Import all helper functions from sub module
from usekit.classes.data.base.post.sub.parser_txt_sub import (
    DEFAULT_TAIL_VALUES,
    _atomic_write_text,
    _ensure_path,
    _wrap_if_needed,
    _detect_tail_mode,
    _apply_tail_cut,
    _search_keydata,
    _replace_in_lines,
)


# ===============================================================================
# Main Interface Functions
# ===============================================================================

def load(
    file: Union[str, Path, TextIO],
    *,
    encoding: str = "utf-8",
    lines: bool = False,
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    line_numbers: bool = False,
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
) -> Union[str, list]:
    """
    Load text file with comprehensive Unix-like text operations.
    
    Basic Usage:
        content = load("file.txt")                      # Read all content
        lines = load("file.txt", lines=True)            # Read as list
    
    Search (grep-like):
        result = load("file.txt", keydata="ERROR")                  # Search lines
        result = load("file.txt", keydata="^ERROR", regex=True)     # Regex search
        result = load("file.txt", keydata="ERROR", invert_match=True)  # Invert match
        result = load("file.txt", keydata="ERROR", line_numbers=True)  # Show line numbers
    
    Tail Operations:
        content = load("file.txt", tail_top=10)         # First 10 lines (like head)
        content = load("file.txt", tail_bottom=10)      # Last 10 lines (like tail)
        content = load("file.txt", tail_mid=20)         # 20 lines around middle
        content = load("file.txt", tail_all=100)        # First 100 lines
    
    Combined Operations:
        result = load("file.txt", 
                     keydata="ERROR",
                     tail_bottom=100,
                     line_numbers=True)  # Search ERROR in last 100 lines
    
    Args:
        file: File path or file-like object
        
        encoding: File encoding
        lines: Return as list of lines instead of single string
        
        keydata: Search pattern (enables grep-like search)
        regex: Treat keydata as regular expression
        case_sensitive: Case-sensitive matching
        invert_match: Return lines that do NOT match keydata
        line_numbers: Prefix each line with line number
        
        tail_all: Show first N lines (None = all)
        tail_top: Show first N lines (like head)
        tail_mid: Show N lines around middle
        tail_bottom: Show last N lines (like tail)
        
    Returns:
        String or list of lines
    """
    
    # Read content
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file}")
        with path.open("r", encoding=encoding) as f:
            content = f.read()
    else:
        # file-like object
        file.seek(0)
        content = file.read()
    
    # Process as lines
    result_lines = content.splitlines()
    
    # Detect and apply tail mode
    tail_mode, tail_opts = _detect_tail_mode(
        tail_all=tail_all,
        tail_top=tail_top,
        tail_mid=tail_mid,
        tail_bottom=tail_bottom
    )
    
    result_lines, _, _ = _apply_tail_cut(result_lines, tail_mode, tail_opts)
    
    # Apply search if keydata provided
    if keydata:
        result_lines = _search_keydata(
            result_lines, keydata,
            regex, case_sensitive, invert_match
        )
    
    # Add line numbers if requested
    if line_numbers:
        width = len(str(len(result_lines)))
        result_lines = [
            f"{i+1:>{width}}: {line}"
            for i, line in enumerate(result_lines)
        ]
    
    # Return format
    if lines:
        return result_lines
    
    return "\n".join(result_lines)


def loads(
    data: str,
    *,
    lines: bool = False,
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    line_numbers: bool = False,
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
) -> Union[str, list]:
    """
    Parse string with Unix-like text operations (in-memory version of load).
    
    Basic Usage:
        content = loads(text)                           # Return as-is
        lines = loads(text, lines=True)                 # Split to list
    
    Search:
        result = loads(text, keydata="ERROR")           # Search lines
        result = loads(text, keydata="^ERROR", regex=True)  # Regex search
    
    Tail:
        result = loads(text, tail_top=10)               # First 10 lines
        result = loads(text, tail_bottom=10)            # Last 10 lines
    
    Args:
        data: Text string to process
        
        lines: Return as list of lines
        
        keydata: Search pattern
        regex: Use regex for keydata
        case_sensitive: Case-sensitive matching
        invert_match: Invert match
        line_numbers: Show line numbers
        
        tail_all/tail_top/tail_mid/tail_bottom: Line range selection
        
    Returns:
        String or list of lines
    """
    
    # Process as lines
    result_lines = data.splitlines()
    
    # Detect and apply tail mode
    tail_mode, tail_opts = _detect_tail_mode(
        tail_all=tail_all,
        tail_top=tail_top,
        tail_mid=tail_mid,
        tail_bottom=tail_bottom
    )
    
    result_lines, _, _ = _apply_tail_cut(result_lines, tail_mode, tail_opts)
    
    # Apply search if keydata provided
    if keydata:
        result_lines = _search_keydata(
            result_lines, keydata,
            regex, case_sensitive, invert_match
        )
    
    # Add line numbers if requested
    if line_numbers:
        width = len(str(len(result_lines)))
        result_lines = [
            f"{i+1:>{width}}: {line}"
            for i, line in enumerate(result_lines)
        ]
    
    # Return format
    if lines:
        return result_lines
    
    return "\n".join(result_lines)


def dump(
    data: Any,
    file: Union[str, Path, TextIO],
    *,
    encoding: str = "utf-8",
    newline: Optional[str] = None,
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,
    keydata: Optional[str] = None,
    regex: bool = False,
    case_sensitive: bool = False,
    replace_all: bool = True,
    max_count: Optional[int] = None,
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    **kwargs
) -> Optional[int]:
    """
    Write text to file with Unix-like operations.
    
    Basic Usage:
        dump("content", "file.txt")                    # Write (atomic by default)
        dump("content", "file.txt", overwrite=False)   # Fail if exists
        dump("content", "file.txt", safe=False)        # Fast write (no atomic)
        dump("content", "file.txt", append=True)       # Append to file
        dump("content", "file.txt", append=True, append_newline=False)  # Append without newline
    
    Replace Mode (sed-like):
        count = dump("new", "file.txt", keydata="old")                    # Replace all "old" with "new"
        count = dump("new", "file.txt", keydata="old", replace_all=False) # Replace first only
        count = dump("new", "file.txt", keydata="old", max_count=5)       # Replace max 5
        count = dump("new", "file.txt", keydata="^ERROR", regex=True)     # Regex replace
    
    Scoped Replace:
        count = dump("FIXED", "file.txt", 
                    keydata="ERROR",
                    tail_bottom=100)  # Replace only in last 100 lines
    
    Data Conversion:
        dump({"key": "val"}, "file.txt", wrap=True)  # Auto-convert dict to string
        dump(12345, "file.txt", wrap=True)           # Auto-convert number to string
    
    Args:
        data: Data to write (or replacement string if keydata provided)
        file: File path or file-like object
        
        encoding: File encoding
        newline: Newline mode (None=platform, ''=no conversion, '\n'=Unix, '\r\n'=Windows)
        
        wrap: Auto-convert non-strings to string
        overwrite: Allow overwriting existing file
        safe: Use atomic write (temp file + replace)
        append: Append to existing file
        append_newline: Add newline before appending
        
        keydata: Pattern to search and replace (enables replace mode)
        regex: Use regex for keydata
        case_sensitive: Case-sensitive matching
        replace_all: Replace all occurrences (False = first only)
        max_count: Maximum replacements (None = unlimited)
        
        tail_*: Limit replacement scope to specific area
        
    Returns:
        None (normal write/append) or int (replacement count in replace mode)
    """
    
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Convert data to string
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    
    # ── Replace mode (keydata provided)
    if keydata:
        # Read existing content
        if path_obj:
            if not path_obj.exists():
                raise FileNotFoundError(f"Replace mode requires existing file: {path_obj}")
            with path_obj.open("r", encoding=encoding) as f:
                content = f.read()
        else:
            file.seek(0)
            content = file.read()
        
        lines = content.splitlines()
        
        # Detect tail mode
        tail_mode, tail_opts = _detect_tail_mode(
            tail_all=tail_all,
            tail_top=tail_top,
            tail_mid=tail_mid,
            tail_bottom=tail_bottom
        )
        
        # Apply tail cut to get scope + indices
        area, start_idx, end_idx = _apply_tail_cut(lines, tail_mode, tail_opts)
        
        # Replace in scoped area
        modified_area, count = _replace_in_lines(
            area, keydata, data,
            regex, case_sensitive,
            replace_all, max_count
        )
        
        # Reconstruct full content
        result_lines = lines[:start_idx] + modified_area + lines[end_idx:]
        result_text = "\n".join(result_lines)
        
        # Write back
        if path_obj:
            if safe:
                _atomic_write_text(path_obj, result_text, encoding=encoding)
            else:
                with path_obj.open("w", encoding=encoding, newline=newline) as f:
                    f.write(result_text)
        else:
            file.seek(0)
            file.truncate()
            file.write(result_text)
        
        return count
    
    # ── Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding, newline=newline) as f:
                if append_newline and path_obj.stat().st_size > 0:
                    # Add newline if file is not empty
                    if not data.startswith('\n'):
                        f.write('\n')
                f.write(data)
        else:
            # file-like object
            if append_newline:
                file.write('\n')
            file.write(data)
        return None
    
    # ── Normal write mode
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[txt.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            # Atomic write
            _atomic_write_text(path_obj, data, encoding=encoding)
        else:
            # Direct write
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline=newline) as f:
                f.write(data)
        return None
    
    # file-like object
    file.write(data)
    return None


def dumps(
    data: Any,
    *,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to string (for API consistency).
    
    Args:
        data: Data to convert to string
        wrap: Auto-convert non-strings
        
    Returns:
        String representation
    """
    data = _wrap_if_needed(data, wrap)
    if not isinstance(data, str):
        data = str(data)
    return data


# ===============================================================================
# Test Helper
# ===============================================================================

def _test(base="sample.txt"):
    """Test TXT parser functionality."""
    from pathlib import Path
    
    print("\n=== Basic I/O Tests ===")
    
    # 1) Simple write
    dump("Hello ROP\nLine 2\nLine 3", base)
    print(f"[1] Wrote basic content to {base}")
    
    # 2) Read
    content = load(base)
    print(f"[2] Read: {repr(content)}")
    
    # 3) Read as lines
    lines = load(base, lines=True)
    print(f"[3] Lines: {lines}")
    
    # 4) Append
    dump("Line 4", base, append=True, append_newline=True)
    print(f"[4] Appended line 4")
    
    print("\n=== Advanced Features Tests ===")
    
    # 5) Search
    result = load(base, keydata="Line", line_numbers=True)
    print(f"[5] Search 'Line':\n{result}")
    
    # 6) Tail operations
    dump("Line 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10", base, append=True)
    top3 = load(base, tail_top=3)
    print(f"[6] First 3 lines:\n{top3}")
    
    bot3 = load(base, tail_bottom=3)
    print(f"[6] Last 3 lines:\n{bot3}")
    
    # 7) Replace
    count = dump("MODIFIED", base, keydata="Line 2", replace_all=True)
    print(f"[7] Replaced 'Line 2' -> 'MODIFIED': {count} replacements")
    print(f"    Content: {load(base)}")
    
    # 8) Regex replace
    dump("test line 1\ntest line 2\nother line", base)
    count = dump("REPLACED", base, keydata="^test", regex=True, replace_all=True)
    print(f"[8] Regex replace '^test': {count} replacements")
    print(f"    Content: {load(base)}")
    
    # 9) Scoped replace (tail_bottom)
    dump("\n".join([f"Line {i}" for i in range(1, 21)]), base)
    count = dump("FIXED", base, keydata="Line", tail_bottom=5, replace_all=True)
    print(f"[9] Scoped replace (last 5 lines): {count} replacements")
    print(f"    Last 5 lines: {load(base, tail_bottom=5)}")
    
    # 10) Complex operation
    dump("\n".join([f"ERROR: Issue {i}" for i in range(1, 11)]), base)
    result = load(base, keydata="ERROR", regex=True, tail_top=5, line_numbers=True)
    print(f"[10] Search 'ERROR' in first 5 lines:\n{result}")
    
    print("\n=== Cleanup ===")
    Path(base).unlink(missing_ok=True)
    print(f"Removed {base}")


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "load",
    "loads",
    "dump", 
    "dumps",
    "DEFAULT_TAIL_VALUES",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
