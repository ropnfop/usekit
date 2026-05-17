# Path: usekit.classes.navi.base.init.wrap.common.nbi_common_wrap.py
# -----------------------------------------------------------------------------------------------
#  Simple Common IO Aliases (ultra-short 3-letter interface)
#  Created by: THE Little Prince × ROP × FOP
#  v3.0: Unified simple wrapper for path / find / list / get / set (including ANY-format routing)
# -----------------------------------------------------------------------------------------------
#  act: p / f / l / g / s   → path / find / list / get / set
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
        path_txt_base, find_txt_base, list_txt_base,
        get_txt_base,  set_txt_base,  ...
    """
    name = getattr(fn, "__name__", "")
    return name.split("_", 1)[0] if "_" in name else ""

# ===============================================================================
# Format-specific wrapper (json/yaml/txt/sql/...)
# Used by the simple wrapper layer for:
#   - path / find / list / get / set
# ===============================================================================
def _wrap_simple_format(fn):
    """
    Generic wrapper for format-specific operations (non-ANY).

    Supported signatures:
        - path      : name, dir_path, keydata, cus
        - find/list : name, dir_path, keydata, cus
        - get       : name, dir_path, op, restore
        - set       : data, name, root, dir_path, op, cp

    Merge rule:
        1) positional args → primary params (highest priority)
        2) normalize_params(**kwargs) to resolve aliases (nm, dp, kd, cs, op, rs, cp, ...)
        3) alias values fill only missing or None fields
    """
    action = _get_action_from_fn(fn)

    def _inner(*args: Any, **kwargs: Any) -> Any:
        # 1) positional mapping keys by action
        if action in ("path", "find", "list"):
            keys = ["name", "dir_path", "keydata", "cus"]
        elif action == "get":
            keys = ["name", "dir_path", "op", "restore"]
        elif action == "set":
            keys = ["data", "name", "root", "dir_path", "op", "cp"]
        else:
            keys = []

        # 2) build params from positional arguments (highest priority)
        params: dict[str, Any] = {}
        for key, value in zip(keys, args):
            params[key] = value

        # 3) normalize aliases from keyword arguments
        alias_params = normalize_params(**kwargs)

        # 4) alias fills only missing or None values
        for k, v in alias_params.items():
            if k not in params or params[k] is None:
                params[k] = v

        # 5) dispatch to final function
        return fn(**params)

    return _inner

# ===============================================================================
# ANY-format wrapper (fmt="any", dynamic routing by mod)
# Used by AnyIO.* layer
# ===============================================================================
def _wrap_simple_any_fmt(fn):
    """
    Generic wrapper for ANY-format (multi-format) operations.

    Supported signatures:
        - path      : name, mod, dir_path, keydata, cus
        - find/list : data, name, mod, dir_path, keydata, cus
        - get       : name, mod, dir_path, op, restore
        - set       : data, name, mod, root, dir_path, op, cp

    Merge rule:
        1) positional args → primary params (highest priority)
        2) normalize_params(**kwargs) to resolve aliases (nm, md, dp, kd, cs, op, rs, cp, ...)
        3) alias values fill only missing or None fields
    """
    action = _get_action_from_fn(fn)

    def _inner(*args: Any, **kwargs: Any) -> Any:
        # 1) positional mapping keys for ANY-format actions
        if action == "path":
            keys = ["name", "mod", "dir_path", "keydata", "cus"]
        elif action in ("find", "list"):
            keys = ["data", "name", "mod", "dir_path", "keydata", "cus"]
        elif action == "get":
            keys = ["name", "mod", "dir_path", "op", "restore"]
        elif action == "set":
            keys = ["data", "name", "mod", "root", "dir_path", "op", "cp"]
        else:
            keys = []

        # 2) build params from positional arguments (highest priority)
        params: dict[str, Any] = {}
        for key, value in zip(keys, args):
            params[key] = value

        # 3) normalize aliases from keyword arguments
        alias_params = normalize_params(**kwargs)

        # 4) alias fills only missing or None values
        for k, v in alias_params.items():
            if k not in params or params[k] is None:
                params[k] = v

        # 5) dispatch to final function
        return fn(**params)

    return _inner