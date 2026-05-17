# Path: usekit.classes.data.base.load.sub.dbl_update_sub.py
# -----------------------------------------------------------------------------------------------
#  DATA UPDATE OPERATION ONLY (Light-weight sub module)
#  Purpose: Merge / replace updates into existing data files
#  Version: v2.1 - Clean separation & unified behavior
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Optional, Union
import io

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.post.parser_factory import get_parser_by_format
from usekit.classes.data.base.load.sub.dbl_common_sub import (
    _ensure_path_obj,
    _filter_dump_kwargs,
    _deep_merge_dict,
)
from usekit.classes.data.base.load.sub.dbl_write_sub import proc_write_data

__all__ = ["proc_update_data"]


# ────────────────────────────────────────────────
# [ UPDATE ]
# ────────────────────────────────────────────────

@log_and_raise
def proc_update_data(
    fmt: str,
    path: Optional[Union[str, Path]],
    updates: Any,
    *,
    dump_mode: bool = False,
    merge: bool = True,
    deep: bool = False,
    upsert: bool = True,
    wrap: bool = True,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: int = 2,
    encoding: str = "utf-8",
    **kwargs
) -> Any:
    """
    Update existing data file:
    - Merge dict/list or replace value entirely
    - Create file if not exists (when upsert=True)
    """
    parser = get_parser_by_format(fmt)

    # Dump mode: no file I/O
    if dump_mode or path is None:
        dump_kwargs = _filter_dump_kwargs(
            fmt, for_file=False,
            wrap=wrap,
            ensure_ascii=ensure_ascii,
            sort_keys=sort_keys,
            indent=indent,
            **kwargs
        )

        if fmt == "pkl":
            if hasattr(parser, "dumps"):
                return parser.dumps(updates, **dump_kwargs)
            buf = io.BytesIO()
            parser.dump(updates, buf, **dump_kwargs)
            return buf.getvalue()

        buffer = io.StringIO()
        parser.dump(updates, buffer, **dump_kwargs)
        return buffer.getvalue()

    path_obj = _ensure_path_obj(path)

    # File missing → create new if allowed
    if not path_obj.exists():
        if upsert:
            proc_write_data(
                fmt, path_obj, updates,
                wrap=wrap, indent=indent,
                ensure_ascii=ensure_ascii,
                sort_keys=sort_keys,
                encoding=encoding,
                **kwargs
            )
            return updates
        raise FileNotFoundError(f"File not found and upsert=False: {path_obj}")

    # Load current data
    if fmt == "pkl":
        current = parser.load(path_obj, **kwargs)
    else:
        with path_obj.open("r", encoding=encoding) as f:
            current = parser.load(f, **kwargs)

    # Merge logic
    if merge and isinstance(current, dict) and isinstance(updates, dict):
        new_data = _deep_merge_dict(current.copy(), updates) if deep \
            else {**current, **updates}
    elif merge and isinstance(current, list) and isinstance(updates, list):
        new_data = current + updates
    else:
        new_data = updates  # Replace

    # Write updated
    proc_write_data(
        fmt, path_obj, new_data,
        wrap=wrap,
        ensure_ascii=ensure_ascii,
        sort_keys=sort_keys,
        indent=indent,
        encoding=encoding,
        **kwargs
    )

    return new_data


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------