# Path: usekit.infra.params_map.py
# -----------------------------------------------------------------------------------
#  Parameter code maps for USEKIT
#
#  - OPERATION_CODES : single-letter → operation name
#  - FORMAT_CODES    : single-letter → data format
#  - LOCATION_CODES  : single-letter → location key
#
#  This module is intentionally small and stable so it can be imported
#  from both low-level (data/navi) and high-level (exec/import) layers.
# -----------------------------------------------------------------------------------

from __future__ import annotations

from typing import Dict

# Single-letter → operation name
OPERATION_CODES: Dict[str, str] = {
    "r": "read",
    "w": "write",
    "u": "update",
    "d": "delete",
    "e": "exists",
    "p": "path",
    "f": "find",
    "l": "list",
    "g": "get",
    "s": "set",
}

# Single-letter → format name
FORMAT_CODES: Dict[str, str] = {
    "j": "json",
    "y": "yaml",
    "c": "csv",
    "t": "txt",
    "m": "md",
    "s": "sql",
    "d": "ddl",
    "p": "pyp",
    "a": "any",
}

# Single-letter → location name
LOCATION_CODES: Dict[str, str] = {
    "b": "base",
    "s": "sub",
    "d": "dir",
    "n": "now",
    "t": "tmp",
    "p": "pre",
    "c": "cache",
}

__all__ = [
    "OPERATION_CODES",
    "FORMAT_CODES",
    "LOCATION_CODES",
]