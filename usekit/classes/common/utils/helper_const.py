# Path: usekit.classes.common.utils
# File: helper_const.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  Version: v2.3-lazy-import (2025-10-29)
#  — memory is echo, performance is key —
# -----------------------------------------------------------------------------------------------

import os
import yaml
from pathlib import Path
import logging
from typing import Dict, Optional
from functools import lru_cache
from usekit.classes.core.env.loader_base_path import BASE_PATH

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# -----------------------------------------------------------------------------------------------
#  OPTIMIZATION: Lazy BASE_PATH loading
# -----------------------------------------------------------------------------------------------
_BASE_PATH_CACHE = None

def get_base_path() -> Path:
    """
    Lazy-load BASE_PATH only when actually needed.
    Avoids expensive import at module load time.
    """
    global _BASE_PATH_CACHE
    if _BASE_PATH_CACHE is None:
        from usekit.classes.core.env.loader_base_path import BASE_PATH
        _BASE_PATH_CACHE = Path(BASE_PATH)
    return _BASE_PATH_CACHE

# -----------------------------------------------------------------------------------------------
# Load sys_const.yaml (project configuration memory)
# -----------------------------------------------------------------------------------------------
def _get_sys_const_path() -> Path:
    """
    Determine sys_const.yaml path from environment or default.
    Priority:
    1. ENV_SYS_CONST_PATH (environment variable)
    2. Package-relative path (for PyPI distribution)
    3. BASE_PATH (for development environment)
    """
    # Priority 1: Explicit environment variable
    env_path = os.getenv("ENV_SYS_CONST_PATH") or ""
    if env_path:
        env_path_obj = Path(env_path)
        return env_path_obj / "sys_const.yaml" if env_path_obj.is_dir() else env_path_obj
    
    # Priority 2: Package-relative path (works in installed package)
    try:
        # Get the directory where this helper_const.py file is located
        current_file = Path(__file__).resolve()
        # Navigate: helper_const.py -> utils -> common -> classes -> usekit -> sys/sys_yaml
        package_root = current_file.parent.parent.parent.parent
        sys_const_path = package_root / "sys" / "sys_yaml" / "sys_const.yaml"
        if sys_const_path.exists():
            return sys_const_path
    except Exception:
        pass
    
    # Priority 3: Development environment using BASE_PATH
    return get_base_path() / "usekit/sys/sys_yaml/sys_const.yaml"

_sys_const_cache = None

@lru_cache(maxsize=1)
def get_sys_const() -> dict:
    """
    Load and cache the project configuration (sys_const.yaml).
    Uses lru_cache for extra safety against repeated calls.
    """
    global _sys_const_cache
    if _sys_const_cache is None:
        sys_const_path = _get_sys_const_path()
        if not sys_const_path.exists():
            raise FileNotFoundError(f"[SYS_CONST] File not found: {sys_const_path}")
        with sys_const_path.open("r", encoding="utf-8") as f:
            _sys_const_cache = yaml.safe_load(f)
    return _sys_const_cache

def clear_sys_const_cache():
    """Clear the cached sys_const.yaml data."""
    global _sys_const_cache
    _sys_const_cache = None
    get_sys_const.cache_clear()

@lru_cache(maxsize=128)
def get_const(key: str):
    """
    Access nested configuration values using dot notation, e.g. 'DATA_PATH.json'
    Cached to avoid repeated dictionary traversal.
    """
    const = get_sys_const()
    keys = key.split(".")
    for k in keys:
        if isinstance(const, dict) and k in const:
            const = const[k]
        else:
            raise KeyError(f"[CONST] '{key}' does not contain '{k}'")
    return const
    
def get_abs_const(key: str, base_path: str = None, root: str = None) -> Path:
    """
    Assemble a safe absolute path under BASE.
    If YAML value starts with '/', root is skipped.
    Else, BASE + root + subkey (all without duplicates).
    """
    try:
        base = Path(base_path).resolve() if base_path else get_base_path().resolve()
        val = str(get_const(key)).replace("\\", "/").strip()
        tokens = [t for t in Path(val.lstrip("/")).parts if t not in ("", ".")]

        # Split key to get section, for root lookup
        section = key.split('.', 1)[0]
        root_val = root.strip("/") if root else get_const(f"{section}.root").strip("/")

        parts = list(base.parts)
        if not val.startswith("/"):
            # Only insert root if YAML value does not start with '/'
            if root_val and root_val not in parts:
                parts.append(root_val)
        for t in tokens:
            if t not in parts:
                parts.append(t)
        final_path = Path(*parts)

        # Ensure result is inside BASE
        try:
            final_path.relative_to(base)
        except ValueError:
            raise ValueError(f"{final_path} is outside of BASE '{base}'")
        return final_path
    except Exception as e:
        logger.error(f"get_abs_const({key}): {e}")
        raise
        
# -----------------------------------------------------------------------------------------------
# Path helpers for current hierarchical YAML structure
# -----------------------------------------------------------------------------------------------

def get_sys_path(sub: Optional[str] = None) -> Path:
    """
    Return the absolute path for 'usekit/sys/[subfolder]'.
    sub can be 'yaml', 'json', etc.
    """
    root = get_const("SYS_PATH.root")      # "usekit/sys"
    if sub:
        folder = get_const(f"SYS_PATH.{sub}")  # "sys_yaml", "sys_json", etc.
        return get_base_path() / root / folder
    return get_base_path() / root

def get_data_path(fmt: str, sub: Optional[str] = None) -> Path:
    """
    Return the absolute path for 'data/[fmt]' or its subfolder.
    fmt: 'json', 'yaml', etc.
    sub: e.g., 'json_sub'
    """
    root = get_const("DATA_PATH.root")
    folder = get_const(f"DATA_PATH.{fmt}")
    path = get_base_path() / root / folder
    if sub:
        sub_folder = get_const(f"DATA_PATH.{sub}")
        return path / sub_folder
    return path

def get_dd_path(kind: str = "ddl", sub: Optional[str] = None) -> Path:
    """
    Return the absolute path for 'data/tables/[ddl|dml]/[sub]'.
    kind: 'ddl' or 'dml'
    """
    kind_uc = kind.upper()
    root = get_const(f"{kind_uc}_PATH.root")
    folder = get_const(f"{kind_uc}_PATH.{kind}")
    path = get_base_path() / root / folder
    if sub:
        sub_folder = get_const(f"{kind_uc}_PATH.{kind}_sub")
        return path / sub_folder
    return path

def get_sys_const_path() -> Path:
    """
    Return the full path to sys_const.yaml file.
    """
    sys_yaml_path = get_sys_path("yaml")
    return sys_yaml_path / "sys_const.yaml"

# -----------------------------------------------------------------------------------------------
# Format/extension helpers (for universal auto-format)
# -----------------------------------------------------------------------------------------------

@lru_cache(maxsize=32)
def get_extension(fmt: str) -> str:
    """
    Return the default file extension for the given format.
    """
    return get_const("EXTENSION_MAP").get(fmt, f".{fmt}")

@lru_cache(maxsize=32)
def resolve_format_section(fmt: str) -> str:
    """
    Map a format string (e.g., 'json') to its section key in sys_const.yaml
    """
    section = get_const("FORMAT_SECTION_MAP").get(fmt.lower())
    if not section:
        raise ValueError(f"[FORMAT] Unknown format type: {fmt}")
    return section

def get_format_info(fmt: str) -> Dict:
    """
    Return metadata for the given format (paths, extensions, names).
    """
    section = resolve_format_section(fmt)
    const = get_const(section)
    fmt_upper = fmt.upper()
    fmt_cap = fmt.capitalize()
    return {
        "KIND": fmt,
        "KIND_SUB": f"{fmt}01",
        "KIND_PATH": const.get(fmt),
        "KIND_SUB_PATH": const.get(f"{fmt}_sub"),
        "KIND_UPPER": fmt_upper,
        "KIND_CAPITAL": fmt_cap,
        "DEFAULT_EXTENSION": get_extension(fmt)
    }

# -----------------------------------------------------------------------------------------------
# Key filtering (for flexible dynamic config lookup)
# -----------------------------------------------------------------------------------------------

def filter_const(prefix: str = "", suffix: str = "", return_type: str = "dict", strict: bool = False) -> dict | list:
    """
    Filter configuration keys by prefix/suffix. 
    return_type: 'dict', 'keys', 'values', 'paths'
    """
    const = get_sys_const()
    prefix = prefix.upper()
    suffix = suffix.upper()
    result = {k: v for k, v in const.items() if k.upper().startswith(prefix) and k.upper().endswith(suffix)}
    if strict and not result:
        raise KeyError(f"[CONST] No values found for prefix={prefix}, suffix={suffix}")
    if return_type == "dict":
        return result
    elif return_type == "keys":
        return list(result.keys())
    elif return_type == "values":
        return list(result.values())
    elif return_type == "paths":
        base = get_base_path()
        return {k: base / Path(v) for k, v in result.items()}
    else:
        raise ValueError("return_type must be one of 'dict', 'keys', 'values', 'paths'")

# -----------------------------------------------------------------------------------------------
# [EOF] helper_const.py — USEKIT memory utility (optimized)
# -----------------------------------------------------------------------------------------------