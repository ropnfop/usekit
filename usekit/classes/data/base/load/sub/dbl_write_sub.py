# Path: usekit.classes.data.base.load.sub.dbl_write_sub.py
# -----------------------------------------------------------------------------------------------
#  DATA WRITE OPERATION ONLY (Light-weight sub module)
#  Purpose: Format-agnostic file write wrapper
#  Version: v2.2 - Optimized safe write logic
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Optional, Union
import io

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.post.parser_factory import get_parser_by_format
from usekit.classes.data.base.load.sub.dbl_common_sub import (
    _ensure_path_obj,
    _atomic_write_text,
    _filter_dump_kwargs,
)

__all__ = ["proc_write_data"]


# ────────────────────────────────────────────────
# [ WRITE ]
# ────────────────────────────────────────────────

@log_and_raise
def proc_write_data(
    fmt: str,
    path: Optional[Union[str, Path]],
    data: Any,
    *,
    dump_mode: bool = False,
    wrap: bool = True,  # JSON-only param (parser handles)
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    encoding: str = "utf-8",
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,  # JSON append support
    append_mode: Optional[str] = None,  # JSON append_mode support
    **kwargs
) -> Any:
    """
    Write data using the format-specific parser.
    If dump_mode=True or path=None → return serialized string/bytes
    
    Args:
        fmt: Format name (json, yaml, txt, csv, pkl, etc.)
        path: Full file path with extension (None if dump_mode=True)
        data: Data to write
        dump_mode: If True, return serialized representation only (no file I/O)
        wrap: Auto-wrap simple values (JSON only) - passed to parser
        ensure_ascii: Escape non-ASCII chars (JSON only)
        sort_keys: Sort dictionary keys
        indent: Indentation level for pretty printing
        encoding: Text file encoding
        overwrite: If False, raise if the file already exists
        safe: Use atomic write (temp file -> replace)
        append: Append mode (JSON/TXT)
        append_mode: JSON append mode (array/object/jsonl/auto)
        **kwargs: Extra parser-specific options
        
    Returns:
        Serialized value if dump_mode=True, otherwise None
    """
    parser = get_parser_by_format(fmt)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [DDL SPECIAL HANDLING]
    # DDL parser has its own smart logic (table name extraction, backup, etc.)
    # Delegate directly to parser.dump() instead of generic handling
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if fmt == "ddl":
        # Build kwargs for DDL parser
        ddl_kwargs = {
            "encoding": encoding,
            "overwrite": overwrite,
            "safe": safe,
            **kwargs  # Includes auto_backup, mode, primary_key, debug, etc.
        }
        
        # Explicitly ensure debug is passed (it should be in kwargs already)
        # This is a safety check in case debug was filtered out somewhere
        if "debug" not in ddl_kwargs and "debug" in kwargs:
            ddl_kwargs["debug"] = kwargs["debug"]
        
        # Call DDL parser directly
        # parser.dump() handles:
        # - file=None or directory → table name extraction
        # - file=path → use as-is
        # - auto-backup logic
        # - dump mode fallback
        result = parser.dump(data, file=path, **ddl_kwargs)
        return result
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # ─── Dump mode (no physical file writing) ───
    if dump_mode or path is None:
        dump_kwargs = _filter_dump_kwargs(
            fmt, for_file=False,
            wrap=wrap,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
            indent=indent,
            append=append,
            append_mode=append_mode,
            **kwargs
        )

        if fmt == "pkl":
            return parser.dumps(data, **dump_kwargs) if hasattr(parser, "dumps") \
                else _dump_to_bytes(parser, data, dump_kwargs)

        buffer = io.StringIO()
        parser.dump(data, buffer, **dump_kwargs)
        return buffer.getvalue()

    # ─── File write mode ───
    path_obj = _ensure_path_obj(path)

    if path_obj.exists() and not overwrite:
        raise FileExistsError(f"File exists: {path_obj}")

    path_obj.parent.mkdir(parents=True, exist_ok=True)

    # ─── PKL write (binary) ───
    if fmt == "pkl":
        parser.dump(data, path_obj, **kwargs)
        return None

    # ─── Text write ───
    # Note: encoding is passed to parser for JSON (in format_specific list)
    # For other formats, it's only used by file.open() or _atomic_write_text()
    dump_kwargs = _filter_dump_kwargs(
        fmt, for_file=False,  # Never include encoding automatically
        wrap=wrap,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        indent=indent,
        append=append,
        append_mode=append_mode,
        overwrite=overwrite,
        safe=safe,
        encoding=encoding,  # Always pass encoding, filter decides if it's used
        **kwargs,
    )

    # JSON parser handles append internally with file path
    if fmt == "json" and append:
        # JSON parser needs encoding for append operations
        parser.dump(data, path_obj, **dump_kwargs)
        return None

    if safe:
        buffer = io.StringIO()
        parser.dump(data, buffer, **dump_kwargs)
        _atomic_write_text(path_obj, buffer.getvalue(), encoding=encoding)
    else:
        with path_obj.open("w", encoding=encoding) as f:
            parser.dump(data, f, **dump_kwargs)

    return None


def _dump_to_bytes(parser, data, kwargs):
    """Fallback if PKL parser has no dumps()"""
    buf = io.BytesIO()
    parser.dump(data, buf, **kwargs)
    return buf.getvalue()


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------