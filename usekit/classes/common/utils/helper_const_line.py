# Path: usekit.classes.common.utils.helper_const_line.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Line-based sys_const.yaml parser that preserves comments and formatting
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from functools import lru_cache

SYS_CONST_PATH = Path("usekit/sys/sys_yaml/sys_const.yaml")

@lru_cache(maxsize=1)
def load_sys_const_lines(path: Path = SYS_CONST_PATH):
    """
    Load sys_const.yaml line-by-line and create SECTION.key index.
    
    Returns:
        (lines, index) where:
        - lines: list of raw lines with original formatting
        - index: dict mapping "SECTION.key" to line metadata
    
    Example index entry:
        "JSON_PATH.json": {
            "line_no": 15,
            "raw": "  json: json_main_1\n",
            "section": "JSON_PATH",
            "key": "json",
            "value_str": "json_main_1"
        }
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)

    index: dict[str, dict] = {}
    current_section: str | None = None

    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.strip()

        # Skip blank lines and comments
        if not stripped or stripped.startswith("#"):
            continue

        indent = len(line) - len(line.lstrip(" "))

        # Section line (e.g., "JSON_PATH:")
        if indent == 0 and stripped.endswith(":"):
            current_section = stripped[:-1].strip()
            continue

        # Key line (e.g., "  json: json_main_1")
        if current_section and ":" in stripped:
            key_part, rest = stripped.split(":", 1)
            key_name = key_part.strip()
            full_key = f"{current_section}.{key_name}"

            index[full_key] = {
                "line_no": lineno,
                "raw": raw,
                "section": current_section,
                "key": key_name,
                "value_str": rest.lstrip(),
            }

    return lines, index


def get_const_line_info(full_key: str):
    """
    Get line metadata for a specific key.
    
    Args:
        full_key: Key in "SECTION.key" format (e.g., "JSON_PATH.json")
    
    Returns:
        (line_no, raw_line, value_str)
    
    Raises:
        KeyError: If key not found in sys_const.yaml
    """
    lines, index = load_sys_const_lines()
    info = index.get(full_key)
    if not info:
        raise KeyError(f"[SYS_CONST_LINE] '{full_key}' not found")

    return info["line_no"], info["raw"], info["value_str"]


def update_const_value(full_key: str, new_value: str, *, quote: bool = None, path: Path = SYS_CONST_PATH):
    """
    Update a single value in sys_const.yaml while preserving all formatting.
    
    Args:
        full_key: Key in "SECTION.key" format
        new_value: New value to set
        quote: Quote behavior:
            - None (default): Auto-detect from original value
            - True: Force quotes
            - False: Force no quotes
        path: Path to sys_const.yaml (defaults to standard location)
    
    Returns:
        The new line that was written
    
    Features:
    - Preserves comments, blank lines, indentation
    - Auto-preserves quote style from original
    - Updates only the target line
    - Auto-clears cache after update
    
    Example:
        # Original: '  root: "data/json"'
        update_const_value("JSON_PATH.root", "data/json_new")
        # Result:   '  root: "data/json_new"'  ← quotes preserved!
        
        # Original: '  json: json_main_1'
        update_const_value("JSON_PATH.json", "json_main_2")
        # Result:   '  json: json_main_2'  ← no quotes preserved!
    """
    lines, index = load_sys_const_lines(path)

    info = index.get(full_key)
    if not info:
        raise KeyError(f"[SYS_CONST_UPDATE] '{full_key}' not found in sys_const.yaml")

    line_no = info["line_no"]
    raw = info["raw"]
    old_value = info["value_str"]

    # Split line: "  json: json_main_1" → "  json" + ":" + " json_main_1"
    before, sep, _ = raw.partition(":")
    if not sep:
        raise ValueError(f"[SYS_CONST_UPDATE] Malformed line for '{full_key}': {raw!r}")

    # Auto-detect quote style if not specified
    if quote is None:
        # Check if original value has quotes
        quote = old_value.startswith('"') and old_value.endswith('"')

    # Build new value part (preserve quote style)
    if quote:
        value_part = f' "{new_value}"'
    else:
        value_part = f" {new_value}"

    # Preserve original newline style
    newline = "" if raw.endswith("\n") else "\n"
    new_line = f"{before}:{value_part}{newline}"

    # Replace line in memory
    lines[line_no - 1] = new_line

    # Write back to file
    path.write_text("".join(lines), encoding="utf-8")

    # Clear cache for next read
    load_sys_const_lines.cache_clear()

    return new_line
