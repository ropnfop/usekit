# Path: usekit.classes.data.base.post.parser.parser_json.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready JSON parser with auto-wrap, append/overwrite/safe modes
# Version: 2.2 - Added keydata search support with parser_json_sub integration
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import json
import tempfile
import os
from typing import Any, Union, Iterable, Optional, List

# Import keydata helpers from sub module
from usekit.classes.data.base.post.sub.parser_json_sub import (
    _search_keydata_in_json,
    _has_keydata_value,
    _match_value,
    _filter_json_list_by_keydata,
    _extract_keydata_values,
)

# print("[DEBUG] >>> JSON parser activated")

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────
def _serialize_json(
    data: Any,
    ensure_ascii: bool,
    sort_keys: bool,
    indent: int,
    separators,
    **kwargs
) -> str:
    return json.dumps(
        data,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        indent=indent,
        separators=separators,
        **kwargs
    )

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Safe write: write to a temp file then atomically replace target.
    Works across most POSIX-like filesystems (and is fine on Colab).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent), encoding=encoding) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

def _try_parse_jsonl(text: str) -> Iterable[Any]:
    """
    Try to parse text as JSON Lines (one JSON per line).
    Returns list of parsed objects if successful, else raises ValueError.
    """
    lines = [ln for ln in text.splitlines() if ln.strip()]
    items = []
    for ln in lines:
        try:
            items.append(json.loads(ln))
        except json.JSONDecodeError as e:
            raise ValueError(f"Not JSONL: line failed to parse → {e}") from e
    return items

def _ensure_path(file: Union[str, Path]) -> Path:
    return file if isinstance(file, Path) else Path(file)

def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """
    Auto-wrap simple values for JSON serialization.
    
    This is a JSON-specific convenience feature that transforms
    simple inputs into valid JSON structures.
    
    Rules (when wrap=True):
    ────────────────────────────────────────────────────────────
    1. JSON string → parsed to dict/list
       '{"a":1}' → {"a": 1}
       '[1,2,3]' → [1, 2, 3]
    
    2. String with colon → key-value dict
       "name:Alice" → {"name": "Alice"}
    
    3. Primitive types → wrapped in dict
       123 → {"value": 123}
       True → {"value": True}
       "plain text" → {"value": "plain text"}
    
    4. Already dict/list → unchanged
       {"key": "val"} → {"key": "val"}
       [1, 2, 3] → [1, 2, 3]
    
    When wrap=False:
    ────────────────────────────────────────────────────────────
    Returns data as-is, no transformation.
    
    Args:
        data: Input data to potentially wrap
        wrap: If True, apply wrapping rules; if False, return as-is
    
    Returns:
        Wrapped or original data based on rules above
    
    Examples:
        >>> _wrap_if_needed("name:Alice", wrap=True)
        {"name": "Alice"}
        
        >>> _wrap_if_needed(42, wrap=True)
        {"value": 42}
        
        >>> _wrap_if_needed({"existing": "dict"}, wrap=True)
        {"existing": "dict"}
        
        >>> _wrap_if_needed('{"a":1}', wrap=True)
        {"a": 1}
        
        >>> _wrap_if_needed("plain text", wrap=False)
        "plain text"
        
    Use Cases:
        ✅ Quick writes: u.wj(data="status:active", wrap=True)
        ✅ CLI inputs: echo "name:Alice" | python script.py
        ✅ Simple values: u.wj(data=123, wrap=True) → saves as JSON
        ✅ JSON strings: u.wj(data='{"key":"val"}', wrap=True) → parses and saves
        ❌ Disable when: Working with pre-formatted JSON structures
    """
    if not wrap:
        return data
    
    # Try to parse JSON string first
    if isinstance(data, str):
        # Check if it looks like JSON (starts with { or [)
        stripped = data.strip()
        if stripped and stripped[0] in ('{', '['):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, ValueError):
                return {"_invalid": data}               
        
        # String with colon → key:value pair
        if ":" in data and not stripped.startswith(('{', '[')):
            key, value = map(str.strip, data.split(":", 1))
            return {key: value}
    
    # Primitive (not dict/list) → wrap in dict
    if not isinstance(data, (dict, list)):
        return {"value": data}
    
    # Already dict/list → no wrap needed
    return data

# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────
def load(
    file, 
    encoding: str = "utf-8", 
    jsonl: bool = False,
    keydata: Optional[str] = None,
    search_value: Any = None,
    recursive: bool = False,
    find_all: bool = False,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False,
    **kwargs
):
    """
    Read JSON (or JSONL if jsonl=True) from a file with optional keydata filtering.
    
    Basic Usage:
        data = load("config.json")
        data = load("data.jsonl", jsonl=True)
    
    Keydata Navigation:
        value = load("config.json", keydata="user/email")
        value = load("config.json", keydata="items[0]/id")
        exists = load("config.json", keydata="user/email", keydata_exists=True)
    
    Keydata Search:
        data = load("users.json", keydata="email", search_value="gmail")
        data = load("users.json", keydata="status", search_value="active")
        values = load("config.json", keydata="version", recursive=True, find_all=True)
    
    Args:
        file: File path (str/Path) or file-like object
        encoding: Text encoding (default: utf-8)
        jsonl: JSON Lines mode
            - False: standard JSON (object/array)
            - True: JSON Lines; returns list[object]
            - 'auto': try JSON first, fall back to JSONL on failure
        
        keydata: Key path for navigation/filtering (e.g., "user/email", "items[0]")
        search_value: Value to match (optional, for filtering)
        recursive: Search recursively through structure
        find_all: Return all matches (when recursive=True)
        case_sensitive: Case-sensitive value matching
        regex: Use regex for value matching
        keydata_exists: Return True/False instead of values (performance)
        
        **kwargs: Additional json.loads options
    
    Returns:
        Parsed JSON data (dict/list/primitive), filtered by keydata if provided
    
    Examples:
        >>> load("config.json")
        {"key": "value"}
        
        >>> load("data.jsonl", jsonl=True)
        [{"line": 1}, {"line": 2}]
        
        >>> load("config.json", keydata="database/host")
        "localhost"
        
        >>> load("users.json", keydata="email", search_value="gmail", recursive=True)
        "user@gmail.com"
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()

    # Parse JSON
    # Filter out keydata-related parameters before passing to json.loads()
    json_kwargs = {k: v for k, v in kwargs.items() 
                   if k not in ('keydata', 'search_value', 'keydata_exists', 
                                'recursive', 'find_all', 'case_sensitive', 'regex')}
    
    if jsonl is True:
        data = list(_try_parse_jsonl(text))
    elif jsonl == "auto":
        try:
            data = json.loads(text, **json_kwargs)
        except json.JSONDecodeError:
            data = list(_try_parse_jsonl(text))
    else:
        # default JSON
        data = json.loads(text, **json_kwargs)
    
    # Apply keydata filtering if provided
    if keydata is not None:
        return _search_keydata_in_json(
            data,
            keydata=keydata,
            search_value=search_value,
            keydata_exists=keydata_exists,
            recursive=recursive,
            find_all=find_all,
            case_sensitive=case_sensitive,
            regex=regex
        )
    
    return data

def loads(
    text: str, 
    jsonl: bool = False,
    keydata: Optional[str] = None,
    search_value: Any = None,
    recursive: bool = False,
    find_all: bool = False,
    case_sensitive: bool = False,
    regex: bool = False,
    keydata_exists: bool = False,
    **kwargs
):
    """
    Parse from string with optional keydata filtering.
    
    Basic Usage:
        data = loads('{"key": "value"}')
        lines = loads('{"a":1}\n{"b":2}', jsonl=True)
    
    Keydata Navigation:
        value = loads('{"user": {"email": "test@example.com"}}', keydata="user/email")
        exists = loads('{"config": {"debug": true}}', keydata="config/debug", keydata_exists=True)
    
    Args:
        text: JSON string to parse
        jsonl: JSON Lines mode
            - False: standard JSON
            - True: parse as JSON Lines (returns list)
            - 'auto': try JSON then JSONL
        
        keydata: Key path for navigation/filtering
        search_value: Value to match (optional)
        recursive: Search recursively
        find_all: Return all matches
        case_sensitive: Case-sensitive matching
        regex: Use regex for matching
        keydata_exists: Return True/False only
        
        **kwargs: Additional json.loads options
    
    Returns:
        Parsed JSON data, filtered by keydata if provided
    """
    # Filter out keydata-related parameters before passing to json.loads()
    json_kwargs = {k: v for k, v in kwargs.items() 
                   if k not in ('keydata', 'search_value', 'keydata_exists', 
                                'recursive', 'find_all', 'case_sensitive', 'regex')}
    
    # Parse JSON
    if jsonl is True:
        data = list(_try_parse_jsonl(text))
    elif jsonl == "auto":
        try:
            data = json.loads(text, **json_kwargs)
        except json.JSONDecodeError:
            data = list(_try_parse_jsonl(text))
    else:
        data = json.loads(text, **json_kwargs)
    
    # Apply keydata filtering if provided
    if keydata is not None:
        return _search_keydata_in_json(
            data,
            keydata=keydata,
            search_value=search_value,
            keydata_exists=keydata_exists,
            recursive=recursive,
            find_all=find_all,
            case_sensitive=case_sensitive,
            regex=regex
        )
    
    return data

# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────
def dump(
    data: Any,
    file,
    *,
    # formatting
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    separators = None,
    encoding: str = "utf-8",
    # behavior
    wrap: bool = True,  # ✅ Changed default to True for convenience
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_mode: str = "auto",  # 'auto' | 'array' | 'object' | 'jsonl'
    # extra kwargs passed to json.dump
    **kwargs
) -> None:
    """
    Write JSON to file with auto-wrap support.

    Features:
    ─────────────────────────────────────────────────────────────
    ✅ Auto-wrap: Simple values → JSON structures (wrap=True)
    ✅ Atomic writes: Safe file replacement (safe=True)
    ✅ Append modes: array/object/jsonl
    ✅ Pretty printing: Customizable indentation

    Args:
        data: Data to serialize
        file: File path (str/Path) or file-like object
        
        Formatting:
        ───────────────────────────────────────────────────────
        ensure_ascii: Escape non-ASCII characters (default: False)
        sort_keys: Sort dictionary keys (default: False)
        indent: Indentation level (default: 2)
        separators: Custom separators tuple
        encoding: Text encoding (default: utf-8)
        
        Behavior:
        ───────────────────────────────────────────────────────
        wrap: Auto-wrap simple values (default: True)
            True → "name:Alice" becomes {"name": "Alice"}
            False → Keep data as-is
        
        overwrite: Allow overwriting existing files (default: True)
            False → Raise FileExistsError if file exists
        
        safe: Use atomic write via temp file (default: True)
            True → Write to temp, then replace
            False → Direct write
        
        append: Append to existing file (default: False)
        
        append_mode: How to append (default: auto)
            'array' : Maintain top-level JSON array, append new data
            'object': Shallow-merge dict (existing.update(data))
            'jsonl' : Append a JSON line (one object/line)
            'auto'  : Detect existing top-level type, fallback smartly

    Append Modes Explained:
    ─────────────────────────────────────────────────────────────
    array:
        [{"id": 1}] + {"id": 2} → [{"id": 1}, {"id": 2}]
    
    object:
        {"a": 1} + {"b": 2} → {"a": 1, "b": 2}
    
    jsonl:
        {"line": 1}
        {"line": 2}  ← new line appended
    
    auto:
        Detects existing structure or chooses based on data type

    Examples:
        >>> # Simple write with wrap
        >>> dump("status:active", "config.json")
        # Writes: {"status": "active"}
        
        >>> # Write without wrap
        >>> dump({"key": "value"}, "data.json", wrap=False)
        # Writes: {"key": "value"}
        
        >>> # Append to array
        >>> dump({"id": 1}, "items.json")
        >>> dump({"id": 2}, "items.json", append=True)
        # Result: [{"id": 1}, {"id": 2}]
        
        >>> # JSONL append
        >>> dump({"event": "login"}, "log.jsonl", append=True, append_mode="jsonl")
        >>> dump({"event": "logout"}, "log.jsonl", append=True, append_mode="jsonl")
        # Result:
        # {"event": "login"}
        # {"event": "logout"}

    Notes:
        - jsonl append writes a single line per dump() call
        - array/object append reads the whole file, modifies structure, 
          then writes back (safe replacement if safe=True)
        - wrap feature is JSON-specific; other parsers ignore it
    """
    path_obj = None
    if isinstance(file, (str, Path)):
        path_obj = _ensure_path(file)

    # ✅ Apply wrap transformation
    data = _wrap_if_needed(data, wrap)

    # ── JSONL append (streaming-friendly)
    if append and append_mode == "jsonl":
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            line = _serialize_json(data, ensure_ascii, sort_keys, indent=None, separators=separators, **kwargs)
            # Ensure single-line JSON (indent=None for jsonl)
            with path_obj.open("a", encoding=encoding) as f:
                f.write(line)
                f.write("\n")
        else:
            # file-like object
            line = _serialize_json(data, ensure_ascii, sort_keys, indent=None, separators=separators, **kwargs)
            file.write(line + "\n")
        return

    # ── Non-JSONL flows require structured write
    if path_obj:
        # overwrite guard
        if path_obj.exists() and not overwrite and not append:
            raise FileExistsError(f"[json.dump] Target exists and overwrite=False: {path_obj}")

        # append with array/object/auto
        if append:
            existing = None
            if path_obj.exists():
                try:
                    existing = load(path_obj, encoding=encoding, jsonl=False)
                except Exception:
                    # if not a valid JSON, fall back to JSONL append
                    # (i.e., treat the file as log-like text)
                    append_mode = "jsonl"
                    return dump(
                        data, path_obj,
                        ensure_ascii=ensure_ascii, sort_keys=sort_keys,
                        indent=indent, separators=separators, encoding=encoding,
                        wrap=False, overwrite=True, safe=safe,
                        append=True, append_mode="jsonl", **kwargs
                    )

            mode = append_mode or "auto"

            # AUTO detection
            if mode == "auto":
                if isinstance(existing, list):
                    mode = "array"
                elif isinstance(existing, dict) and isinstance(data, dict):
                    mode = "object"
                elif existing is None:
                    # decide by incoming data
                    if isinstance(data, list):
                        mode = "array"
                    elif isinstance(data, dict):
                        mode = "object"
                    else:
                        mode = "jsonl"
                else:
                    mode = "jsonl"

            if mode == "array":
                if existing is None:
                    target = data if isinstance(data, list) else [data]
                else:
                    if not isinstance(existing, list):
                        raise TypeError("[json.dump] append_mode='array' requires existing top-level list")
                    target = existing
                    if isinstance(data, list):
                        target.extend(data)
                    else:
                        target.append(data)
                text = _serialize_json(target, ensure_ascii, sort_keys, indent, separators, **kwargs)

            elif mode == "object":
                if not isinstance(data, dict):
                    raise TypeError("[json.dump] append_mode='object' requires dict data")
                if existing is None:
                    target = data
                else:
                    if not isinstance(existing, dict):
                        raise TypeError("[json.dump] append_mode='object' requires existing top-level dict")
                    target = existing
                    target.update(data)
                text = _serialize_json(target, ensure_ascii, sort_keys, indent, separators, **kwargs)

            elif mode == "jsonl":
                # delegate to jsonl branch
                return dump(
                    data, path_obj,
                    ensure_ascii=ensure_ascii, sort_keys=sort_keys,
                    indent=indent, separators=separators, encoding=encoding,
                    wrap=False, overwrite=True, safe=safe,
                    append=True, append_mode="jsonl", **kwargs
                )
            else:
                raise ValueError(f"[json.dump] Unknown append_mode: {mode}")

            if safe:
                _atomic_write_text(path_obj, text, encoding=encoding)
            else:
                path_obj.parent.mkdir(parents=True, exist_ok=True)
                with path_obj.open("w", encoding=encoding) as f:
                    f.write(text)
            return

        # normal overwrite write
        text = _serialize_json(data, ensure_ascii, sort_keys, indent, separators, **kwargs)
        if safe:
            _atomic_write_text(path_obj, text, encoding=encoding)
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding) as f:
                f.write(text)
        return

    # file-like object path (no path_obj)
    # Note: we cannot safe-replace an unknown stream. Just write directly.
    json.dump(
        data, file,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        indent=indent,
        separators=separators,
        **kwargs
    )

def dumps(
    data: Any,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    separators = None,
    wrap: bool = True,  # ✅ Changed default to True
    jsonl: bool = False,
    **kwargs
) -> str:
    """
    Serialize to string.
    
    Args:
        data: Data to serialize
        ensure_ascii: Escape non-ASCII characters (default: False)
        sort_keys: Sort dictionary keys (default: False)
        indent: Indentation level (default: 2)
        separators: Custom separators tuple
        wrap: Auto-wrap simple values (default: True)
        jsonl: Return as single-line JSON with trailing newline
        **kwargs: Additional json.dumps options
    
    Returns:
        JSON string
    
    Examples:
        >>> dumps("status:active")
        '{\n  "status": "active"\n}'
        
        >>> dumps({"key": "value"}, indent=None)
        '{"key": "value"}'
        
        >>> dumps({"event": "login"}, jsonl=True)
        '{"event": "login"}\n'
    """
    # Apply wrap transformation
    data = _wrap_if_needed(data, wrap)
    
    if jsonl:
        line = _serialize_json(data, ensure_ascii, sort_keys, indent=None, separators=separators, **kwargs)
        return line + "\n"
    return _serialize_json(data, ensure_ascii, sort_keys, indent, separators, **kwargs)

# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────
def _test(base="sample.json"):
    """Test all major features of the JSON parser."""
    print("=" * 80)
    print("JSON Parser Feature Test")
    print("=" * 80)
    
    # [1] Wrap feature
    print("\n[1] Auto-wrap feature")
    print("-" * 80)
    
    dump("status:active", base, wrap=True)
    result = load(base)
    print(f"String with colon: {result}")
    assert result == {"status": "active"}
    
    dump(42, base, wrap=True)
    result = load(base)
    print(f"Primitive value: {result}")
    assert result == {"value": 42}
    
    dump({"existing": "dict"}, base, wrap=True)
    result = load(base)
    print(f"Already dict: {result}")
    assert result == {"existing": "dict"}
    
    # Test JSON string parsing (bug fix)
    print("\n[1.1] JSON string parsing")
    print("-" * 80)
    
    dump('{"a":1}', base, wrap=True)
    result = load(base)
    print(f"JSON string (curly brace): {result}")
    assert result == {"a": 1}, f"Expected {{'a': 1}}, got {result}"
    
    dump('[1,2,3]', base, wrap=True)
    result = load(base)
    print(f"JSON string (square bracket): {result}")
    assert result == [1, 2, 3], f"Expected [1, 2, 3], got {result}"
    
    dump('{"nested": {"key": "value"}}', base, wrap=True)
    result = load(base)
    print(f"Nested JSON string: {result}")
    assert result == {"nested": {"key": "value"}}, f"Expected nested dict, got {result}"
    
    # [2] Append modes
    print("\n[2] Append modes")
    print("-" * 80)
    
    dump({"id": 1}, base, wrap=False)
    dump({"id": 2}, base, append=True, append_mode="auto", wrap=False)
    result = load(base)
    print(f"Array append (auto): {result}")
    
    dump({"a": 1}, base, wrap=False)
    dump({"b": 2}, base, append=True, append_mode="object", wrap=False)
    result = load(base)
    print(f"Object append (merge): {result}")
    
    # Cleanup
    if Path(base).exists():
        Path(base).unlink()
    
    print("\n" + "=" * 80)
    print("All tests passed! ")
    print("=" * 80)

if __name__ == "__main__":
    _test()