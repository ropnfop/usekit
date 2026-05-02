# Path: usekit.classes.data.base.load.dbl_ops_loader.py
# -----------------------------------------------------------------------------------------------
#  DataLd - Thin wrapper over operation modules
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Literal, Union
from functools import partialmethod

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_const import get_const

# Import operations
from usekit.classes.data.base.load.ops.dbl_a_index_ops import (
    read_operation,
    write_operation,
    update_operation,
    delete_operation,
    has_operation,
)
from usekit.classes.data.base.load.ops.dbl_emit import emit_operation

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "pre", "cache"], str]


class DataLd:
    """
    Unified IO interface - delegates to operation modules
    
    Features:
    - [NEW] Pattern matching: "user_*", "log_????", "%test%"
    - Multiple location types (base/sub/dir/now/tmp/cus)
    - Custom path presets via cus parameter
    - Nested key access: "users[0]/email"
    - Recursive operations
    - [Future] k, kv, kc, kf, pyp (reserved)
    """

    def __init__(self, fmt: Optional[str] = None, *, debug: Optional[bool] = None):
        self.fmt = fmt or "json"
        self.debug_mode = bool(get_const(f"DEBUG_OPTIONS.{self.fmt}")) if debug is None else bool(debug)

    # ----------------------------------------------------------------
    # Delegated Operations
    # ----------------------------------------------------------------

    @log_and_raise
    def read(
        self,
        name: Optional[str] = None,
        mod: Optional[str] = None,   # ex) "json", "ini", "log", "yaml", "all"
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        default: Any = None,
        recursive: bool = False,
        find_all: bool = False,
        **kwargs
    ) -> Any:
        """
        Read with pattern support
        
        Examples:
            >>> loader.read(name="config")
            >>> loader.read(name="user_*")  # [NEW] pattern
            >>> loader.read(name="%test%", keydata="email")
        """
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        return read_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            default=default,
            recursive=recursive,
            find_all=find_all,
            debug=debug,
            **kwargs
        )

    @log_and_raise
    def write(
        self,
        data: Any = None,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        create_missing: bool = True,
        recursive: bool = False,
        **kwargs
    ) -> Optional[Path]:
        """Write operation"""
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        return write_operation(
            fmt=self.fmt,
            data=data,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            create_missing=create_missing,
            recursive=recursive,
            debug=debug,
            **kwargs
        )

    @log_and_raise
    def update(
        self,
        data: Any = None,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        create_missing: bool = True,
        recursive: bool = False,
        **kwargs
    ) -> Optional[Path]:
        """Update operation"""
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        return update_operation(
            fmt=self.fmt,
            data=data,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            create_missing=create_missing,
            recursive=recursive,
            debug=debug,
            **kwargs
        )

    @log_and_raise
    def delete(
        self,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        recursive: bool = False,
        **kwargs
    ) -> Optional[Path]:
        """Delete operation"""
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        return delete_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            recursive=recursive,
            debug=debug,
            **kwargs
        )

    def has(
        self,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        recursive: bool = False,
        **kwargs
    ) -> bool:
        """Exists check with pattern support"""
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        return has_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            recursive=recursive,
            debug=debug,
        )

    # ----------------------------------------------------------------
    # Emit Operation (memory-only serialization)
    # ----------------------------------------------------------------

    @log_and_raise
    def emit(
        self,
        data: Any = None,
        type: str = "s",
        **kwargs
    ) -> Any:
        """Memory-only serialization (no file I/O).

        Args:
            data: Data to serialize/deserialize.
            type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).

        Returns:
            Serialized or deserialized data in the requested type.
        """
        debug = kwargs.pop('debug', self.debug_mode)

        return emit_operation(
            fmt=self.fmt,
            data=data,
            type=type,
            loc="mem",
            debug=debug,
            **kwargs
        )

    # Emit alias (mem only)
    emit_mem = partialmethod(emit)

    # ----------------------------------------------------------------
    # IDE-friendly Aliases (6 location variants)
    # ----------------------------------------------------------------
    
    # READ aliases
    read_base = partialmethod(read, loc="base")
    read_sub  = partialmethod(read, loc="sub")
    read_dir  = partialmethod(read, loc="dir")
    read_now  = partialmethod(read, loc="now")
    read_tmp  = partialmethod(read, loc="tmp")
    read_pre  = partialmethod(read, loc="cus")
    read_cache  = partialmethod(read, loc="cache")

    # WRITE aliases
    write_base = partialmethod(write, loc="base")
    write_sub  = partialmethod(write, loc="sub")
    write_dir  = partialmethod(write, loc="dir")
    write_now  = partialmethod(write, loc="now")
    write_tmp  = partialmethod(write, loc="tmp")
    write_pre  = partialmethod(write, loc="cus")
    write_cache  = partialmethod(write, loc="cache")

    # UPDATE aliases
    update_base = partialmethod(update, loc="base")
    update_sub  = partialmethod(update, loc="sub")
    update_dir  = partialmethod(update, loc="dir")
    update_now  = partialmethod(update, loc="now")
    update_tmp  = partialmethod(update, loc="tmp")
    update_pre  = partialmethod(update, loc="cus")
    update_cache  = partialmethod(update, loc="cache")

    # DELETE aliases
    delete_base = partialmethod(delete, loc="base")
    delete_sub  = partialmethod(delete, loc="sub")
    delete_dir  = partialmethod(delete, loc="dir")
    delete_now  = partialmethod(delete, loc="now")
    delete_tmp  = partialmethod(delete, loc="tmp")
    delete_pre  = partialmethod(delete, loc="cus")
    delete_cache  = partialmethod(delete, loc="cache")

    # EXISTS aliases
    has_base = partialmethod(has, loc="base")
    has_sub  = partialmethod(has, loc="sub")
    has_dir  = partialmethod(has, loc="dir")
    has_now  = partialmethod(has, loc="now")
    has_tmp  = partialmethod(has, loc="tmp")
    has_pre  = partialmethod(has, loc="cus")
    has_cache  = partialmethod(has, loc="cache")

    def __repr__(self) -> str:
        """String representation of DataLd instance."""
        return f"DataLd(fmt={self.fmt!r}, debug={self.debug_mode})"
