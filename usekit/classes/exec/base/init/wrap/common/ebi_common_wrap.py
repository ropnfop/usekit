# Path: usekit.classes.exec.base.init.wrap.common.ebi_exec_common_wrap.py
# -----------------------------------------------------------------------------------------------
#  EXEC Common Wrapper (ultra-short 3-letter interface)
#  Created by: THE Little Prince × ROP × FOP
#  v1.0: Unified wrapper for exec / import / boot / close with alias support
# -----------------------------------------------------------------------------------------------
#  act: e / i / b / c   → exec / import / boot / close
#  obj: a / c / d / j / m / p / s / t / y
#       any / csv / ddl / json / md / pyp / sql / txt / yaml
#  loc: b / s / d / n / t / p / c
#       base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from typing import Any
from usekit.infra.params_alias import normalize_params

# ===============================================================================
# Utility: extract action type from function name
# ===============================================================================
def _get_action_from_fn(fn) -> str:
    """
    Extract the action prefix from a wrapped function name.

    Expected patterns:
        exec_pyp_base, import_pyp_base, boot_pyp_base, close_pyp_base
    """
    name = getattr(fn, "__name__", "")
    return name.split("_", 1)[0] if "_" in name else ""

# ===============================================================================
# EXEC wrapper (exec / import / boot)
# Supports pattern-based execution with dynamic *args forwarding
# ===============================================================================
def _wrap_exec_operation(fn):
    """
    Generic wrapper for EXEC operations (exec/import/boot).

    Supported signatures:
        - exec   : pattern, *args, dir_path, keydata, cus, **kwargs
        - import : pattern, dir_path, keydata, cus, **kwargs  
        - boot   : pattern, dir_path, keydata, cus, **kwargs

    Pattern format:
        - "name:func"  → execute specific function
        - "name"       → load module
        - ":func"      → execute function on current module

    Merge rule:
        1) pattern is always first positional arg (required for exec)
        2) *args are forwarded to target function (exec only)
        3) normalize_params(**kwargs) to resolve aliases (dp, kd, cs, ...)
        4) alias values fill only missing or None fields
    """
    action = _get_action_from_fn(fn)

    def _inner(*args: Any, **kwargs: Any) -> Any:
        # 1) Extract pattern from first positional arg
        if not args:
            pattern = None
            remaining_args = ()
        else:
            pattern = args[0]
            remaining_args = args[1:]  # Rest are for target function (exec only)

        # 2) Build base params
        params: dict[str, Any] = {"pattern": pattern}

        # 3) Normalize aliases from keyword arguments
        alias_params = normalize_params(**kwargs)

        # 4) Merge aliases into params (only for missing/None values)
        for k, v in alias_params.items():
            if k not in params or params[k] is None:
                params[k] = v

        # 5) Add remaining kwargs that weren't aliased
        for k, v in kwargs.items():
            if k not in alias_params and k not in params:
                params[k] = v

        # 6) Dispatch based on action type
        if action == "exec":
            # exec needs to forward *args to target function
            return fn(params.pop("pattern"), *remaining_args, **params)
        else:
            # import/boot don't use *args
            return fn(**params)

    return _inner

# ===============================================================================
# CLOSE wrapper (different signature - no pattern, has op/restore)
# ===============================================================================
def _wrap_close_operation(fn):
    """
    Generic wrapper for CLOSE operations.

    Supported signature:
        - close: name, dir_path, op, restore, **kwargs

    Merge rule:
        1) positional args → primary params
        2) normalize_params(**kwargs) for aliases
        3) alias values fill only missing/None fields
    """
    def _inner(*args: Any, **kwargs: Any) -> Any:
        # 1) Map positional args
        keys = ["name", "dir_path", "op", "restore"]
        params: dict[str, Any] = {}
        for key, value in zip(keys, args):
            params[key] = value

        # 2) Normalize aliases
        alias_params = normalize_params(**kwargs)

        # 3) Merge aliases (only for missing/None)
        for k, v in alias_params.items():
            if k not in params or params[k] is None:
                params[k] = v

        # 4) Add remaining kwargs
        for k, v in kwargs.items():
            if k not in alias_params and k not in params:
                params[k] = v

        # 5) Dispatch
        return fn(**params)

    return _inner

# ===============================================================================
# ANY-format EXEC wrapper (multi-format with mod parameter)
# ===============================================================================
def _wrap_exec_any_fmt(fn):
    """
    Generic wrapper for ANY-format EXEC operations.

    Adds 'mod' parameter for dynamic format routing.

    Supported signatures:
        - exec   : pattern, *args, mod, dir_path, keydata, cus, **kwargs
        - import : pattern, mod, dir_path, keydata, cus, **kwargs
        - boot   : pattern, mod, dir_path, keydata, cus, **kwargs

    Merge rule: same as _wrap_exec_operation but includes 'mod' in params
    """
    action = _get_action_from_fn(fn)

    def _inner(*args: Any, **kwargs: Any) -> Any:
        # 1) Extract pattern from first positional arg
        if not args:
            pattern = None
            remaining_args = ()
        else:
            pattern = args[0]
            remaining_args = args[1:]

        # 2) Build base params (includes mod for ANY-format)
        params: dict[str, Any] = {"pattern": pattern}

        # 3) Normalize aliases
        alias_params = normalize_params(**kwargs)

        # 4) Merge aliases
        for k, v in alias_params.items():
            if k not in params or params[k] is None:
                params[k] = v

        # 5) Add remaining kwargs
        for k, v in kwargs.items():
            if k not in alias_params and k not in params:
                params[k] = v

        # 6) Dispatch
        if action == "exec":
            return fn(params.pop("pattern"), *remaining_args, **params)
        else:
            return fn(**params)

    return _inner
