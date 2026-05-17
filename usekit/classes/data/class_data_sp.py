# Path: usekit.classes.data.class_data_sp.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is connection —
# -----------------------------------------------------------------------------------------------
#  Lazy Parallel Data IO binder with transparent access
#  
#  v3.2: Dynamic 3-letter method routing via __getattr__
#        - Zero upfront method generation cost
#        - Lazy binding on first access with memoization
#        - Memory efficient: only creates methods actually used
#        
#  User interfaces:
#    u.json.rjb("test")    # format-first (explicit)
#    u.rjb("test")         # 3-letter alias (compact)
#
#  Method naming: op + fmt + loc
#    op  : r(read) w(write) u(update) d(delete) h(has)
#    fmt : j(json) y(yaml) c(csv) t(txt) m(md) s(sql) d(ddl) p(pyp) a(any)
#    loc : b(base) s(sub) d(dir) n(now) t(tmp) p(pre) c(cache)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace

# ===============================================================================
# Transparent Lazy Loading Wrapper
# ===============================================================================

class TransparentLazyIO:
    """
    Lazy wrapper providing transparent attribute access to format IO modules.
    
    Delays module import until first attribute access, then caches the loaded
    instance for subsequent calls. This enables fast startup while maintaining
    transparent access patterns.
    
    Architecture:
        - _factory: Callable that imports and returns the actual IO instance
        - _cache: Stores loaded instance after first access
        - __getattr__: Forwards all attribute access to cached instance
    
    Examples
    --------
    >>> json_io = TransparentLazyIO(lambda: import_json_module())
    >>> json_io.rjb("test")  # First access triggers import
    >>> json_io.wjb(data)    # Subsequent calls use cached instance
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

def _import(fmt):
    """
    Create lazy loader for a specific format module.
    
    Returns a TransparentLazyIO wrapper that will import the format module
    only when first accessed. This defers expensive imports until actually needed.
    
    Parameters
    ----------
    fmt : str
        Format name: json, yaml, csv, txt, md, sql, ddl, pyp, any
    
    Returns
    -------
    TransparentLazyIO
        Lazy wrapper around {Format}SP singleton
    
    Examples
    --------
    >>> json_io = _import("json")
    >>> # No import yet - module not loaded
    >>> data = json_io.rjb("config")  # Import happens here
    """
    def factory():
        module_path = f"usekit.classes.data.base.init.wrap.{fmt}.dbi_simple_{fmt}"
        mod = __import__(module_path, fromlist=["*"])
        return getattr(mod, f"{fmt.capitalize()}SP")
    
    return TransparentLazyIO(factory)

# ===============================================================================
# Lazy Format Instances
# ===============================================================================

_json_io = _import("json")
_yaml_io = _import("yaml")
_csv_io = _import("csv")
_txt_io = _import("txt")
_md_io = _import("md")
_sql_io = _import("sql")
_ddl_io = _import("ddl")
_pyp_io = _import("pyp")
_km_io = _import("km")
_any_io = _import("any")

# ===============================================================================
# DataSP Router with Dynamic Method Binding
# ===============================================================================

class _DataSPRouter(SimpleNamespace):
    """
    Intelligent router providing dual access patterns:
      1. Format-first:  DataSP.json.rjb("test")  [explicit, IDE-friendly]
      2. 3-letter flat: DataSP.rjb("test")       [compact, mobile-optimized]
    
    The 3-letter methods are created dynamically on first access via __getattr__,
    then memoized for subsequent calls. This provides zero initialization cost
    while maintaining fast access after first use.
    
    Method Naming Convention
    ------------------------
    3-letter format: op + fmt + loc
    
    Operations (op):
        r : read    - Load data from file
        w : write   - Write data to file (overwrite)
        u : update  - Update existing data (merge)
        d : delete  - Delete file or key path
        h : has  - Check if file or key path exists
    
    Formats (fmt):
        j : json    y : yaml    c : csv     t : txt     m : md
        s : sql     d : ddl     p : pyp    k : km  a : any
    
    Locations (loc):
        b : base    - Base directory
        s : sub     - Subdirectory
        d : dir     - Custom directory path
        n : now     - Timestamped (current time)
        t : tmp     - Temporary directory
        p : pre     - Predefined prefix
        c : cache   - Cache directory
    
    Performance Characteristics
    ---------------------------
    - Initialization: O(1) - no method pre-generation
    - First access:   O(1) - method creation + memoization
    - Later access:   O(1) - direct attribute lookup (fastest)
    - Memory:         O(k) where k = number of methods actually used
    
    Examples
    --------
    >>> # Format-first (explicit)
    >>> data = DataSP.json.rjb("config")
    >>> DataSP.yaml.wyb(data, "output")
    
    >>> # 3-letter alias (compact)
    >>> data = DataSP.rjb("config")  # read json base
    >>> DataSP.wyb(data, "output")   # write yaml base
    
    >>> # Both styles work identically
    >>> DataSP.json.rjb("test") == DataSP.rjb("test")  # True
    """
    
    # Operation codes and their verbose names
    _OPERATIONS = {
        "r": "read",
        "w": "write",
        "u": "update",
        "d": "delete",
        "h": "has",
    }
    
    # Format codes and their verbose names
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
    
    # Location codes and their verbose names
    _LOCATIONS = {
        "b": "base",
        "s": "sub",
        "d": "dir",
        "n": "now",
        "t": "tmp",
        "p": "pre",
        "c": "cache",
    }
    
    def __init__(self, **kwargs):
        """
        Initialize router with format IO instances.
        
        Parameters
        ----------
        **kwargs : dict
            Format name -> lazy IO instance mappings
            Expected: json, yaml, csv, txt, md, sql, ddl, pyp, any
        """
        super().__init__(**kwargs)
        
        # Build format character -> IO instance mapping
        fmt_map = {code: getattr(self, name) 
                   for code, name in self._FORMATS.items()}
        
        # Store in instance (bypassing __setattr__)
        object.__setattr__(self, "_fmt_map", fmt_map)
        object.__setattr__(self, "_op_names", self._OPERATIONS)
        object.__setattr__(self, "_fmt_names", self._FORMATS)
        object.__setattr__(self, "_loc_names", self._LOCATIONS)
    
    def __getattr__(self, name):
        """
        Dynamic method binding with memoization.
        
        This method intercepts attribute access for 3-letter method names and
        creates proxy functions on-demand. The proxy is then memoized as an
        instance attribute for fast subsequent access.
        
        Flow:
            1. Check if it's a 3-letter name (op + fmt + loc)
            2. Validate each component (op/fmt/loc)
            3. Create proxy function that forwards to format IO
            4. Add docstring and metadata
            5. Memoize proxy as instance attribute
            6. Return proxy
        
        Parameters
        ----------
        name : str
            Attribute name being accessed
        
        Returns
        -------
        callable
            Proxy function for the 3-letter method
        
        Raises
        ------
        AttributeError
            If name doesn't match 3-letter pattern or is invalid
        
        Examples
        --------
        >>> # First access to 'rjb'
        >>> method = DataSP.rjb  # __getattr__ creates and memoizes proxy
        >>> # Second access to 'rjb'
        >>> method = DataSP.rjb  # Direct attribute lookup (no __getattr__)
        """
        # Try normal SimpleNamespace attributes first (json, yaml, etc.)
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass
        
        # Must be 3-letter alias
        if len(name) != 3:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'"
            )
        
        # Parse 3-letter components
        op, fmt_key, loc = name[0], name[1], name[2]
        
        # Get lookup tables
        fmt_map = object.__getattribute__(self, "_fmt_map")
        op_names = object.__getattribute__(self, "_op_names")
        fmt_names = object.__getattribute__(self, "_fmt_names")
        loc_names = object.__getattribute__(self, "_loc_names")
        
        # Validate components
        if op not in op_names or fmt_key not in fmt_map or loc not in loc_names:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'\n"
                f"Invalid 3-letter pattern. Expected: op(r/w/u/d/e) + "
                f"fmt(j/y/c/t/m/s/d/p/k/a) + loc(b/s/d/n/t/p/c)"
            )
        
        # Get components
        fmt_obj = fmt_map[fmt_key]
        op_full = op_names[op]
        fmt_full = fmt_names[fmt_key]
        loc_full = loc_names[loc]
        
        # Create lazy proxy function
        def proxy(*args, _name=name, _fmt_obj=fmt_obj, **kwargs):
            """
            Proxy that forwards calls to the actual format IO method.
            
            The format IO module is loaded lazily on first invocation via
            getattr, which triggers TransparentLazyIO.__getattr__ if not
            yet cached.
            """
            target = getattr(_fmt_obj, _name)
            return target(*args, **kwargs)
        
        # Add metadata for introspection
        proxy.__name__ = name
        proxy.__qualname__ = f"DataSP.{name}"
        proxy.__doc__ = (
            f"{op_full} {fmt_full} {loc_full}\n\n"
            f"Supports positional, keyword, and alias parameters (nm, dp, kd).\n\n"
            f"Method pattern: {name} = {op_full[0]} + {fmt_full[0]} + {loc_full[0]}\n\n"
            f"Examples\n"
            f"--------\n"
            f">>> use.{name}(\"test\")\n"
            f">>> u.{name}(\"test\")  # if DataSP bound to u\n"
            f">>> u.{fmt_full}.{name}(\"test\")  # format-first access\n"
        )
        
        # Memoize: store proxy as instance attribute for fast subsequent access
        setattr(self, name, proxy)
        
        return proxy

# ===============================================================================
# DataSP Singleton Instance
# ===============================================================================

DataSP = _DataSPRouter(
    json=_json_io,
    yaml=_yaml_io,
    csv=_csv_io,
    txt=_txt_io,
    md=_md_io,
    sql=_sql_io,
    ddl=_ddl_io,
    pyp=_pyp_io,
    km=_km_io,
    any=_any_io,
)

# ===============================================================================
# Parallel Preload Utility
# ===============================================================================

def preload_sp():
    """
    Preload all format modules in parallel background threads.
    
    This function triggers lazy imports for all format modules concurrently,
    warming up the module cache. Useful for reducing first-access latency in
    production environments.
    
    Use Cases
    ---------
    - Application startup: Import modules while initializing other components
    - Lambda warm-up: Prepare modules before handling requests
    - Testing: Ensure all modules are loaded before benchmarking
    
    Performance
    -----------
    - Sequential loading: ~10 × single module time
    - Parallel loading:   ~1 × single module time (10 workers)
    - Speedup:           ~10x with max_workers=10
    
    Examples
    --------
    >>> # At application startup
    >>> preload_sp()  # Background loading starts
    >>> # Continue with other initialization...
    >>> # By the time you use DataSP, modules are ready
    >>> data = DataSP.rjb("config")  # No import delay
    
    Notes
    -----
    This function returns immediately while loading happens in background.
    The lazy.preload() method handles thread pooling and synchronization.
    """
    lazy_values = [
        obj._factory for obj in [
            _json_io, _yaml_io, _csv_io,
            _txt_io, _md_io, _sql_io,
            _ddl_io, _pyp_io, _km_io, _any_io
        ]
    ]
    
    from usekit.classes.common.init.helper_lazy import lazy
    
    # Trigger all factories in parallel (max 10 workers)
    lazy.preload(*[lazy.value(f) for f in lazy_values], max_workers=10)

# ===============================================================================
# Public API
# ===============================================================================

__all__ = [
    "DataSP",       # Primary interface: DataSP.json.rjb() and DataSP.rjb()
    "preload_sp",   # Parallel preloading utility
]
