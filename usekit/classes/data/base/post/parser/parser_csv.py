# Path: usekit.classes.data.base.post.parser.parser_csv.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready CSV parser with append/overwrite/safe modes
# Version: 2.0 - Added keydata search support with parser_csv_sub integration
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
import csv
from typing import Any, Union, Optional, List, Dict

# Import keydata helpers from sub module
from usekit.classes.data.base.post.sub.parser_csv_sub import (
    _extract_column,
    _has_column,
    _filter_rows_by_column,
    _match_value,
    _filter_rows_by_multiple_columns,
    _search_in_csv,
)

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_csv(path: Path, rows: List, encoding: str = "utf-8", **csv_kwargs) -> None:
    """
    Safe write: write to a temp file then atomically replace target.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding, newline=""
    ) as tmp:
        writer = csv.writer(tmp, **csv_kwargs)
        writer.writerows(rows)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(
    file,
    encoding: str = "utf-8",
    dialect: str = "excel",
    header: bool = True,
    keydata: Optional[str] = None,
    search_value: Any = None,
    key_type: Optional[str] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False,
    **kwargs
):
    """
    Read CSV from a file with optional keydata filtering.
    
    Basic Usage:
        data = load("users.csv")
        rows = load("data.csv", header=False)
    
    Column Extraction:
        emails = load("users.csv", keydata="email", key_type="column")
        # → ["alice@gmail.com", "bob@yahoo.com"]
        
        ages = load("users.csv", keydata="age", key_type="column")
        # → [30, 25, 35]
    
    Row Filtering:
        gmail_users = load("users.csv", keydata="email", search_value="gmail")
        # → [{"name": "Alice", "email": "alice@gmail.com", ...}]
        
        active = load("users.csv", keydata="status", search_value="active")
        # → All rows where status contains "active"
    
    Existence Check:
        has_gmail = load("users.csv", keydata="email", search_value="gmail", keydata_exists=True)
        # → True/False
    
    Args:
        file: File path or file-like object
        encoding: File encoding
        dialect: CSV dialect ('excel', 'unix', etc.)
        header: If True, return list of dicts with first row as keys
        
        keydata: Column name for filtering/extraction
        search_value: Value to match (optional)
        key_type: Operation type
            - "column": Extract column values
            - "row": Filter rows by condition
            - None: Auto-detect (column if no search_value, else row)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        keydata_exists: Return True/False instead of data (performance)
        
        **kwargs: Additional csv.reader options (delimiter, quotechar, etc.)
        
    Returns:
        - List[Dict]: if header=True and no keydata
        - List[List]: if header=False and no keydata
        - List[Any]: if key_type="column"
        - List[Dict]: if key_type="row"
        - bool: if keydata_exists=True
    
    Examples:
        >>> load("users.csv")
        [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        
        >>> load("users.csv", keydata="name", key_type="column")
        ["Alice", "Bob"]
        
        >>> load("users.csv", keydata="age", search_value=30)
        [{"name": "Alice", "age": 30}]
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding, newline="") as f:
            reader = csv.reader(f, dialect=dialect, **kwargs)
            rows = list(reader)
    else:
        reader = csv.reader(file, dialect=dialect, **kwargs)
        rows = list(reader)
    
    if not rows:
        return False if keydata_exists else []
    
    # Parse data
    if header:
        headers = rows[0]
        data = [dict(zip(headers, row)) for row in rows[1:]]
    else:
        data = rows
    
    # Apply keydata filtering if provided
    if keydata is not None:
        if not header:
            # Cannot use keydata without headers
            raise ValueError(
                "[csv.load] keydata requires header=True. "
                "CSV must have column names to filter by keydata."
            )
        
        return _search_in_csv(
            data,
            keydata=keydata,
            search_value=search_value,
            key_type=key_type,
            case_sensitive=case_sensitive,
            regex=regex,
            keydata_exists=keydata_exists
        )
    
    return data


def loads(
    text: str,
    dialect: str = "excel",
    header: bool = True,
    keydata: Optional[str] = None,
    search_value: Any = None,
    key_type: Optional[str] = None,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False,
    **kwargs
):
    """
    Parse CSV from string with optional keydata filtering.
    
    Basic Usage:
        data = loads("name,age\nAlice,30\nBob,25")
    
    Column Extraction:
        names = loads(csv_text, keydata="name", key_type="column")
    
    Row Filtering:
        filtered = loads(csv_text, keydata="age", search_value="30")
    
    Args:
        text: CSV text string
        dialect: CSV dialect
        header: If True, return list of dicts
        
        keydata: Column name for filtering/extraction
        search_value: Value to match (optional)
        key_type: Operation type ("column", "row", or None)
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        keydata_exists: Return True/False only
        
        **kwargs: Additional csv.reader options
        
    Returns:
        List of dicts if header=True, else list of lists
        (or filtered results if keydata provided)
    """
    lines = text.splitlines()
    reader = csv.reader(lines, dialect=dialect, **kwargs)
    rows = list(reader)
    
    if not rows:
        return False if keydata_exists else []
    
    # Parse data
    if header:
        headers = rows[0]
        data = [dict(zip(headers, row)) for row in rows[1:]]
    else:
        data = rows
    
    # Apply keydata filtering if provided
    if keydata is not None:
        if not header:
            raise ValueError(
                "[csv.loads] keydata requires header=True. "
                "CSV must have column names to filter by keydata."
            )
        
        return _search_in_csv(
            data,
            keydata=keydata,
            search_value=search_value,
            key_type=key_type,
            case_sensitive=case_sensitive,
            regex=regex,
            keydata_exists=keydata_exists
        )
    
    return data


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Union[List[List], List[Dict]],
    file,
    *,
    # formatting
    encoding: str = "utf-8",
    dialect: str = "excel",
    # behavior
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    header: Optional[List[str]] = None,
    # extra kwargs
    **kwargs
) -> None:
    """
    Write CSV to file.
    
    Modes:
        overwrite=False : raise if file exists
        safe=True       : atomic write (temp file -> replace)
        append=True     : append to existing file
    
    Args:
        data: List of lists or list of dicts
        file: File path or file-like object
        encoding: File encoding
        dialect: CSV dialect
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Append to existing file
        header: Custom header row (auto-detected from dicts if None)
        **kwargs: Additional csv.writer options (delimiter, quotechar, etc.)
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)
    
    # Normalize data to list of lists
    rows = []
    if data and isinstance(data[0], dict):
        # List of dicts
        if header is None:
            header = list(data[0].keys())
        if not append or (path_obj and not path_obj.exists()):
            rows.append(header)
        rows.extend([list(row.values()) for row in data])
    else:
        # List of lists
        if header is not None and (not append or (path_obj and not path_obj.exists())):
            rows.append(header)
        rows.extend(data)
    
    # ── Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding, newline="") as f:
                writer = csv.writer(f, dialect=dialect, **kwargs)
                writer.writerows(rows)
        else:
            writer = csv.writer(file, dialect=dialect, **kwargs)
            writer.writerows(rows)
        return
    
    # ── Normal write mode
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[csv.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            # Atomic write
            _atomic_write_csv(path_obj, rows, encoding=encoding, dialect=dialect, **kwargs)
        else:
            # Direct write
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding, newline="") as f:
                writer = csv.writer(f, dialect=dialect, **kwargs)
                writer.writerows(rows)
        return
    
    # file-like object
    writer = csv.writer(file, dialect=dialect, **kwargs)
    writer.writerows(rows)


def dumps(
    data: Union[List[List], List[Dict]],
    *,
    dialect: str = "excel",
    header: Optional[List[str]] = None,
    **kwargs
) -> str:
    """
    Serialize to CSV string.
    
    Args:
        data: List of lists or list of dicts
        dialect: CSV dialect
        header: Custom header row
        **kwargs: Additional csv.writer options
        
    Returns:
        CSV string
    """
    import io
    output = io.StringIO()
    
    # Normalize data
    rows = []
    if data and isinstance(data[0], dict):
        if header is None:
            header = list(data[0].keys())
        rows.append(header)
        rows.extend([list(row.values()) for row in data])
    else:
        if header is not None:
            rows.append(header)
        rows.extend(data)
    
    writer = csv.writer(output, dialect=dialect, **kwargs)
    writer.writerows(rows)
    return output.getvalue()


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.csv"):
    """Test CSV parser functionality."""
    
    # Write list of dicts
    data = [
        {"name": "Alice", "age": "30", "city": "Seoul"},
        {"name": "Bob", "age": "25", "city": "Busan"}
    ]
    dump(data, base)
    print("[CSV] wrote dicts:", base)
    
    # Read with header
    content = load(base)
    print("[CSV] read:", content)
    
    # Append
    dump([{"name": "Charlie", "age": "35", "city": "Jeju"}], base, append=True)
    print("[CSV] appended:", load(base))
    
    # Write list of lists
    rows = [["x", "y"], [1, 2], [3, 4]]
    dump(rows, "coords.csv", header=None)
    print("[CSV] wrote lists:", load("coords.csv", header=False))
    
    # dumps test
    csv_str = dumps(data)
    print("[CSV] dumps:\n", csv_str)
    
    # loads test
    parsed = loads(csv_str)
    print("[CSV] loads:", parsed)

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------