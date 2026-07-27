# Path: usekit.classes.common.utils.helper_env.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# — memory is emotion —
# -----------------------------------------------------------------------------------------------
# Purpose:
#   .env file read/write utility.
#   Delegates file operations to manager_dotenv.
#   Auto-resolves .env path via loader_env.
#
#   Usage:
#       from usekit.classes.common.utils.helper_env import set_env, del_env, list_env, get_env_path
#
#       set_env("ANTHROPIC_API_KEY", "sk-ant-xxx")   # write to .env + os.environ
#       del_env("OLD_KEY")                            # remove from .env + os.environ
#       list_env()                                    # {key: masked_value, ...}
#       get_env_path()                                # Path to .env file
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Optional

# ========================================================================
# Internal: .env path resolution (cached)
# ========================================================================

_env_path_cache: Optional[Path] = None


def get_env_path() -> Optional[Path]:
    """
    Get the active .env file path.
    Uses loader_env.find_env_file() for reliable detection.

    Returns:
        Path to .env file, or None if not found
    """
    global _env_path_cache
    if _env_path_cache is not None:
        return _env_path_cache

    try:
        from usekit.classes.core.env.loader_env import find_env_file
        result = find_env_file(auto_copy=False, verbose=False)
        if result:
            _env_path_cache = Path(result)
            return _env_path_cache
    except Exception:
        pass

    return None


def clear_cache():
    """Clear cached .env path."""
    global _env_path_cache
    _env_path_cache = None


# ========================================================================
# Public: set / del / list
# ========================================================================

def set_env(key: str, value: str, verbose: bool = False) -> bool:
    """
    Write a key=value to .env file and update os.environ.

    Args:
        key: Variable name (e.g. 'ANTHROPIC_API_KEY')
        value: Variable value
        verbose: Print status

    Returns:
        True if saved successfully

    Example:
        set_env("ANTHROPIC_API_KEY", "sk-ant-xxx")
    """
    env_path = get_env_path()
    if not env_path:
        if verbose:
            print("[helper_env] No .env file found.")
        return False

    try:
        from usekit.classes.core.env.base.manager_dotenv import update_env_variable
        ok = update_env_variable(env_path, key, value)
        if ok:
            # Sync to os.environ immediately
            os.environ[key] = value
            if verbose:
                print(f"[helper_env] Saved: {key}")
        return ok
    except Exception as e:
        if verbose:
            print(f"[helper_env] Failed to save {key}: {e}")
        return False


def del_env(key: str, verbose: bool = False) -> bool:
    """
    Remove a key from .env file and os.environ.

    Args:
        key: Variable name to remove
        verbose: Print status

    Returns:
        True if removed successfully

    Example:
        del_env("OLD_API_KEY")
    """
    env_path = get_env_path()
    if not env_path:
        if verbose:
            print("[helper_env] No .env file found.")
        return False

    try:
        from usekit.classes.core.env.base.manager_dotenv import remove_env_variable
        ok = remove_env_variable(env_path, key)
        if ok:
            os.environ.pop(key, None)
            if verbose:
                print(f"[helper_env] Removed: {key}")
        return ok
    except Exception as e:
        if verbose:
            print(f"[helper_env] Failed to remove {key}: {e}")
        return False


def list_env(mask: bool = True) -> Dict[str, str]:
    """
    List all variables in .env file (not os.environ, just the file).

    Args:
        mask: Mask sensitive values (KEY, SECRET, TOKEN, etc)

    Returns:
        Dict of key-value pairs from .env file

    Example:
        list_env()
        # → {'ENV_BASE_PATH': '/storage/...', 'GOOGLE_API_KEY': 'AIz...qPg'}
    """
    env_path = get_env_path()
    if not env_path:
        return {}

    try:
        from usekit.classes.core.env.base.manager_dotenv import parse_dotenv
        raw = parse_dotenv(env_path)
        if not mask:
            return raw
        # Apply masking
        return {k: _mask(v) if _is_sensitive(k) else v for k, v in raw.items()}
    except Exception:
        return {}


# ========================================================================
# Internal: masking (shared pattern)
# ========================================================================

_SENSITIVE = ("KEY", "SECRET", "TOKEN", "PASSWORD", "PASS", "API")


def _mask(val: str, show: int = 3) -> str:
    """Mask sensitive value."""
    if not val:
        return ""
    if len(val) <= show * 2:
        return "***"
    return f"{val[:show]}...{val[-show:]}"


def _is_sensitive(key: str) -> bool:
    """Check if key name looks sensitive."""
    upper = key.upper()
    return any(pat in upper for pat in _SENSITIVE)


# ========================================================================
# Exports
# ========================================================================

__all__ = ["set_env", "del_env", "list_env", "get_env_path", "clear_cache"]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
