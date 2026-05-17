# Path: usekit.classes.data.base.load.sub.dbl_read_sub.py
# -----------------------------------------------------------------------------------------------
#  DATA READ OPERATION ONLY (Light-weight sub module)
#  Purpose: Format-agnostic file read wrapper
#  Version: v2.1 - Clean separation from internal common utilities
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Optional, Union
import os

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.post.parser_factory import get_parser_by_format
from usekit.classes.data.base.load.sub.dbl_common_sub import (
    _ensure_path_obj,
)

__all__ = ["proc_read_data"]


# ────────────────────────────────────────────────
# [ READ ]
# ────────────────────────────────────────────────

@log_and_raise
def proc_read_data(
    fmt: str,
    path: Union[str, Path],
    *,
    unwrap_key: Optional[str] = None,
    force_dict: bool = False,
    return_meta: bool = False,
    encoding: str = "utf-8",
    **kwargs
) -> Any:
    """
    Read data from file using format-specific parser.
    """
    parser = get_parser_by_format(fmt)
    path_obj = _ensure_path_obj(path)

    if not path_obj.is_file():
        raise FileNotFoundError(f"File not found: {path_obj}")

    # PKL: binary load
    if fmt == "pkl":
        try:
            data = parser.load(path_obj, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to decode PKL: {e}") from e

    # TEXT formats
    else:
        try:
            with path_obj.open("r", encoding=encoding) as f:
                data = parser.load(f, **kwargs)
        except Exception as e:
            raise ValueError(f"Failed to decode {fmt.upper()}: {e}") from e

    # Extract specific key
    if unwrap_key and isinstance(data, dict):
        data = data.get(unwrap_key, {})

    # Enforce dict
    if force_dict and not isinstance(data, dict):
        data = {"_": data}

    # Return with meta info
    if return_meta:
        size = os.path.getsize(path_obj) if path_obj.exists() else None
        return {
            "data": data,
            "path": str(path_obj.resolve()),
            "size": size
        }

    return data

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------