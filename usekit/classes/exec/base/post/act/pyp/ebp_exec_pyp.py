# Path: usekit.classes.exec.base.post.act.pyp.ebp_exec_pyp.py
# -----------------------------------------------------------------------------------------------
#  PYP Execution Handler - EXEC MODE ONLY
#  Created by: THE Little Prince × ROP × FOP
#
#  Single Responsibility: Execute Python functions from .pyp files
#  
#  Changes from original:
#  - REMOVED: import mode (moved to ebi_import_pyp.py)
#  - REMOVED: boot mode (moved to ebb_boot_pyp.py)
#  - KEPT: exec mode only (single action)
#  - SIMPLIFIED: No mode branching
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, Union
import importlib.util
import sys

from usekit.classes.common.errors.helper_debug import log_and_raise


# ===============================================================================
# Module Loading (Private Utility)
# ===============================================================================

def _load_module_from_path(
    path: Path,
    module_name: Optional[str] = None,
    reload: bool = False
) -> Any:
    """
    Dynamically load module from file path.
    
    Args:
        path: Path to .pyp file
        module_name: Custom module name (default: file stem)
        reload: Reload if already imported
        
    Returns:
        Loaded module object
    """
    
    if module_name is None:
        module_name = path.stem
    
    # Check if already loaded
    if module_name in sys.modules:
        if reload:
            return importlib.reload(sys.modules[module_name])
        else:
            return sys.modules[module_name]
    
    # Load new module
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from: {path}")
    
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    
    return module


def _execute_function(
    module: Any,
    func_name: str,
    args: tuple,
    kwargs: dict,
    debug: bool
) -> Any:
    """
    Execute function from module.
    
    Args:
        module: Module object
        func_name: Function name to execute
        args: Positional arguments
        kwargs: Keyword arguments
        debug: Debug mode
        
    Returns:
        Function execution result
    """
    
    if not hasattr(module, func_name):
        raise AttributeError(
            f"Module '{module.__name__}' has no function '{func_name}'"
        )
    
    func = getattr(module, func_name)
    
    if not callable(func):
        raise TypeError(f"'{func_name}' is not callable")
    
    if debug:
        print(f"[PYP-EXEC] Executing: {func_name}()")
        print(f"[PYP-EXEC]   args: {args}")
        print(f"[PYP-EXEC]   kwargs: {kwargs}")
    
    return func(*args, **kwargs)


# ===============================================================================
# Inline Execution (Alternative to sys.modules)
# ===============================================================================

def _execute_inline_code(
    code: str,
    func_name: str,
    args: tuple,
    kwargs: dict,
    debug: bool
) -> Any:
    """
    Execute inline Python code string.
    
    Used when inline=True (no sys.modules pollution).
    
    Args:
        code: Python code string
        func_name: Function name to execute
        args: Positional arguments
        kwargs: Keyword arguments
        debug: Debug mode
        
    Returns:
        Execution result
    """
    
    namespace = {}
    
    # Execute code to define functions/classes
    exec(code, namespace)
    
    # Execute specific function
    if func_name not in namespace:
        raise NameError(
            f"Function '{func_name}' not found in executed code"
        )
    
    func = namespace[func_name]
    
    if not callable(func):
        raise TypeError(f"'{func_name}' is not callable")
    
    if debug:
        print(f"[PYP-INLINE] Executing: {func_name}()")
        print(f"[PYP-INLINE]   args: {args}")
        print(f"[PYP-INLINE]   kwargs: {kwargs}")
    
    return func(*args, **kwargs)


# ===============================================================================
# Main PYP Execution Handler (EXEC MODE ONLY)
# ===============================================================================

@log_and_raise
def exec_pyp(
    path: Union[str, Path],
    func: Optional[str] = None,
    args: tuple = (),
    kwargs_exec: dict = None,
    *,
    reload: bool = False,
    safe: bool = True,
    inline: bool = False,
    module_name: Optional[str] = None,
    debug: bool = False,
    **kwargs
) -> Any:
    """
    Execute Python function or script from .pyp file.
    
    Single Responsibility: Execute and return result
    
    Execution Modes:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Function execution (func provided): Execute specific function
    2. Script execution (func=None): Execute entire script (if __name__ == "__main__")
    
    Execution Strategies:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. Standard (inline=False): Import module → Execute
       - Module cached in sys.modules
       - Faster for repeated calls
       - Use reload=True to refresh
    
    2. Inline (inline=True): Execute in isolated namespace
       - No sys.modules pollution
       - Isolated namespace
       - Slower but cleaner
    
    Args:
        path: Path to .pyp file (guaranteed to exist by OPS layer)
        func: Function name to execute (None for script execution)
        args: Positional arguments
        kwargs_exec: Keyword arguments dict
        reload: Reload module if already imported
        safe: Safe execution mode (future - sandboxing)
        inline: Execute as inline code (no sys.modules)
        module_name: Custom module name for import
        debug: Debug mode
        **kwargs: Additional options (ignored for now)
        
    Returns:
        - Function execution: Function result
        - Script execution: None (prints to stdout)
        
    Raises:
        AttributeError: If function not found
        TypeError: If function not callable
        
    Examples:
        # Execute function
        >>> exec_pyp(Path("utils.pyp"), func="clean_data", args=(data,))
        cleaned_data
        
        # Execute script
        >>> exec_pyp(Path("hello.pyp"))  # Runs if __name__ == "__main__" block
        None
        
        # Inline execution
        >>> exec_pyp(Path("temp.pyp"), func="process", inline=True, args=(x,))
        result
    """
    
    if kwargs_exec is None:
        kwargs_exec = {}
    
    path_obj = Path(path) if isinstance(path, str) else path
    
    if debug:
        print(f"[PYP-EXEC] Path: {path_obj}")
        print(f"[PYP-EXEC] Function: {func}")
        print(f"[PYP-EXEC] Inline: {inline}")
    
    # Case 1: Script execution (no function specified)
    if func is None:
        if debug:
            print(f"[PYP-EXEC] Script execution mode")
        
        # Execute script directly with __name__ = "__main__"
        # No parser needed - exec() can read file content directly
        namespace = {'__name__': '__main__'}
        exec(path_obj.read_text(encoding='utf-8'), namespace)
        return None
    
    # Case 2: Function execution
    if inline:              
        from usekit.classes.data.base.post.parser.parser_pyp import load as pyp_load
        from usekit.classes.data.base.post.sub.parser_pyp_sub import \
            _extract_function_with_imports
        
        code = pyp_load(path_obj)
        
        func_info = _extract_function_with_imports(
            code,
            func,
            include_decorators=True
        )
        
        if func_info is None:
            raise ValueError(
                f"Function '{func}' not found in {path_obj.name}"
            )
        
        return _execute_inline_code(
            func_info["executable_code"],
            func,
            args,
            kwargs_exec,
            debug
        )
    
    # Standard execution: Import then execute function
    module = _load_module_from_path(path_obj, module_name, reload)
    
    return _execute_function(
        module,
        func,
        args,
        kwargs_exec,
        debug
    )


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "exec_pyp",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
