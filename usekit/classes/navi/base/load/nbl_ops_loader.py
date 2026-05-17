# Path: usekit.classes.navi.base.load.nbl_ops_loader.py
# -----------------------------------------------------------------------------------------------
#  NaviLd - Thin wrapper over operation modules
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Literal, Union
from functools import partialmethod

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_const import get_const

# Import operations
from usekit.classes.navi.base.load.ops.nbl_a_index_ops import (
    path_operation,
    find_operation,
    list_operation,
    get_operation,
    set_operation,
)

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "pre", "cache"], str]

class NaviLd:
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
    def path(
        self,
        name: Optional[str] = None,
        mod: Optional[str] = None, 
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
        path with pattern support
        
        Examples:
            >>> loader.path(name="config")
            >>> loader.path(name="user_*")  # [NEW] pattern
            >>> loader.path(name="%test%", keydata="email")
        """
        mod = mod or "all"

        return path_operation(
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
            debug=self.debug_mode,
            **kwargs
        )

    @log_and_raise
    def find(
        self,
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
        """find operation"""
        mod = mod or "all"

        return find_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            create_missing=create_missing,
            recursive=recursive,
            debug=self.debug_mode,
            **kwargs
        )

    @log_and_raise
    def list(
        self,
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
        """list operation"""
        mod = mod or "all"

        return list_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            create_missing=create_missing,
            recursive=recursive,
            debug=self.debug_mode,
            **kwargs
        )

    @log_and_raise
    def get(
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
        """get operation"""
        mod = mod or "all"

        return get_operation(
            fmt=self.fmt,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            recursive=recursive,
            debug=self.debug_mode,
            **kwargs
        )

    def set(
        self,
        mod: Optional[str] = None,
        data: Any = None,
        name: Optional[str] = None,
        root: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Loc = "base",
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        recursive: bool = False,
        **kwargs
    ) -> bool:
        """set check with pattern support"""
        mod = mod or "all"

        return set_operation(
            fmt=self.fmt,
            mod=mod,
            data=data,
            name=name,
            root=root,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            recursive=recursive,
            debug=self.debug_mode,
            **kwargs
        )

    # ----------------------------------------------------------------
    # IDE-friendly Aliases (6 location variants)
    # ----------------------------------------------------------------
    
    # path aliases
    path_base = partialmethod(path, loc="base")
    path_sub  = partialmethod(path, loc="sub")
    path_dir  = partialmethod(path, loc="dir")
    path_now  = partialmethod(path, loc="now")
    path_tmp  = partialmethod(path, loc="tmp")
    path_pre  = partialmethod(path, loc="cus")
    path_cache  = partialmethod(path, loc="cache")

    # find aliases
    find_base = partialmethod(find, loc="base")
    find_sub  = partialmethod(find, loc="sub")
    find_dir  = partialmethod(find, loc="dir")
    find_now  = partialmethod(find, loc="now")
    find_tmp  = partialmethod(find, loc="tmp")
    find_pre  = partialmethod(find, loc="cus")
    find_cache  = partialmethod(find, loc="cache")

    # list aliases
    list_base = partialmethod(list, loc="base")
    list_sub  = partialmethod(list, loc="sub")
    list_dir  = partialmethod(list, loc="dir")
    list_now  = partialmethod(list, loc="now")
    list_tmp  = partialmethod(list, loc="tmp")
    list_pre  = partialmethod(list, loc="cus")
    list_cache  = partialmethod(list, loc="cache")

    # get aliases
    get_base = partialmethod(get, loc="base")
    get_sub  = partialmethod(get, loc="sub")
    get_dir  = partialmethod(get, loc="dir")
    get_now  = partialmethod(get, loc="now")
    get_tmp  = partialmethod(get, loc="tmp")
    get_pre  = partialmethod(get, loc="cus")
    get_cache  = partialmethod(get, loc="cache")

    # set aliases
    set_base = partialmethod(set, loc="base")
    set_sub  = partialmethod(set, loc="sub")
    set_dir  = partialmethod(set, loc="dir")
    set_now  = partialmethod(set, loc="now")
    set_tmp  = partialmethod(set, loc="tmp")
    set_pre  = partialmethod(set, loc="cus")
    set_cache  = partialmethod(set, loc="cache")

    def __repr__(self) -> str:
        """String representation of NaviLd instance."""
        return f"NaviLd(fmt={self.fmt!r}, debug={self.debug_mode})"