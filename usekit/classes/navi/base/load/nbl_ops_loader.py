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
from usekit.infra.params_value import normalize_value_params

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
    # Internal: common normalization (like ExecLd/DataLd._normalize_common)
    # ----------------------------------------------------------------

    def _normalize_common(
        self,
        name: Optional[str],
        *,
        dir_path: Optional[str] = None,
        loc: Optional[Loc] = None,
        cus: Optional[str] = None,
        debug: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Normalize name expression for NAVI layer.

        Applies normalize_value_params to support:
        - Dot path: "test.test01" → dir_path="test", name="test01"
        - Inline codes: "@jb.data" → ov_fmt="json", ov_loc="base"
        - @alias resolution: "@card.math_001" → km lookup → dir_path + name

        @alias MUST resolve. If km file or alias is missing, error is raised.
        """
        # --- Step 0: @alias → KM resolve (BEFORE normalize_value_params) ---
        if isinstance(name, str) and name.startswith("@"):
            from usekit.classes.common.utils.helper_km_system import resolve_km_alias

            body = name[1:]
            parts = body.split(".", 1)
            alias = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

            effective_loc = loc or "base"

            km_result = resolve_km_alias(
                alias, rest, self.fmt, effective_loc, debug=debug,
            )

            # --- Group binding ---
            if km_result.get("is_group"):
                result = {
                    "dir_paths": km_result.get("dir_paths"),
                    "name": km_result.get("name"),
                    "is_group": True,
                }
                if debug:
                    print("[NAVI-LOADER] _normalize_common() [KM-GROUP]")
                    print(f"  input     = {name!r}")
                    print(f"  dir_paths = {result['dir_paths']}")
                    print(f"  name      = {result['name']!r}")
                return result

            # --- Single alias ---
            result = {
                "name": km_result.get("name"),
                "dir_path": km_result.get("dir_path"),
            }
            if debug:
                print("[NAVI-LOADER] _normalize_common() [KM]")
                print(f"  input     = {name!r}")
                print(f"  name      = {result['name']!r}")
                print(f"  dir_path  = {result['dir_path']!r}")
            return result

        # --- Step 1: Standard normalize_value_params ---
        norm_kwargs: dict[str, Any] = {
            "fmt": self.fmt,
            "loc": loc,
            "cus": cus,
            "dir_path": dir_path,
            **kwargs,
        }
        norm_kwargs = {k: v for k, v in norm_kwargs.items() if v is not None}

        params = normalize_value_params(name, **norm_kwargs)

        if debug:
            print("[NAVI-LOADER] _normalize_common()")
            print(f"  input     = {name!r}")
            print(f"  name      = {params.get('name')!r}")
            print(f"  dir_path  = {params.get('dir_path')!r}")
            if params.get("ov_fmt") or params.get("ov_loc"):
                print(
                    f"  override  = fmt={params.get('ov_fmt')!r}, "
                    f"loc={params.get('ov_loc')!r}"
                )

        return params

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
            >>> loader.path(name="test.test01")  # dot path
            >>> loader.path(name="user_*")  # pattern
        """
        mod = mod or "all"
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: return paths from all directories ---
            if params.get("is_group"):
                all_paths = []
                for dp in params["dir_paths"]:
                    try:
                        r = path_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            default=None, recursive=recursive, find_all=find_all,
                            debug=debug, **kwargs,
                        )
                        if r:
                            if isinstance(r, list):
                                all_paths.extend(r)
                            else:
                                all_paths.append(r)
                    except Exception:
                        continue
                return all_paths if all_paths else default

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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
            debug=debug,
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
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: collect from all dirs ---
            if params.get("is_group"):
                all_found = []
                for dp in params["dir_paths"]:
                    try:
                        r = find_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            create_missing=create_missing, recursive=recursive,
                            debug=debug, **kwargs,
                        )
                        if r:
                            if isinstance(r, list):
                                all_found.extend(r)
                            else:
                                all_found.append(r)
                    except Exception:
                        continue
                return all_found if all_found else None

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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
            debug=debug,
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
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: list from all directories ---
            if params.get("is_group"):
                all_items = []
                for dp in params["dir_paths"]:
                    try:
                        r = list_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            create_missing=create_missing, recursive=recursive,
                            debug=debug, **kwargs,
                        )
                        if r:
                            if isinstance(r, list):
                                all_items.extend(r)
                            else:
                                all_items.append(r)
                    except Exception:
                        continue
                return all_items if all_items else None

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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
            debug=debug,
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
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: get from all directories ---
            if params.get("is_group"):
                all_results = []
                for dp in params["dir_paths"]:
                    try:
                        r = get_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            recursive=recursive, debug=debug, **kwargs,
                        )
                        if r is not None:
                            all_results.append(r)
                    except Exception:
                        continue
                return all_results if all_results else None

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

        return get_operation(
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
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding blocked for set (write-type operation) ---
            if params.get("is_group"):
                alias = name[1:].split(".")[0] if name.startswith("@") else name
                raise ValueError(
                    f"Group alias '@{alias}' cannot be used for set. "
                    f"Use a single alias instead."
                )

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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
            debug=debug,
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