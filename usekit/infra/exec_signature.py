# Path: usekit.infra.exec_signature.py
# -----------------------------------------------------------------------------------------------
#  Universal Execution Signature
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0 - Complete with parameter processing functions
#
#  Structure: 3-layer parameter system + execution-specific options
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional, Union, Literal
import warnings

from usekit.infra.params_value import normalize_value_params

# ===============================================================================
# Type Definitions
# ===============================================================================

Loc = Union[Literal["base", "sub", "dir", "now", "tmp", "cus", "cache"], str]
ExecMode = Literal["import", "exec", "boot", "quit"]
KeyType = Literal["name", "path", "both", "auto", "def", "class"]


# ===============================================================================
# Layer 1: USER LAYER - Semantic inputs
# ===============================================================================

USER_LAYER = {
    "name": None,               # Module/function name (can use "@SRC/path:fn" syntax)
    "path": None,               # Direct file path (alternative to name)
    "dir_path": None,           # Directory path (dp is auto-aliased)
    "cus": None,                # Custom preset
    "keydata": None,            # Key path for helper_keydata_path integration
}


# ===============================================================================
# Layer 2: TARGETING LAYER - Execution options & filters
# ===============================================================================

TARGETING_LAYER = {
    # Execution arguments
    "args": None,               # Positional arguments tuple
    "kwargs": None,             # Keyword arguments dict
    "reload": False,            # Reload module before execution
    "safe": True,               # Safe execution mode
    
    # Import options
    "from_list": None,          # For "from X import Y1, Y2"
    "as_name": None,            # For "import X as Y"
    "lazy": False,              # Lazy import (defer until first use)
    
    # Boot options
    "init_args": None,          # Initialization arguments
    "config_path": None,        # Configuration file path
    
    # Search options (helper_keydata_path integration)
    "key_type": "auto",         # Key type: "name", "path", "both", "auto", "def", "class"
    "recursive": False,         # Recursive search in helper_search
    "find_all": False,          # Find all matches vs first match
    "walk": False,              # Recursive directory walk
    "case_sensitive": False,    # Case-sensitive search
    
    # Future features
    "k": None,
    "kv": None,
    "kc": "eq",
    "kf": None,
}


# ===============================================================================
# Layer 3: SYSTEM LAYER - Execution control
# ===============================================================================

SYSTEM_LAYER = {
    # Core execution
    "fmt": "pyp",               # Format (pyp, sql, ddl)
    "loc": "base",              # Location preset (base/sub/dir/now/tmp/cus/cache)
    "mod": None,                # Module filter (all/user/...)
    "ov_fmt": None,             # Format override (from @xx syntax)
    "ov_loc": None,             # Location override (from @xx syntax)
    "func": None,               # Function/entry name (canonical; fn is alias)
    "alias": None,              # Logical alias (non-inline, e.g. "SRC")
    "raw_name": None,           # Original name expression (for logging)
    "mode": "import",           # Mode: import/exec/boot/quit
    "mode_sub": None,           # Sub-mode for future extension
    "debug": False,             # Debug mode
    
    # Execution control
    "timeout": None,            # Execution timeout in seconds
    "cwd": None,                # Working directory
    "env": None,                # Environment variables dict
    "module_name": None,        # Custom module name for dynamic import
    "inline": False,            # Execute as inline code (without sys.modules)
    
    # Error handling
    "raise_errors": False,      # Raise errors instead of returning None
    "fallback": None,           # Fallback value on error
}


# ===============================================================================
# Unified defaults
# ===============================================================================

ALL_DEFAULTS = {
    **USER_LAYER,
    **TARGETING_LAYER,
    **SYSTEM_LAYER,
}


# ===============================================================================
# Valid values (constants)
# ===============================================================================

# Valid operations for each mode
VALID_OPS = {
    "import": ["ijb"],           # Import from base
    "exec": ["xjb"],             # Execute from base
    "boot": ["bjb"],             # Boot from base
    "quit": ["qjb"],             # Quit from base
}

# Valid key types for helper_keydata_path
VALID_KEY_TYPES = ["name", "path", "both", "auto", "def", "class"]

# Valid formats for execution
VALID_FORMATS = ["pyp", "sql", "ddl"]


# ===============================================================================
# Parameter Processing Functions
# ===============================================================================

def get_exec_params(**kwargs) -> dict:
    """
    Get execution parameters with defaults.
    
    This applies normalize_value_params to handle:
    - Name expressions: "@SRC/path:fn"
    - Inline codes: "@cs" → ov_fmt="csv", ov_loc="sub"
    - Function suffix: "mod:fn" → func="fn"
    
    Args:
        **kwargs: User-provided parameters
        
    Returns:
        Complete parameter dict with all defaults
        
    Examples:
        >>> p = get_exec_params(name="utils:clean_data")
        >>> p["name"]      # "utils"
        >>> p["func"]      # "clean_data"
        
        >>> p = get_exec_params(name="@cs.helpers/data:process")
        >>> p["ov_fmt"]    # "csv" (from inline code 'c')
        >>> p["ov_loc"]    # "sub" (from inline code 's')
        >>> p["dir_path"]  # "helpers"
        >>> p["name"]      # "data"
        >>> p["func"]      # "process"
    """
    # Apply value normalization (handles @syntax, :func, etc.)
    normalized = normalize_value_params(**kwargs)
    
    # Merge with defaults
    result = {**ALL_DEFAULTS, **normalized}
    
    return result


def get_user_layer(params: dict) -> dict:
    """Extract USER LAYER parameters only"""
    return {k: params.get(k, USER_LAYER[k]) for k in USER_LAYER.keys()}


def get_targeting_layer(params: dict) -> dict:
    """Extract TARGETING LAYER parameters only"""
    return {k: params.get(k, TARGETING_LAYER[k]) for k in TARGETING_LAYER.keys()}


def get_system_layer(params: dict) -> dict:
    """Extract SYSTEM LAYER parameters only"""
    return {k: params.get(k, SYSTEM_LAYER[k]) for k in SYSTEM_LAYER.keys()}


# ===============================================================================
# Convenience functions: operation-specific parameter extraction
# ===============================================================================

def params_for_exec(**kwargs) -> dict:
    """
    Execution operation parameters.
    
    Default mode: "exec"
    """
    if "mode" not in kwargs:
        kwargs["mode"] = "exec"
    return get_exec_params(**kwargs)


def params_for_import(**kwargs) -> dict:
    """
    Import operation parameters.
    
    Default mode: "import"
    """
    if "mode" not in kwargs:
        kwargs["mode"] = "import"
    return get_exec_params(**kwargs)


def params_for_boot(**kwargs) -> dict:
    """
    Boot operation parameters.
    
    Default mode: "boot"
    """
    if "mode" not in kwargs:
        kwargs["mode"] = "boot"
    return get_exec_params(**kwargs)


# ===============================================================================
# Future features check functions
# ===============================================================================

def has_future_features(params: dict) -> bool:
    """
    Check if future features (k, kv, kc, kf) are used.
    
    Returns:
        True if any future feature is used
    """
    return any([
        params.get("k") is not None,
        params.get("kv") is not None,
        params.get("kc")  is not None,
        params.get("kf") is not None,
    ])


def warn_future_features(params: dict):
    """Warn if future features are used"""
    if has_future_features(params):
        used = []
        if params.get("k") is not None:
            used.append(f"k={params['k']}")
        if params.get("kv") is not None:
            used.append(f"kv={params['kv']}")
        if params.get("kc")  is not None:
            used.append(f"kc={params['kc']}")
        if params.get("kf") is not None:
            used.append(f"kf={params['kf']}")
        
        warnings.warn(
            f"Future features ({', '.join(used)}) are not yet implemented. "
            f"They will be ignored for now.",
            FutureWarning,
            stacklevel=3
        )


# ===============================================================================
# Documentation: Layer descriptions
# ===============================================================================

EXEC_PARAMS_STRUCTURE = """
Universal Execution Parameter Structure (3 Layers):

    # ---------------------------------------------------------------
    # [1] USER LAYER - Semantic inputs
    # ---------------------------------------------------------------
    name: Optional[str] = None,     # "@SRC/path:fn" syntax supported
    path: Optional[str] = None,     # Direct file path
    dir_path: Optional[str] = None, # Directory path
    cus: Optional[str] = None,      # Custom preset
    keydata: Optional[str] = None,  # Key path
    
    # ---------------------------------------------------------------
    # [2] TARGETING LAYER - Execution options
    # ---------------------------------------------------------------
    *,
    # Execution
    args: Optional[tuple] = None,
    kwargs: Optional[dict] = None,
    reload: bool = False,
    safe: bool = True,
    
    # Import options
    from_list: Optional[list] = None,
    as_name: Optional[str] = None,
    lazy: bool = False,
    
    # Search options
    key_type: str = "auto",         # "name", "path", "both", "auto", "def", "class"
    recursive: bool = False,
    find_all: bool = False,
    walk: bool = False,
    case_sensitive: bool = False,
    
    # ---------------------------------------------------------------
    # [3] SYSTEM LAYER - Execution control
    # ---------------------------------------------------------------
    fmt: str = "pyp",               # "pyp", "sql", "ddl"
    loc: str = "base",
    mod: Optional[str] = None,
    ov_fmt: Optional[str] = None,   # Override from @syntax
    ov_loc: Optional[str] = None,   # Override from @syntax
    func: Optional[str] = None,     # Function/entry name
    mode: str = "import",           # "import", "exec", "boot", "quit"
    debug: bool = False,
    **kwargs
"""


LAYER_DOCS = {
    "USER_LAYER": """
    User perspective semantic inputs (What to execute)
    
    - name: Module/function name (supports "@SRC/path:fn" syntax)
    - path: Direct file path (alternative to name)
    - dir_path: Directory path
    - cus: Custom location preset
    - keydata: Key path for nested access
    """,
    
    "TARGETING_LAYER": """
    Execution options and filters (How to execute)
    
    Execution:
    - args: Positional arguments for function
    - kwargs: Keyword arguments for function
    - reload: Reload module before execution
    - safe: Safe execution mode
    
    Import:
    - from_list: List of names to import
    - as_name: Alias name for import
    - lazy: Lazy import (defer until use)
    
    Search:
    - key_type: "name", "path", "both", "auto", "def", "class"
    - recursive: Recursive search
    - find_all: Find all matches
    - walk: Recursive directory walk
    - case_sensitive: Case-sensitive search
    """,
    
    "SYSTEM_LAYER": """
    System-level execution control (System configuration)
    
    Core:
    - fmt: Format type (pyp, sql, ddl)
    - loc: Location preset (base/sub/dir/now/tmp/cus/cache)
    - mod: Module filter
    - ov_fmt: Format override (from inline @code)
    - ov_loc: Location override (from inline @code)
    - func: Function/entry name
    - mode: Execution mode (import/exec/boot/quit)
    - debug: Debug mode
    
    Control:
    - timeout: Execution timeout
    - cwd: Working directory
    - env: Environment variables
    - module_name: Custom module name
    - inline: Inline execution mode
    """
}


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    # Types
    "Loc",
    "ExecMode",
    "KeyType",
    
    # Layer definitions
    "USER_LAYER",
    "TARGETING_LAYER",
    "SYSTEM_LAYER",
    "ALL_DEFAULTS",
    
    # Valid values
    "VALID_OPS",
    "VALID_KEY_TYPES",
    "VALID_FORMATS",
    
    # Parameter functions
    "get_exec_params",
    "get_user_layer",
    "get_targeting_layer",
    "get_system_layer",
    "params_for_exec",
    "params_for_import",
    "params_for_boot",
    
    # Future features
    "has_future_features",
    "warn_future_features",
    
    # Documentation
    "EXEC_PARAMS_STRUCTURE",
    "LAYER_DOCS",
]