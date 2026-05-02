# Path: usekit.classes.exec.base.load.ops.ebl_ops_loader.py
# -----------------------------------------------------------------------------------------------
#  ExecLd - Pattern-normalizing loader for import / exec / boot / close
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from functools import partialmethod
from typing import Any, Optional, Literal, Union

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_const import get_const
from usekit.infra.params_value import normalize_value_params

# Low-level ops (index layer)
from usekit.classes.exec.base.load.ops.ebl_a_index_ops import (
    import_operation,
    exec_operation,
    boot_operation,
    close_operation,
)

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "pre", "cache"], str]


class ExecLd:
    """
    Unified EXEC loader - pattern normalization + op delegation

    Pipeline:
        User → ExecLd.import_op/exec/boot/close → normalize_value_params → *_operation

    Responsibilities:
    - Normalize pattern + kwargs (single source of truth)
    - Handle edge cases (e.g. ":run" function-only)
    - Split usekit params vs target kwargs (for exec)
    - Call index-layer operations (import_operation / exec_operation / ...)

    NOT responsible for:
    - Real execution (→ ebl_exec / ebp_exec_*)
    - Path resolution details (→ ebl_exec_sub / helper_search)
    """

    def __init__(
        self,
        fmt: Optional[str] = None,
        *,
        loc: Loc = "base",
        debug: Optional[bool] = None,
    ) -> None:
        # Default format for exec world is usually "pyp"
        self.fmt = fmt or "pyp"
        self.loc: Loc = loc

        # Use global debug config if not explicitly set
        self.debug_mode: bool = (
            bool(get_const(f"DEBUG_OPTIONS.{self.fmt}")) if debug is None else bool(debug)
        )

        # Used for function-only pattern ":run"
        self._current_module_name: Optional[str] = None

    # =========================================================================
    # Internal: common normalization
    # =========================================================================

    def _normalize_common(
        self,
        pattern: Optional[str],
        *,
        name: Optional[str],
        mod: Optional[str],
        dir_path: Optional[str],
        loc: Optional[Loc],
        cus: Optional[str],
        keydata: Optional[str | list[str]],
        default: Any,
        recursive: bool,
        find_all: bool,
        debug: Optional[bool],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Common normalization for all operations (import / exec / boot / close).

        This is the ONLY place where:
        - pattern is parsed
        - inline format/location overrides are handled
        - alias / raw_name / loc / fmt are finalized
        """

        norm_kwargs: dict[str, Any] = {
            "fmt": self.fmt,
            "loc": loc or self.loc,
            "mod": mod or "all",
            "cus": cus,
            "keydata": keydata,
            "default": default,
            "recursive": recursive,
            "find_all": find_all,
            "debug": self.debug_mode if debug is None else debug,
            "name": name,
            "dir_path": dir_path,
            **kwargs,
        }

        # Remove None values: let normalizer apply its own defaults
        norm_kwargs = {k: v for k, v in norm_kwargs.items() if v is not None}

        params = normalize_value_params(pattern, **norm_kwargs)

        if params.get("debug"):
            print("[LOADER] normalize_common()")
            print(f"  pattern   = {pattern!r}")
            print(f"  name      = {params.get('name')!r}")
            print(f"  func      = {params.get('func')!r}")
            print(f"  dir_path  = {params.get('dir_path')!r}")
            if params.get("ov_fmt") or params.get("ov_loc"):
                print(
                    f"  override  = fmt={params.get('ov_fmt')!r}, "
                    f"loc={params.get('ov_loc')!r}"
                )

        return params

    # =========================================================================
    # IMPORT
    # =========================================================================

    @log_and_raise
    def import_op(
        self,
        pattern: Optional[str] = None,
        *,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Optional[Loc] = None,
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        default: Any = None,
        recursive: bool = False,
        find_all: bool = False,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Import module/functions with pattern support.
        
        Supports batch import with pipe separator ("|"):
            loader.import_op("mod1:f1,f2 | mod2:f3,f4")
            loader.import_op("test:add | utils:helper | math:sqrt")

        Single import examples:
            loader.import_op("test.test_args:add,sub")
            loader.import_op("@ps.utils:f1,f2,f3")
            loader.import_op("test:helper1,helper2")
        """
        
        # ======================================================================
        # Batch Import: Check for pipe separator
        # ======================================================================
        if pattern and "|" in pattern:
            # Split by pipe and trim whitespace
            patterns = [p.strip() for p in pattern.split("|") if p.strip()]
            
            if debug or self.debug_mode:
                print(f"[LOADER] Batch import detected: {len(patterns)} patterns")
                for idx, p in enumerate(patterns, 1):
                    print(f"[LOADER]   {idx}. {p}")
            
            # Import each pattern individually
            results = []
            for idx, single_pattern in enumerate(patterns, 1):
                if debug or self.debug_mode:
                    print(f"[LOADER] Batch {idx}/{len(patterns)}: {single_pattern}")
                
                # Recursive call with single pattern
                result = self.import_op(
                    single_pattern,
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
                results.append(result)
            
            if debug or self.debug_mode:
                print(f"[LOADER] Batch import completed: {len(results)} modules")
            
            # Return list of ImportedModule objects
            return results
        
        # ======================================================================
        # Single Import: Normal processing
        # ======================================================================
        params = self._normalize_common(
            pattern,
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
            **kwargs,
        )

        # For import, 그대로 넘기면 됨 (index ops가 func 분리 등 처리)
        return import_operation(**params)

    # =========================================================================
    # EXEC
    # =========================================================================

    @log_and_raise
    def exec(
        self,
        pattern: Optional[str] = None,
        *args: Any,
        name: Optional[str] = None,
        func: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Optional[Loc] = None,
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        recursive: bool = False,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Execute code.

        Examples:
            loader.exec("test:add", 10, 20)
            loader.exec("test.test_args:add", 10, 20)
            loader.exec("@ps.utils:run", data)
            loader.exec(":run", 10, 20)  # function-only with context
        """

        params = self._normalize_common(
            pattern,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            default=None,
            recursive=recursive,
            find_all=False,
            debug=debug,
            **kwargs,
        )

        # Overwrite func if explicitly given
        if func is not None:
            params["func"] = func

        # ── Edge 1: function-only (":run")
        if params.get("name") is None and params.get("func") is not None:
            if params.get("debug"):
                print("[LOADER] function-only pattern detected (:run)")

            if self._current_module_name:
                params["name"] = self._current_module_name
                if params.get("debug"):
                    print(
                        f"[LOADER] using current module: "
                        f"{self._current_module_name!r}"
                    )
            else:
                raise ValueError(
                    f"Function-only pattern '{pattern}' requires context.\n"
                    f"- Either load a module first (loader.exec('mod.name'))\n"
                    f"- Or use 'module:func' pattern directly "
                    f"(e.g. 'test:add')."
                )

        # ── Edge 2: name-only ("run") → 그대로 넘기고 하위에서 entry-point 판단
        if params.get("name") is not None and params.get("func") is None:
            if params.get("debug"):
                print("[LOADER] name-only pattern detected (pass-through)")

        # Positional args for target function
        params["args"] = args
        
        if params.get("debug"):
            print(f"[LOADER] args assigned to params: {args}")

        # usekit internal parameter keys (not passed to target kwargs)
        USEKIT_PARAMS = {
            "fmt",
            "mod",
            "name",
            "func",
            "dir_path",
            "loc",
            "cus",
            "ov_fmt",
            "ov_loc",
            "raw_name",
            "alias",
            "debug",
            "reload",
            "safe",
            "mode",
            "mode_sub",
            "walk",
            "case_sensitive",
            "key_type",
            "path",
            "keydata",
            "default",
            "recursive",
            "find_all",
            "create_missing",
        }

        # Target kwargs: everything that is not internal usekit key
        kwargs_exec = {
            k: v
            for k, v in params.items()
            if k not in USEKIT_PARAMS and k not in {"args", "kwargs_exec"}
        }
        params["kwargs_exec"] = kwargs_exec

        if params.get("debug") and kwargs_exec:
            print(f"[LOADER] target kwargs = {list(kwargs_exec.keys())}")

        result = exec_operation(**params)

        # Remember current module for ":run"
        if params.get("name"):
            self._current_module_name = params["name"]

        return result

    # =========================================================================
    # BOOT / CLOSE (same normalization, 다른 op로 delegate)
    # =========================================================================

    @log_and_raise
    def boot(
        self,
        pattern: Optional[str] = None,
        *,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Optional[Loc] = None,
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Boot operation (session / service bootstrap).
        Pattern/loc 처리 방식은 import_op와 동일하게 간주.
        """
        params = self._normalize_common(
            pattern,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            default=None,
            recursive=False,
            find_all=False,
            debug=debug,
            **kwargs,
        )
        return boot_operation(**params)

    @log_and_raise
    def close(
        self,
        pattern: Optional[str] = None,
        *,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        loc: Optional[Loc] = None,
        cus: Optional[str] = None,
        keydata: Optional[str | list[str]] = None,
        debug: Optional[bool] = None,
        **kwargs: Any,
    ) -> Any:
        """
        Close operation (session / service teardown).
        """
        params = self._normalize_common(
            pattern,
            name=name,
            mod=mod,
            dir_path=dir_path,
            loc=loc,
            cus=cus,
            keydata=keydata,
            default=None,
            recursive=False,
            find_all=False,
            debug=debug,
            **kwargs,
        )
        return close_operation(**params)

    # =========================================================================
    # IDE-friendly location aliases (7 loc variants)
    # =========================================================================

    # IMPORT_OP aliases
    import_base = partialmethod(import_op, loc="base")
    import_sub = partialmethod(import_op, loc="sub")
    import_dir = partialmethod(import_op, loc="dir")
    import_now = partialmethod(import_op, loc="now")
    import_tmp = partialmethod(import_op, loc="tmp")
    import_pre = partialmethod(import_op, loc="pre")
    import_cache = partialmethod(import_op, loc="cache")

    # EXEC aliases
    exec_base = partialmethod(exec, loc="base")
    exec_sub = partialmethod(exec, loc="sub")
    exec_dir = partialmethod(exec, loc="dir")
    exec_now = partialmethod(exec, loc="now")
    exec_tmp = partialmethod(exec, loc="tmp")
    exec_pre = partialmethod(exec, loc="pre")
    exec_cache = partialmethod(exec, loc="cache")

    # BOOT aliases
    boot_base = partialmethod(boot, loc="base")
    boot_sub = partialmethod(boot, loc="sub")
    boot_dir = partialmethod(boot, loc="dir")
    boot_now = partialmethod(boot, loc="now")
    boot_tmp = partialmethod(boot, loc="tmp")
    boot_pre = partialmethod(boot, loc="pre")
    boot_cache = partialmethod(boot, loc="cache")

    # CLOSE aliases
    close_base = partialmethod(close, loc="base")
    close_sub = partialmethod(close, loc="sub")
    close_dir = partialmethod(close, loc="dir")
    close_now = partialmethod(close, loc="now")
    close_tmp = partialmethod(close, loc="tmp")
    close_pre = partialmethod(close, loc="pre")
    close_cache = partialmethod(close, loc="cache")

    def __repr__(self) -> str:
        return f"ExecLd(fmt={self.fmt!r}, loc={self.loc!r}, debug={self.debug_mode})"