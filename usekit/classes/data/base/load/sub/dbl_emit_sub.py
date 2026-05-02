# -----------------------------------------------------------------------------------------------
#  Emit Sub-operation - Memory-only serialization helper
#  Created by: THE Little Prince × ROP × FOP
#  Pure in-memory data transformation without file I/O
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Any, Union

from usekit.classes.data.base.post.parser_factory import get_parser_by_format


def _ensure_str(x: Any) -> str:
    if isinstance(x, str):
        return x
    if isinstance(x, bytes):
        return x.decode("utf-8")
    return str(x)


def _ensure_bytes(x: Any) -> bytes:
    if isinstance(x, bytes):
        return x
    if isinstance(x, str):
        return x.encode("utf-8")
    return str(x).encode("utf-8")


def proc_emit_data(fmt: str, data: Any, type: str = "s", **dump_kwargs) -> Union[str, dict, list, bytes]:
    """
    Memory-only emit helper.
    Uses parser.dumps()/parser.loads() only (no file I/O).
    """

    parser = get_parser_by_format(fmt)

    # [1] Dict/object output
    if type == "d":
        if isinstance(data, (dict, list)):
            return data
        if isinstance(data, (str, bytes)):
            # loads (memory)
            return parser.loads(data)
        return data

    # [2] String output
    if type == "s":
        if isinstance(data, str):
            return data
        if isinstance(data, bytes):
            return data.decode("utf-8")
        # dumps (memory)
        return parser.dumps(data, **dump_kwargs)

    # [3] Bytes output
    if type == "b":
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            return data.encode("utf-8")
        # dumps then encode
        s = parser.dumps(data, **dump_kwargs)
        return _ensure_bytes(s)

    # [4] List output
    if type == "l":
        if isinstance(data, list):
            return data
        if isinstance(data, tuple):
            return list(data)
        if isinstance(data, (str, bytes)):
            return _ensure_str(data).splitlines()
        if isinstance(data, dict):
            s = parser.dumps(data, **dump_kwargs)
            if isinstance(s, list):
                return s
            return _ensure_str(s).splitlines()
        return [data]

    raise ValueError(
        f"Unsupported output type: '{type}'. "
        "Valid types: 's' (string), 'd' (dict), 'l' (list), 'b' (bytes)"
    )


__all__ = ["proc_emit_data"]