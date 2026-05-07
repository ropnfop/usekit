# Path: usekit.classes.data.base.load.ops.dbl_mem_store.py
# -----------------------------------------------------------------------------------------------
#  MemStore - Process-level in-memory store for loc="mem"
#  Created by: THE Little Prince × ROP × FOP
#  No file I/O. Data lives only for the duration of the process.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Any

_STORE: dict[str, Any] = {}


def mem_write(name: str, data: Any) -> None:
    _STORE[name] = data


def mem_read(name: str, default: Any = None) -> Any:
    return _STORE.get(name, default)


def mem_has(name: str) -> bool:
    return name in _STORE


def mem_delete(name: str) -> bool:
    return _STORE.pop(name, _STORE) is not _STORE


def mem_keys() -> list[str]:
    return list(_STORE.keys())


def mem_clear() -> None:
    _STORE.clear()


__all__ = [
    "mem_write", "mem_read", "mem_has",
    "mem_delete", "mem_keys", "mem_clear",
]
