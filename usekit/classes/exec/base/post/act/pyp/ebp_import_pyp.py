# Path: usekit.classes.exec.base.post.act.pyp.ebp_import_pyp.py
# -----------------------------------------------------------------------------------------------
#  Import PYP POST Layer - Actual Import Logic
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Import Python module or functions
#  
#  Key features:
#  - Import entire module
#  - Import specific functions (multiple)
#  - Extract executable code for each function
#  - Register in global namespace
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import sys
import importlib.util

from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.data.base.post.parser.parser_pyp import extract_executable


# ===============================================================================
# Imported Module Wrapper
# ===============================================================================

class ImportedModule:
    """
    Wrapper class for imported functions that supports both attribute and dict access.
    
    Provides dual access patterns:
    1. Object access: m.add(10, 20) or m['add'](10, 20)
    2. Global access: add(10, 20) - auto-injected by default
    
    Examples:
        >>> m = import_pyp(path, func_list=["add", "greet"])
        
        # Object attribute access
        >>> m.add(10, 20)
        30
        
        # Object dict access
        >>> m['add'](10, 20)
        30
        
        # Direct global call (auto-injected)
        >>> add(10, 20)
        30
        
        # Dict-like behavior
        >>> len(m)               # number of functions
        2
        >>> list(m)              # list of function names
        ['add', 'greet']
        >>> for name in m:       # iteration
        ...     print(name)
        add
        greet
    """
    
    def __init__(self, functions: Dict[str, Any], inject_globals: bool = False):
        """
        Initialize with function dictionary.
        
        Args:
            functions: Dict mapping function names to function objects
            inject_globals: If True, inject functions into global namespace
        """
        self._functions = functions
        
        if inject_globals:
            self._inject_to_globals()
    
    def _inject_to_globals(self):
        """Inject all functions into the caller's global namespace."""
        import inspect
        
        # Get the caller's frame
        frame = inspect.currentframe()
        if frame is None:
            return
        
        try:
            # Walk up the frame stack to find the right target
            # In Colab/IPython: we need to reach the __main__ module's globals
            # In script: we need the topmost user code frame
            
            target_frame = None
            current = frame
            
            # Strategy: find frame with __name__ == '__main__' or topmost frame
            while current is not None:
                if current.f_globals.get('__name__') == '__main__':
                    target_frame = current
                    break
                current = current.f_back
            
            # Fallback: use the topmost frame if __main__ not found
            if target_frame is None:
                current = frame
                while current.f_back is not None:
                    current = current.f_back
                target_frame = current
            
            if target_frame is None:
                return
            
            caller_globals = target_frame.f_globals
            
            # Inject each function into caller's globals
            for name, func in self._functions.items():
                caller_globals[name] = func
        finally:
            del frame
    
    def __getattr__(self, name: str) -> Any:
        """Enable attribute access: m.add"""
        if name.startswith('_'):
            # Private attributes access the actual __dict__
            return object.__getattribute__(self, name)
        if name in self._functions:
            return self._functions[name]
        raise AttributeError(f"Function '{name}' not found. Available: {list(self._functions.keys())}")
    
    def __getitem__(self, name: str) -> Any:
        """Enable dict access: m['add']"""
        return self._functions[name]
    
    def __contains__(self, name: str) -> bool:
        """Enable 'in' operator: 'add' in m"""
        return name in self._functions
    
    def __len__(self) -> int:
        """Enable len(): len(m)"""
        return len(self._functions)
    
    def __iter__(self):
        """Enable iteration: for name in m"""
        return iter(self._functions)
    
    def __repr__(self) -> str:
        """String representation"""
        return f"ImportedModule({list(self._functions.keys())})"
    
    def keys(self):
        """Dict-like keys()"""
        return self._functions.keys()
    
    def values(self):
        """Dict-like values()"""
        return self._functions.values()
    
    def items(self):
        """Dict-like items()"""
        return self._functions.items()
    
    def get(self, name: str, default=None):
        """Dict-like get()"""
        return self._functions.get(name, default)


# ===============================================================================
# Global Import Registry
# ===============================================================================

_IMPORT_REGISTRY: Dict[str, Any] = {}
"""
Global registry for imported modules and functions.

Structure:
{
    "module_name": <module_object>,
    "module_name.func1": <function_object>,
    "module_name.func2": <function_object>,
}

This allows:
- Persistent imports across sessions
- Quick lookup for re-imports
- Function-level tracking
- Direct function calls via call() helper
"""


def get_registry() -> Dict[str, Any]:
    """Get the import registry."""
    return _IMPORT_REGISTRY


def clear_registry():
    """Clear the import registry."""
    _IMPORT_REGISTRY.clear()


def call(func_path: str, *args, **kwargs) -> Any:
    """
    Call imported function directly from registry without global injection.
    
    This provides a clean way to call imported functions without polluting
    global namespace or using object attribute access.
    
    Args:
        func_path: Function path in format "module.func" or just "func"
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
        
    Returns:
        Function return value
        
    Raises:
        KeyError: If function not found in registry
        
    Examples:
        >>> # Import functions (no global injection needed)
        >>> import_pyp(path, func_list=["add"], auto_inject=False)
        
        >>> # Call directly via registry
        >>> call("test_args.add", 10, 40)
        50
        
        >>> # Short form (searches all modules)
        >>> call("add", 10, 40)
        50
        
        >>> # With kwargs
        >>> call("greet", name="USE", greeting="HI")
        'HI, USE!'
    """
    # Try exact match first (e.g., "test_args.add")
    if func_path in _IMPORT_REGISTRY:
        return _IMPORT_REGISTRY[func_path](*args, **kwargs)
    
    # Try short name search (e.g., "add" → search for "*.add")
    for key, func in _IMPORT_REGISTRY.items():
        if key.endswith(f".{func_path}"):
            return func(*args, **kwargs)
    
    # Not found
    available = [k for k in _IMPORT_REGISTRY.keys() if '.' in k]
    raise KeyError(
        f"Function '{func_path}' not found in registry. "
        f"Available: {available}"
    )


# ===============================================================================
# Module Import
# ===============================================================================

# Module cache: path -> (signature, module). Before this every ipb() call
# re-executed the file (and every ipb() at its top level, recursively), so a
# chat turn ran ~600 exec_module calls. A hit is only served while the file's
# (mtime_ns, size) is unchanged, so editing a .py still takes effect on the
# next call. A module may list extra files it reads at import time in
# __ipb_deps__ (e.g. prompt .md files); their mtimes join the signature.
# A module can opt out with __ipb_nocache__ = True.
# USEKIT_IPB_FRESH=1 disables the cache (old behaviour).
_MODULE_CACHE: Dict[str, tuple] = {}

# One re-entrant lock around cache MISSES only (hits stay lock-free). Without
# it a startup prewarm thread and the first request could exec the same file
# twice and end up holding two different module objects. Re-entrant because a
# module's top level often ipb()s others on the same thread.
import threading as _threading
_MODULE_LOCK = _threading.RLock()


def clear_module_cache() -> None:
    _MODULE_CACHE.clear()


def _file_sig(fp) -> tuple:
    try:
        st = os.stat(fp)
        return (st.st_mtime_ns, st.st_size)
    except OSError:
        return (None, None)


def _module_sig(path: Path, module: Any = None) -> tuple:
    sig = [_file_sig(path)]
    deps = getattr(module, "__ipb_deps__", None) if module is not None else None
    if deps:
        for d in deps:
            sig.append((str(d), _file_sig(d)))
    return tuple(sig)


def _import_module(path: Path, debug: bool = False) -> Any:
    """
    Import a Python module from file path.
    
    Args:
        path: Python file path
        debug: Debug mode
        
    Returns:
        Imported module object
        
    Examples:
        >>> mod = _import_module(Path("utils.pyp"))
        >>> mod.add(1, 2)
        3
    """
    
    module_name = path.stem
    fresh = os.environ.get("USEKIT_IPB_FRESH", "") not in ("", "0")
    ckey = str(path)

    if not fresh:
        hit = _MODULE_CACHE.get(ckey)
        if hit is not None:
            sig, cached = hit
            if sig == _module_sig(path, cached):
                if debug:
                    print(f"[IMPORT-PYP] module cache hit: {module_name}")
                sys.modules[module_name] = cached
                _IMPORT_REGISTRY[module_name] = cached
                return cached
            _MODULE_CACHE.pop(ckey, None)
    
    with _MODULE_LOCK:
        if not fresh:
            # another thread may have finished this file while we waited
            hit = _MODULE_CACHE.get(ckey)
            if hit is not None and hit[0] == _module_sig(path, hit[1]):
                sys.modules[module_name] = hit[1]
                _IMPORT_REGISTRY[module_name] = hit[1]
                return hit[1]
        return _exec_fresh(path, module_name, ckey, fresh, debug)


def _exec_fresh(path: Path, module_name: str, ckey: str, fresh: bool, debug: bool) -> Any:
    if debug:
        print(f"[IMPORT-PYP] Loading module: {module_name}")
    
    # Create module spec
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create module spec for: {path}")
    
    # Load module
    module = importlib.util.module_from_spec(spec)
    
    # Register in sys.modules (important for relative imports)
    sys.modules[module_name] = module
    
    # Execute module
    spec.loader.exec_module(module)
    
    # Register in our registry
    _IMPORT_REGISTRY[module_name] = module

    # Cache only after a clean exec (a failed exec raises above and is never
    # cached). Signature is taken now so __ipb_deps__ set at import counts.
    if not fresh and not getattr(module, "__ipb_nocache__", False):
        _MODULE_CACHE[ckey] = (_module_sig(path, module), module)
    
    if debug:
        print(f"[IMPORT-PYP] Module loaded: {module_name}")
    
    return module


# ===============================================================================
# Function Import
# ===============================================================================

# ===============================================================================
# Fallback Strategy Functions
# ===============================================================================

def _wrap_result(
    result_dict: Dict[str, Any],
    inject_globals: bool = True,
    debug: bool = False
) -> Any:
    """
    Wrap result dict in ImportedModule, with auto-unwrap for single items.
    
    If result contains only one item, return it directly (unwrapped).
    This allows natural usage:
        ut = u.ipd("module : ut")
        ut.now()  # ✅ Direct call
    
    Also supports auto-inject without assignment:
        u.ipd("module : ut")  # No assignment
        ut.now()              # ✅ Still works (auto-injected)
    
    Args:
        result_dict: Dict of name -> value
        inject_globals: Inject into caller's namespace
        debug: Print debug messages
        
    Returns:
        Single item (unwrapped) if len==1, else ImportedModule (wrapped)
    """
    # Inject to globals FIRST (before unwrapping)
    # This ensures auto-inject works even without assignment
    if inject_globals:
        import inspect
        frame = inspect.currentframe()
        try:
            # Need to go up multiple levels:
            # 0: _wrap_result (current)
            # 1: _import_pyp_smart
            # 2: import_pyp
            # 3: (wrapper functions)
            # ...
            # N: User's code
            
            # Strategy: Find the __main__ module frame
            current = frame
            target_frame = None
            
            while current is not None:
                if current.f_globals.get('__name__') == '__main__':
                    target_frame = current
                    break
                current = current.f_back
            
            # Inject into target frame
            if target_frame:
                target_frame.f_globals.update(result_dict)
                if debug:
                    print(f"[IMPORT-PYP] Auto-injected {list(result_dict.keys())} to globals")
        finally:
            del frame
    
    # Auto-unwrap for single item
    if len(result_dict) == 1:
        if debug:
            item_name = list(result_dict.keys())[0]
            print(f"[IMPORT-PYP] Single item '{item_name}' detected, auto-unwrapping")
        
        return list(result_dict.values())[0]
    
    # Multiple items → wrap in ImportedModule
    if debug:
        print(f"[IMPORT-PYP] Multiple items ({len(result_dict)}), wrapping in ImportedModule")
    
    return ImportedModule(result_dict, inject_globals=False)  # Already injected above


def _exec_module_and_pick(path: Path, names: List[str], debug: bool = False) -> Dict[str, Any]:
    """
    Execute full module and extract requested names.
    
    This is the SAFE fallback - always works but executes entire module.
    Used when:
    - Requested items are not functions (variables, classes, instances)
    - Selective extraction fails due to complex dependencies
    
    Args:
        path: Path to Python file
        names: List of names to extract (functions, variables, classes, etc.)
        debug: Print debug messages
        
    Returns:
        Dict mapping names to their values
        
    Raises:
        RuntimeError: If module execution fails or names not found
    """
    if debug:
        print(f"[IMPORT-PYP] Full module execution fallback")
        print(f"[IMPORT-PYP] Extracting: {names}")
    
    # Read source
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Cannot read file {path}: {e}")
    
    # Execute full module
    namespace = {}
    try:
        exec(src, namespace)
    except Exception as e:
        raise RuntimeError(f"Cannot execute module {path}: {e}")
    
    # Extract requested names
    result = {}
    missing = []
    
    for name in names:
        if name in namespace:
            result[name] = namespace[name]
        else:
            missing.append(name)
    
    if missing:
        available = [k for k in namespace.keys() if not k.startswith('_')]
        raise RuntimeError(
            f"Names not found in module {path}: {missing}\n"
            f"Available names: {available[:20]}"  # Show first 20
        )
    
    if debug:
        print(f"[IMPORT-PYP] Successfully extracted {len(result)} items")
    
    return result


def _import_pyp_smart(
    path: Path,
    names: List[str],
    auto_inject: bool = True,
    debug: bool = False
) -> ImportedModule:
    """
    Smart import with automatic fallback.
    
    Strategy:
    1. Validate if all requested names are functions
    2. If not (variables, classes, etc.) → use full module execution (safe path)
    3. If yes (all functions) → try selective extraction (fast path)
    4. If selective fails → fallback to full module (safe path)
    
    This ensures 100% reliability while optimizing for the common case.
    
    Args:
        path: Path to Python file
        names: List of names to import
        auto_inject: Auto-inject into caller's namespace
        debug: Print debug messages
        
    Returns:
        ImportedModule with requested items
    """
    
    # Read source for validation
    try:
        src = path.read_text(encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"Cannot read file {path}: {e}")
    
    # Step 1: Validate requested names
    from usekit.classes.data.base.post.sub.parser_pyp_sub import _validate_function_exists
    
    validation = _validate_function_exists(src, names)
    
    # Step 2: If any name is not a function → use full module execution
    if validation["missing"]:
        if debug:
            print(f"[IMPORT-PYP] Non-function items detected: {validation['missing']}")
            print(f"[IMPORT-PYP] Valid functions: {validation['valid']}")
            print(f"[IMPORT-PYP] Strategy: Full module execution (safe path)")
        
        result_dict = _exec_module_and_pick(path, names, debug=debug)
        
        # Register in global registry
        module_name = path.stem
        for name, obj in result_dict.items():
            registry_key = f"{module_name}.{name}"
            _IMPORT_REGISTRY[registry_key] = obj
        
        return _wrap_result(result_dict, inject_globals=auto_inject, debug=debug)
    
    # Step 3: All are functions → try selective extraction (fast path)
    if debug:
        print(f"[IMPORT-PYP] All items are functions: {validation['valid']}")
        print(f"[IMPORT-PYP] Strategy: Selective extraction (fast path)")
    
    try:
        executable_code = extract_executable(
            file=path,
            func_names=names,
            include_imports=True,
            include_decorators=True
        )
        
        if debug:
            print(f"[IMPORT-PYP] Executable code length: {len(executable_code)} chars")
        
        # Execute extracted code
        namespace = {}
        exec(executable_code, namespace)
        
        # Extract results
        result_dict = {}
        missing = []
        
        for name in names:
            if name in namespace:
                result_dict[name] = namespace[name]
            else:
                missing.append(name)
        
        if missing:
            raise RuntimeError(f"Functions not in namespace after exec: {missing}")
        
        if debug:
            print(f"[IMPORT-PYP] Selective extraction successful")
        
        # Register in global registry
        module_name = path.stem
        for name, obj in result_dict.items():
            registry_key = f"{module_name}.{name}"
            _IMPORT_REGISTRY[registry_key] = obj
        
        return _wrap_result(result_dict, inject_globals=auto_inject, debug=debug)
        
    except Exception as e:
        # Step 4: Selective extraction failed → fallback to full module
        if debug:
            print(f"[IMPORT-PYP] Selective extraction failed: {e}")
            print(f"[IMPORT-PYP] Strategy: Full module execution (fallback)")
        
        result_dict = _exec_module_and_pick(path, names, debug=debug)
        
        # Register in global registry
        module_name = path.stem
        for name, obj in result_dict.items():
            registry_key = f"{module_name}.{name}"
            _IMPORT_REGISTRY[registry_key] = obj
        
        return _wrap_result(result_dict, inject_globals=auto_inject, debug=debug)


# ===============================================================================
# Import Functions (Original - kept for backward compatibility)
# ===============================================================================

def _import_functions(
    path: Path,
    func_list: List[str],
    auto_inject: bool = True,
    debug: bool = False
) -> ImportedModule:
    """
    Import specific functions from a Python module.
    
    This creates individual executable blocks for each function,
    allowing selective import without loading entire module.
    
    ALWAYS provides both:
    - Object with attribute/dict access (m.add or m['add'])
    - Global namespace injection (add directly callable)
    
    Args:
        path: Python file path
        func_list: List of function names to import
        auto_inject: If True, inject functions into global namespace (default: True)
        debug: Debug mode
        
    Returns:
        ImportedModule wrapper supporting attribute and dict access
        
    Raises:
        ValueError: If any function not found
        
    Examples:
        >>> m = _import_functions(Path("utils.pyp"), ["add", "sub"])
        >>> m.add(1, 2)      # attribute access
        3
        >>> m['sub'](5, 3)   # dict access
        2
        >>> add(1, 2)        # also works - auto-injected!
        3
    """
    
    module_name = path.stem
    
    if debug:
        print(f"[IMPORT-PYP] Extracting functions from {module_name}: {func_list}")
    
    result = {}
    
    for func_name in func_list:
        if debug:
            print(f"[IMPORT-PYP] Processing function: {func_name}")
        
        # Extract executable code for this function
        # This includes function definition + required imports
        try:
            executable_code = extract_executable(
                file=path,
                func_names=func_name,  # Single function
                include_imports=True,
                include_decorators=True
            )
        except Exception as e:
            raise ValueError(
                f"Cannot extract function '{func_name}' from {path}: {e}"
            )
        
        if debug:
            print(f"[IMPORT-PYP] Executable code length: {len(executable_code)} chars")
        
        # Create isolated namespace for execution
        namespace = {}
        
        try:
            exec(executable_code, namespace)
        except Exception as e:
            raise RuntimeError(
                f"Cannot execute function '{func_name}' from {path}: {e}"
            )
        
        # Extract the function object
        if func_name not in namespace:
            raise ValueError(
                f"Function '{func_name}' not found in execution namespace"
            )
        
        func_obj = namespace[func_name]
        result[func_name] = func_obj
        
        # Register in global registry
        registry_key = f"{module_name}.{func_name}"
        _IMPORT_REGISTRY[registry_key] = func_obj
        
        if debug:
            print(f"[IMPORT-PYP] Function imported: {func_name}")
    
    if debug:
        print(f"[IMPORT-PYP] All functions imported: {list(result.keys())}")
    
    # Wrap in ImportedModule for attribute access
    # auto_inject will trigger global namespace injection if not assigned
    return ImportedModule(result, inject_globals=auto_inject)


# ===============================================================================
# Main Import Entry Point
# ===============================================================================

@log_and_raise
def import_pyp(
    path: Path,
    func_list: List[str] | None = None,
    from_list: List[str] | None = None,  # Future: from X import Y
    as_name: str | None = None,          # Future: import X as Y
    lazy: bool = False,                  # Future: lazy loading
    auto_inject: bool = True,            # Always inject to globals by default
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Import Python module or functions.
    
    Single Responsibility: Perform actual import operation
    
    SUB layer guarantees:
    - path exists and is valid
    - func_list is parsed (["f1", "f2"] or None)
    - All parameters are validated
    
    POST layer responsibility:
    - Import module OR functions
    - Register in global namespace
    - Handle errors gracefully
    
    ALWAYS provides both (when auto_inject=True, default):
    - Object with attribute/dict access
    - Global namespace injection
    
    Args:
        path: Python file path (guaranteed to exist)
        func_list: List of function names (None = import entire module)
        from_list: Reserved for future use
        as_name: Reserved for future use
        lazy: Reserved for future use
        auto_inject: If True, inject functions to globals (default: True)
        debug: Debug mode
        **kwargs: Additional options
        
    Returns:
        - If func_list is None: module object
        - If func_list provided: ImportedModule wrapper (supports m.func() and m['func']())
        
    Raises:
        ImportError: If module cannot be imported
        ValueError: If any function not found
        
    Examples:
        # Import entire module
        >>> mod = import_pyp(Path("utils.pyp"))
        >>> mod.add(1, 2)
        3
        
        # Import specific functions - BOTH ways work!
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add", "sub"])
        >>> m.add(1, 2)        # object attribute access
        3
        >>> add(1, 2)          # direct global call
        3
        >>> m['sub'](5, 3)     # object dict access
        2
        >>> sub(5, 3)          # direct global call
        2
        
        # Disable auto-inject if needed
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add"], auto_inject=False)
        >>> m.add(1, 2)        # works
        3
        >>> add(1, 2)          # NameError - not injected
        
        # Multiple functions
        >>> m = import_pyp(Path("utils.pyp"), func_list=["add", "sub", "mul"])
        >>> len(m)
        3
        >>> list(m)
        ['add', 'sub', 'mul']
    """
    
    if debug:
        print(f"[IMPORT-PYP] Starting import from: {path}")
        if func_list:
            print(f"[IMPORT-PYP] Target functions: {func_list}")
    
    # Future features (not implemented yet)
    if from_list is not None:
        raise NotImplementedError("from_list is not yet supported")
    if as_name is not None:
        raise NotImplementedError("as_name is not yet supported")
    if lazy:
        raise NotImplementedError("lazy import is not yet supported")
    
    # Determine import mode
    if func_list is None or len(func_list) == 0:
        # Import entire module
        if debug:
            print("[IMPORT-PYP] Mode: full module import")
        result = _import_module(path, debug=debug)
    else:
        # Import specific items with smart fallback
        if debug:
            print(f"[IMPORT-PYP] Mode: selective import ({len(func_list)} items)")
        
        # Use smart fallback strategy
        result = _import_pyp_smart(
            path=path,
            names=func_list,
            auto_inject=auto_inject,
            debug=debug
        )
    
    if debug:
        print("[IMPORT-PYP] Import completed successfully")
    
    return result


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "import_pyp",
    "ImportedModule",
    "get_registry",
    "clear_registry",
    "call",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
