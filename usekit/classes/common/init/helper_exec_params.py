# Path: usekit.infra.helper_exec_params.py
# -----------------------------------------------------------------------------------------------
#  EXEC Parameter Helper Functions
#  Created by: THE Little Prince × ROP × FOP
#  Version: 1.0
#
#  Logic functions for exec_signature
#  - Parameter extraction and merging
#  - dp alias handling
#  - Name pattern parsing
#  - Validation functions
#  - keydata path detection
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, List, Tuple, Dict
import warnings

# Import from exec_signature (absolute import for testing, can be relative in package)
try:
    from .exec_signature import (
        ALL_DEFAULTS,
        USER_LAYER,
        TARGETING_LAYER,
        SYSTEM_LAYER,
        VALID_OPS,
        VALID_KEY_TYPES,
    )
except ImportError:
    # Fallback for standalone testing
    from exec_signature import (
        ALL_DEFAULTS,
        USER_LAYER,
        TARGETING_LAYER,
        SYSTEM_LAYER,
        VALID_OPS,
        VALID_KEY_TYPES,
    )


# ===============================================================================
# Parameter Extraction Functions
# ===============================================================================

def get_exec_params(**kwargs) -> dict:
    """
    Extract and validate all EXEC parameters.
    Automatically handles 'dp' as alias for 'dir_path'.
    
    Examples:
        >>> p = get_exec_params(name="run", dp="aa/bb/cc")
        >>> p["dir_path"]  # "aa/bb/cc" (dp auto-aliased)
        
        >>> p = get_exec_params(name="run", dir_path="aa/bb")
        >>> p["dir_path"]  # "aa/bb"
    """
    params = ALL_DEFAULTS.copy()
    
    # Handle dp → dir_path alias (dp takes precedence if both provided)
    if "dp" in kwargs:
        kwargs["dir_path"] = kwargs.pop("dp")
    
    params.update(kwargs)
    return params


def get_user_layer(**kwargs) -> dict:
    """Extract USER layer parameters."""
    params = get_exec_params(**kwargs)
    return {k: params.get(k, v) for k, v in USER_LAYER.items()}


def get_targeting_layer(**kwargs) -> dict:
    """Extract TARGETING layer parameters."""
    params = get_exec_params(**kwargs)
    return {k: params.get(k, v) for k, v in TARGETING_LAYER.items()}


def get_system_layer(**kwargs) -> dict:
    """Extract SYSTEM layer parameters."""
    params = get_exec_params(**kwargs)
    return {k: params.get(k, v) for k, v in SYSTEM_LAYER.items()}


# ===============================================================================
# Operation-Specific Parameter Helpers
# ===============================================================================

def params_for_import(**kwargs) -> dict:
    """
    Get parameters for import operation.
    
    Examples:
        # Simple import
        params_for_import(name="pandas")
        
        # Module from path
        params_for_import(name="my_module", dp="aa/bb/cc")
        
        # From import
        params_for_import(name="numpy", from_list=["array", "zeros"])
        
        # Import as
        params_for_import(name="pandas", as_name="pd")
    """
    params = get_exec_params(**kwargs)
    params["mode"] = "import"
    return params


def params_for_exec(**kwargs) -> dict:
    """
    Get parameters for exec operation.
    
    Examples:
        # Execute function
        params_for_exec(name="run", dp="aa/bb/cc", args=(1, 2))
        
        # Execute with module path
        params_for_exec(name="dd.ee:run", dp="aa/bb", kwargs={"debug": True})
        
        # Execute from specific file
        params_for_exec(name="fn_run", path="/full/path/to/file.py")
    """
    params = get_exec_params(**kwargs)
    params["mode"] = "exec"
    return params


def params_for_boot(**kwargs) -> dict:
    """
    Get parameters for boot operation.
    
    Examples:
        # Boot with config
        params_for_boot(config_path="config.yaml")
        
        # Boot with init args
        params_for_boot(init_args={"debug": True, "port": 8080})
    """
    params = get_exec_params(**kwargs)
    params["mode"] = "boot"
    return params


def params_for_quit(**kwargs) -> dict:
    """
    Get parameters for quit operation.
    
    Examples:
        # Simple quit
        params_for_quit()
        
        # Quit with cleanup
        params_for_quit(safe=True)
    """
    params = get_exec_params(**kwargs)
    params["mode"] = "quit"
    return params


# ===============================================================================
# Validation Functions
# ===============================================================================

def validate_op(op: str, mode: str) -> bool:
    """
    Validate if operation matches mode.
    
    Args:
        op: Operation name (e.g., "ijb", "xjb")
        mode: Mode name (e.g., "import", "exec")
    
    Returns:
        True if valid, False otherwise
    """
    valid_ops = VALID_OPS.get(mode, [])
    return op in valid_ops


def get_valid_ops(mode: str) -> List[str]:
    """
    Get valid operations for a mode.
    
    Args:
        mode: Mode name
    
    Returns:
        List of valid operation names
    """
    return VALID_OPS.get(mode, [])


def validate_key_type(key_type: str) -> bool:
    """
    Validate key_type value for helper_keydata_path integration.
    
    Args:
        key_type: Key type to validate
    
    Returns:
        True if valid, False otherwise
    """
    return key_type in VALID_KEY_TYPES


def warn_invalid_key_type(key_type: str):
    """
    Warn if invalid key_type is provided.
    
    Args:
        key_type: Key type to check
    """
    if not validate_key_type(key_type):
        warnings.warn(
            f"Invalid key_type '{key_type}'. Valid options: {VALID_KEY_TYPES}. "
            f"Defaulting to 'auto'.",
            UserWarning,
            stacklevel=2
        )


# ===============================================================================
# Name Pattern Parsing
# ===============================================================================

def parse_exec_name(name: str) -> dict:
    """
    Parse execution name into module and function components.
    
    Pattern: "module.path:func1, func2, func3" or "func1, func2"
    
    Args:
        name: Execution name string
    
    Returns:
        Dictionary with:
        - module: Module path (None if no module)
        - funcs: List of function names
        - func: First function name (convenience)
        - has_module: Whether module path exists
        - multi_func: Whether multiple functions specified
    
    Examples:
        >>> parse_exec_name("aby.ghh:run")
        {'module': 'aby.ghh', 'funcs': ['run'], 'func': 'run', 
         'has_module': True, 'multi_func': False}
        
        >>> parse_exec_name("aaa.bb:as, bb, cc")
        {'module': 'aaa.bb', 'funcs': ['as', 'bb', 'cc'], 'func': 'as',
         'has_module': True, 'multi_func': True}
        
        >>> parse_exec_name("fn1, fn2, fn3")
        {'module': None, 'funcs': ['fn1', 'fn2', 'fn3'], 'func': 'fn1',
         'has_module': False, 'multi_func': True}
    """
    if not name:
        return {
            "module": None,
            "funcs": [],
            "func": None,
            "has_module": False,
            "multi_func": False
        }
    
    # Check for module:function separator
    if ":" in name:
        module_part, func_part = name.split(":", 1)
        module = module_part.strip()
        func_str = func_part.strip()
    else:
        module = None
        func_str = name.strip()
    
    # Parse function list (comma-separated)
    if "," in func_str:
        funcs = [f.strip() for f in func_str.split(",") if f.strip()]
    else:
        funcs = [func_str] if func_str else []
    
    return {
        "module": module,
        "funcs": funcs,
        "func": funcs[0] if funcs else None,
        "has_module": module is not None,
        "multi_func": len(funcs) > 1
    }


# ===============================================================================
# helper_keydata_path Integration Utilities
# ===============================================================================

def has_keydata_path(params: dict) -> bool:
    """
    Check if parameters include keydata for helper_keydata_path integration.
    
    This enables using helper_search and helper_path to resolve paths
    based on keydata instead of explicit dir_path.
    
    Args:
        params: Parameter dictionary
    
    Returns:
        True if keydata is provided and not None
    
    Examples:
        >>> has_keydata_path({"keydata": "config/db"})
        True
        >>> has_keydata_path({"keydata": None})
        False
        >>> has_keydata_path({"name": "run"})
        False
    """
    return params.get("keydata") is not None


def get_effective_dir_path(params: dict) -> Optional[str]:
    """
    Get effective directory path, prioritizing explicit dir_path over keydata.
    
    When keydata is provided without dir_path, this indicates that
    helper_keydata_path should be used to resolve the path.
    
    Args:
        params: Parameter dictionary
    
    Returns:
        - dir_path if explicitly provided
        - None if keydata is provided (signals helper_keydata_path usage)
        - None otherwise
    
    Examples:
        >>> get_effective_dir_path({"dir_path": "aa/bb"})
        'aa/bb'
        >>> get_effective_dir_path({"keydata": "config/db"})
        None  # Use helper_keydata_path
        >>> get_effective_dir_path({})
        None
    """
    # Explicit dir_path takes precedence
    if params.get("dir_path") is not None:
        return params["dir_path"]
    
    # If keydata provided, return None to signal helper_keydata_path usage
    if has_keydata_path(params):
        return None
    
    # No path information
    return None


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    # Parameter extractors
    "get_exec_params",
    "get_user_layer",
    "get_targeting_layer",
    "get_system_layer",
    
    # Operation helpers
    "params_for_import",
    "params_for_exec",
    "params_for_boot",
    "params_for_quit",
    
    # Validation
    "validate_op",
    "get_valid_ops",
    "validate_key_type",
    "warn_invalid_key_type",
    
    # Utilities
    "parse_exec_name",
    "has_keydata_path",
    "get_effective_dir_path",
]
