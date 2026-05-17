# Path: usekit.classes.wrap.simple.use_simple.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince × ROP × FOP
#  — memory is usegation —
# -----------------------------------------------------------------------------------------------
#  Lazy 3-letter Usegation Interface
#
#  Dynamic routing: act + obj + loc
#    act data  : r(read) w(write) u(update) d(delete) h(has)
#    act navi  : p(path) f(find) l(list) g(get) s(set)
#    act exec  : x(exec) i(imp) b(boot) c(close)
#    obj      : j(json) y(yaml) c(csv) t(txt) m(md) s(sql) d(ddl) p(pyp) k(km) a(any)
#    loc      : b(base) s(sub) d(dir) n(now) t(tmp) p(pre) c(cache)
#
#  Usage:
#    u.pjb()           # path json base
#    u.rjb("test")     # read json base
#    u.wtb("hello")    # write txt base
#    u.ljd()           # list json dir
#    u.xpb("mod:func", args)  # exec pyp base
#    u.ipb("module")   # imp pyp base
#
#  This file binds all "simple" 3-letter methods into a single lazy router:
#    UseSP / u
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable, Optional


# ===============================================================================
# Transparent Lazy IO Wrapper
# ===============================================================================

class TransparentLazyIO:
    """
    Transparent lazy proxy around a backend object.

    - The backend object is created only once on first access.
    - All attribute access / assignment is forwarded to the backend.
    - The factory is kept for optional preload.
    """

    def __init__(self, factory):
        """
        Initialize lazy wrapper with a factory function.
        
        Parameters
        ----------
        factory : callable
            Function that returns the actual IO instance when called
        """
        object.__setattr__(self, '_factory', factory)
        object.__setattr__(self, '_cache', None)
    
    def _load(self):
        """Load and cache the actual instance on first access."""
        cache = object.__getattribute__(self, '_cache')
        if cache is None:
            factory = object.__getattribute__(self, '_factory')
            cache = factory()
            object.__setattr__(self, '_cache', cache)
        return cache
    
    def __getattr__(self, name):
        """Transparent attribute access to the lazy-loaded instance."""
        return getattr(self._load(), name)
    
    def __setattr__(self, name, value):
        """Transparent attribute setting to the lazy-loaded instance."""
        setattr(self._load(), name, value)
    
    def __dir__(self):
        """Show attributes of the lazy-loaded instance."""
        return dir(self._load())

# ===============================================================================
# Lazy Import Factory
# ===============================================================================

def _import(fmt, layer="data"):
    """
    Create lazy loader for a specific format module.
    
    Returns a TransparentLazyIO wrapper that will import the format module
    only when first accessed. This defers expensive imports until actually needed.
    
    Parameters
    ----------
    fmt : str
        Format name: json, yaml, csv, txt, md, sql, ddl, pyp, km, any
    layer : str
        Layer type: "data", "navi", or "exec"
    
    Returns
    -------
    TransparentLazyIO
        Lazy wrapper around {Format}SP/{Format}NS/{Format}EX singleton
    
    Examples
    --------
    >>> json_io = _import("json", "data")
    >>> # No import yet - module not loaded
    >>> data = json_io.rjb("config")  # Import happens here
    >>> 
    >>> pyp_exec = _import("pyp", "exec")
    >>> result = pyp_exec.xpb("mod:func", args)  # EXEC operation
    """
    def factory():
        if layer == "data":
            module_path = f"usekit.classes.data.base.init.wrap.{fmt}.dbi_simple_{fmt}"
            mod = __import__(module_path, fromlist=["*"])
            return getattr(mod, f"{fmt.capitalize()}SP")
        elif layer == "navi":
            module_path = f"usekit.classes.navi.base.init.wrap.{fmt}.nbi_simple_{fmt}"
            mod = __import__(module_path, fromlist=["*"])
            return getattr(mod, f"{fmt.capitalize()}NS")
        elif layer == "exec":
            module_path = f"usekit.classes.exec.base.init.wrap.{fmt}.ebi_simple_{fmt}"
            mod = __import__(module_path, fromlist=["*"])
            return getattr(mod, f"{fmt.capitalize()}EX")
        else:
            raise ValueError(f"Unknown layer: {layer}. Expected 'data', 'navi', or 'exec'")
            
    return TransparentLazyIO(factory)

# ===============================================================================
# Lazy Format Usegation Instances (DATA Layer)
# ===============================================================================

_json_data = _import("json", "data")
_yaml_data = _import("yaml", "data")
_csv_data = _import("csv", "data")
_txt_data = _import("txt", "data")
_md_data = _import("md", "data")
_sql_data = _import("sql", "data")
_ddl_data = _import("ddl", "data")
_pyp_data = _import("pyp", "data")
_km_data = _import("km", "data")
_any_data = _import("any", "data")

# ===============================================================================
# Lazy Format Usegation Instances (NAVI Layer)
# ===============================================================================

_json_navi = _import("json", "navi")
_yaml_navi = _import("yaml", "navi")
_csv_navi = _import("csv", "navi")
_txt_navi = _import("txt", "navi")
_md_navi = _import("md", "navi")
_sql_navi = _import("sql", "navi")
_ddl_navi = _import("ddl", "navi")
_pyp_navi = _import("pyp", "navi")
_km_navi = _import("km", "navi")
_any_navi = _import("any", "navi")

# ===============================================================================
# Lazy Format Usegation Instances (EXEC Layer)
# ===============================================================================

_json_exec = _import("json", "exec")
_yaml_exec = _import("yaml", "exec")
_csv_exec = _import("csv", "exec")
_txt_exec = _import("txt", "exec")
_md_exec = _import("md", "exec")
_sql_exec = _import("sql", "exec")
_ddl_exec = _import("ddl", "exec")
_pyp_exec = _import("pyp", "exec")
_km_exec = _import("km", "exec")
_any_exec = _import("any", "exec")


# ===============================================================================
# 3-Letter Usegation Router
# ===============================================================================

class _UseSPRouter(SimpleNamespace):
    """
    3-letter usegation router.

    Allows direct calls like:

        UseSP.rjb("test")  # read json base
        UseSP.wtb("hello") # write txt base
        UseSP.ljd()        # list json dir

    Each 3-letter method is resolved on first access and memoized.
    """

    # Operation / format / location dictionaries are also used for help text.
    _OPERATIONS = {
        # DATA operations
        "r": "read",
        "w": "write",
        "u": "update",
        "d": "delete",
        "h": "has",
        "e": "emit",
        # NAVI operations
        "p": "path",
        "f": "find",
        "l": "list",
        "g": "get",
        "s": "set",
        # EXEC operations
        "x": "exec",
        "i": "imp",
        "b": "boot",
        "c": "close",
    }

    _FORMATS = {
        "j": "json",
        "y": "yaml",
        "c": "csv",
        "t": "txt",
        "m": "md",
        "s": "sql",
        "d": "ddl",
        "p": "pyp",
        "k": "km",
        "a": "any",
    }

    _LOCATIONS = {
        "b": "base",
        "s": "sub",
        "d": "dir",
        "n": "now",
        "t": "tmp",
        "p": "pre",
        "c": "cache",
        "m": "mem",
    }

    def __init__(self, **kwargs: Any) -> None:
        """
        Parameters
        ----------
        kwargs :
            Format name mapping with data, navi, and exec layers, e.g.
                json_data=_json_data, json_navi=_json_navi, json_exec=_json_exec, ...
        """
        super().__init__(**kwargs)

        # Split formats into three layers
        data_map = {}
        navi_map = {}
        exec_map = {}
        
        for key, value in kwargs.items():
            if key.endswith("_data"):
                fmt_code = key[:-5]  # Remove "_data" suffix
                # Find corresponding format code in _FORMATS
                for code, name in self._FORMATS.items():
                    if name == fmt_code:
                        data_map[code] = value
                        break
            elif key.endswith("_navi"):
                fmt_code = key[:-5]  # Remove "_navi" suffix
                # Find corresponding format code in _FORMATS
                for code, name in self._FORMATS.items():
                    if name == fmt_code:
                        navi_map[code] = value
                        break
            elif key.endswith("_exec"):
                fmt_code = key[:-5]  # Remove "_exec" suffix
                # Find corresponding format code in _FORMATS
                for code, name in self._FORMATS.items():
                    if name == fmt_code:
                        exec_map[code] = value
                        break

        object.__setattr__(self, "_data_map", data_map)
        object.__setattr__(self, "_navi_map", navi_map)
        object.__setattr__(self, "_exec_map", exec_map)
        object.__setattr__(self, "_op_names", self._OPERATIONS)
        object.__setattr__(self, "_fmt_names", self._FORMATS)
        object.__setattr__(self, "_loc_names", self._LOCATIONS)

    # ------------------------------------------------------------------ #
    # Dynamic 3-letter method resolution
    # ------------------------------------------------------------------ #

    def __getattr__(self, name: str) -> Any:
        """
        Resolve 3-letter methods on demand and memoize them.

        - If `name` is a known attribute, normal lookup is used.
        - If `len(name) != 3`, this behaves like a normal AttributeError.
        - If `len(name) == 3`, it is interpreted as: op + fmt + loc.
        - Routes to DATA (r/w/u/d/e), NAVI (p/f/l/g/s), or EXEC (x/i/b/c) based on action.
        """
        # 1) Normal attribute resolution first.
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        # 2) Only 3-letter names are handled as dynamic usegation.
        if len(name) != 3:
            raise AttributeError(f"'{type(self).__name__}' exists no attribute '{name}'")

        op, fmt_key, loc = name[0], name[1], name[2]

        data_map = object.__getattribute__(self, "_data_map")
        navi_map = object.__getattribute__(self, "_navi_map")
        exec_map = object.__getattribute__(self, "_exec_map")
        op_names = object.__getattribute__(self, "_op_names")
        fmt_names = object.__getattribute__(self, "_fmt_names")
        loc_names = object.__getattribute__(self, "_loc_names")

        if op not in op_names or fmt_key not in fmt_names or loc not in loc_names:
            raise AttributeError(
                f"Invalid 3-letter: {name}. Expected: "
                f"op(r/w/u/d/h/e/p/f/l/g/s/x/i/b/c) + "
                f"fmt(j/y/c/t/m/s/d/p/k/a) + "
                f"loc(b/s/d/n/t/p/c/m)"
            )

        # ── Emit guard: emit only supports 'mem' location ──
        if op == "e" and loc != "m":
            fmt_full = fmt_names[fmt_key]
            raise AttributeError(
                f"emit supports only 'mem' location, got '{loc_names[loc]}'.\n"
                f"Emit is memory-only serialization (no file I/O).\n\n"
                f"Use:  u.e{fmt_key}m(data)    # emit {fmt_full} mem\n\n"
                f"For file operations, use write instead:\n"
                f"  u.w{fmt_key}{loc}(data, 'filename')"
            )

        # Determine layer based on action character
        # DATA: r/w/u/d/h/e (read, write, update, delete, has, emit)
        # NAVI: p/f/l/g/s (path, find, list, get, set)
        # EXEC: x/i/b/c (exec, imp, boot, close)
        if op in "rwudhe":
            fmt_map = data_map
            layer = "data"
        elif op in "pflgs":
            fmt_map = navi_map
            layer = "navi"
        elif op in "xibc":
            fmt_map = exec_map
            layer = "exec"
        else:
            raise AttributeError(f"Unknown action '{op}' in method '{name}'")

        if fmt_key not in fmt_map:
            raise AttributeError(
                f"Format '{fmt_key}' not available in {layer} layer for method '{name}'"
            )

        fmt_obj = fmt_map[fmt_key]
        op_full = op_names[op]
        fmt_full = fmt_names[fmt_key]
        loc_full = loc_names[loc]

        def proxy(*args: Any, _name: str = name, _fmt_obj: Any = fmt_obj, **kwargs: Any) -> Any:
            """
            Proxy to the underlying `{fmt_full}` simple wrapper.

            This function is dynamically bound to UseSP.{name} and forwards
            all positional and keyword arguments to the backend wrapper.
            """
            try:
                target = getattr(_fmt_obj, _name)
            except AttributeError as exc:
                raise AttributeError(
                    f"[UseSP] Backend object '{_fmt_obj}' has no method '{_name}'"
                ) from exc
            return target(*args, **kwargs)

        proxy.__name__ = name
        proxy.__qualname__ = f"UseSP.{name}"
        proxy.__doc__ = f"{op_full} {fmt_full} {loc_full}"

        # Memoize on the instance so subsequent calls are direct.
        setattr(self, name, proxy)
        return proxy


# ===============================================================================
# Public Singleton + Preload
# ===============================================================================

UseSP = _UseSPRouter(
    # DATA layer
    json_data=_json_data,
    yaml_data=_yaml_data,
    csv_data=_csv_data,
    txt_data=_txt_data,
    md_data=_md_data,
    sql_data=_sql_data,
    ddl_data=_ddl_data,
    pyp_data=_pyp_data,
    km_data=_km_data,
    any_data=_any_data,
    # NAVI layer
    json_navi=_json_navi,
    yaml_navi=_yaml_navi,
    csv_navi=_csv_navi,
    txt_navi=_txt_navi,
    md_navi=_md_navi,
    sql_navi=_sql_navi,
    ddl_navi=_ddl_navi,
    pyp_navi=_pyp_navi,
    km_navi=_km_navi,
    any_navi=_any_navi,
    # EXEC layer
    json_exec=_json_exec,
    yaml_exec=_yaml_exec,
    csv_exec=_csv_exec,
    txt_exec=_txt_exec,
    md_exec=_md_exec,
    sql_exec=_sql_exec,
    ddl_exec=_ddl_exec,
    pyp_exec=_pyp_exec,
    km_exec=_km_exec,
    any_exec=_any_exec,
)

# Optional ultra-short alias (not exported by default, but convenient in REPL)
u = UseSP


def preload_sp() -> None:
    """
    Preload all simple usegation backends (DATA, NAVI, and EXEC layers) in parallel.

    This will trigger imports and instantiation of all `{Fmt}SP/{Fmt}NS/{Fmt}EX` singletons,
    so that first user call does not pay the import cost.
    """
    lazy_values = [
        obj._factory for obj in [
            # DATA layer
            _json_data, _yaml_data, _csv_data,
            _txt_data, _md_data, _sql_data,
            _ddl_data, _pyp_data, _km_data, _any_data,
            # NAVI layer
            _json_navi, _yaml_navi, _csv_navi,
            _txt_navi, _md_navi, _sql_navi,
            _ddl_navi, _pyp_navi, _km_navi, _any_navi,
            # EXEC layer
            _json_exec, _yaml_exec, _csv_exec,
            _txt_exec, _md_exec, _sql_exec,
            _ddl_exec, _pyp_exec, _km_exec, _any_exec,
        ]
    ]

    from usekit.classes.common.init.helper_lazy import lazy
    lazy.preload(*(lazy.value(f) for f in lazy_values), max_workers=20)


__all__ = ["UseSP", "preload_sp"]