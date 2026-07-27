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
from usekit.infra.params_value import normalize_value_params

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
    # Internal: common normalization (like ExecLd._normalize_common)
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
        Normalize name expression for DATA layer.

        Applies normalize_value_params to support:
        - Dot path: "test.test01" → dir_path="test", name="test01"
        - Inline codes: "@jb.data" → ov_fmt="json", ov_loc="base"
        - @alias resolution: "@card.math_001" → km lookup → dir_path + name

        @alias MUST resolve. If km file or alias is missing, error is raised.
        (Design doc Section 8: alias must not silently fall through)
        """
        # --- Step 0: @alias → KM resolve (BEFORE normalize_value_params) ---
        if isinstance(name, str) and name.startswith("@"):
            from usekit.classes.common.utils.helper_km_system import resolve_km_alias

            body = name[1:]
            parts = body.split(".", 1)
            alias = parts[0]
            rest = parts[1] if len(parts) > 1 else ""

            effective_loc = loc or "base"

            # This raises FileNotFoundError / KeyError on failure (no fallthrough)
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
                    print("[DATA-LOADER] _normalize_common() [KM-GROUP]")
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
                print("[DATA-LOADER] _normalize_common() [KM]")
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
        # Remove None values: let normalizer apply its own defaults
        norm_kwargs = {k: v for k, v in norm_kwargs.items() if v is not None}

        params = normalize_value_params(name, **norm_kwargs)

        if debug:
            print("[DATA-LOADER] _normalize_common()")
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
            >>> loader.read(name="test.test01")  # dot path → dir_path auto
            >>> loader.read(name="user_*")  # pattern
            >>> loader.read(name="%test%", keydata="email")
        """
        mod = mod or "all"
        
        # Allow user-provided debug to override instance debug
        debug = kwargs.pop('debug', self.debug_mode)

        # --- Normalize name expression (dot path, inline codes) ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: search across multiple directories ---
            if params.get("is_group"):
                results = []
                for dp in params["dir_paths"]:
                    try:
                        r = read_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            default=None, recursive=recursive, find_all=find_all,
                            debug=debug, **kwargs,
                        )
                        results.append(r)
                    except FileNotFoundError:
                        continue
                if not results:
                    raise FileNotFoundError(
                        f"No files found in group '@{name[1:].split('.')[0]}' "
                        f"for name='{params.get('name')}'"
                    )
                return results if len(results) > 1 else results[0]

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            # Apply format/location overrides if present
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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

        # --- Normalize name expression (dot path, inline codes) ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding blocked for write ---
            if params.get("is_group"):
                alias = name[1:].split(".")[0] if name.startswith("@") else name
                raise ValueError(
                    f"Group alias '@{alias}' cannot be used for write. "
                    f"Use a single alias instead."
                )

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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

        # --- Normalize name expression (dot path, inline codes) ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding blocked for update ---
            if params.get("is_group"):
                alias = name[1:].split(".")[0] if name.startswith("@") else name
                raise ValueError(
                    f"Group alias '@{alias}' cannot be used for update. "
                    f"Use a single alias instead."
                )

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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

        # --- Normalize name expression (dot path, inline codes) ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding blocked for delete ---
            if params.get("is_group"):
                alias = name[1:].split(".")[0] if name.startswith("@") else name
                raise ValueError(
                    f"Group alias '@{alias}' cannot be used for delete. "
                    f"Use a single alias instead."
                )

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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

        # --- Normalize name expression (dot path, inline codes) ---
        if name and isinstance(name, str) and ('.' in name or name.startswith('@')):
            params = self._normalize_common(
                name, dir_path=dir_path, loc=loc, cus=cus, debug=debug,
            )

            # --- Group binding: any dir has it → True ---
            if params.get("is_group"):
                for dp in params["dir_paths"]:
                    try:
                        if has_operation(
                            fmt=self.fmt, name=params.get("name"), mod=mod,
                            dir_path=dp, loc=loc, cus=cus, keydata=keydata,
                            recursive=recursive, debug=debug, **kwargs,
                        ):
                            return True
                    except Exception:
                        continue
                return False

            name = params.get("name", name)
            dir_path = params.get("dir_path", dir_path)
            if params.get("ov_loc"):
                loc = params["ov_loc"]

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
            **kwargs
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
    read_base  = partialmethod(read, loc="base")
    read_sub   = partialmethod(read, loc="sub")
    read_dir   = partialmethod(read, loc="dir")
    read_now   = partialmethod(read, loc="now")
    read_tmp   = partialmethod(read, loc="tmp")
    read_pre   = partialmethod(read, loc="cus")
    read_cache = partialmethod(read, loc="cache")
    read_mem   = partialmethod(read, loc="mem")

    # WRITE aliases
    write_base  = partialmethod(write, loc="base")
    write_sub   = partialmethod(write, loc="sub")
    write_dir   = partialmethod(write, loc="dir")
    write_now   = partialmethod(write, loc="now")
    write_tmp   = partialmethod(write, loc="tmp")
    write_pre   = partialmethod(write, loc="cus")
    write_cache = partialmethod(write, loc="cache")
    write_mem   = partialmethod(write, loc="mem")

    # UPDATE aliases
    update_base  = partialmethod(update, loc="base")
    update_sub   = partialmethod(update, loc="sub")
    update_dir   = partialmethod(update, loc="dir")
    update_now   = partialmethod(update, loc="now")
    update_tmp   = partialmethod(update, loc="tmp")
    update_pre   = partialmethod(update, loc="cus")
    update_cache = partialmethod(update, loc="cache")
    update_mem   = partialmethod(update, loc="mem")

    # DELETE aliases
    delete_base  = partialmethod(delete, loc="base")
    delete_sub   = partialmethod(delete, loc="sub")
    delete_dir   = partialmethod(delete, loc="dir")
    delete_now   = partialmethod(delete, loc="now")
    delete_tmp   = partialmethod(delete, loc="tmp")
    delete_pre   = partialmethod(delete, loc="cus")
    delete_cache = partialmethod(delete, loc="cache")
    delete_mem   = partialmethod(delete, loc="mem")

    # EXISTS aliases
    has_base  = partialmethod(has, loc="base")
    has_sub   = partialmethod(has, loc="sub")
    has_dir   = partialmethod(has, loc="dir")
    has_now   = partialmethod(has, loc="now")
    has_tmp   = partialmethod(has, loc="tmp")
    has_pre   = partialmethod(has, loc="cus")
    has_cache = partialmethod(has, loc="cache")
    has_mem   = partialmethod(has, loc="mem")

    def list_mem(self) -> list:
        """List all keys currently in the in-memory store."""
        from usekit.classes.data.base.load.ops.dbl_mem_store import mem_list
        return mem_list()

    def clear_mem(self) -> None:
        """Clear all entries from the in-memory store."""
        from usekit.classes.data.base.load.ops.dbl_mem_store import mem_clear
        mem_clear()

    def __repr__(self) -> str:
        """String representation of DataLd instance."""
        return f"DataLd(fmt={self.fmt!r}, debug={self.debug_mode})"
