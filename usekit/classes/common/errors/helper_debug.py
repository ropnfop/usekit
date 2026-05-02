# Path: usekit.classes.common.errors.helper_debug.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  This module provides debugging utilities and a decorator for conditional error logging.
# ----------------------------------------------------------------------------------------------- #

import logging
import os
import traceback
from functools import wraps
from usekit.classes.common.errors.helper_errors import LoaderError
from usekit.classes.common.utils.helper_const import get_const

# Basic logger setup (logs stream to stdout)
logger = logging.getLogger("loader")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Set logging level to DEBUG if LOADER_DEBUG=1 (env var)
logger.setLevel(logging.DEBUG if os.getenv("LOADER_DEBUG") == "1" else logging.INFO)

def get_debug_option_helper():
    """
    Returns whether DEBUG_OPTIONS.helper is enabled in sys_const.yaml.
    """
    return get_debug_option_for("helper")

def get_debug_option_for(format_key: str) -> bool:
    """
    Generic debug flag checker based on the format key.
    Accepts 'json', 'yaml', 'helper', etc.
    Returns True if the corresponding debug option is enabled in sys_const.yaml.
    """
    try:
        value = get_const(f'DEBUG_OPTIONS.{format_key}')
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes', 'on')
        return bool(value)
    except Exception:
        return False

def log_and_raise(fn):
    """
    Decorator: If DEBUG_OPTIONS.helper is enabled,
    wraps a function to log and re-raise exceptions in LoaderError form.
    If not enabled, it behaves as a passthrough (returns fn).
    """
    if not get_debug_option_helper():
        return fn

    @wraps(fn)
    def _wrap(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            logger.error("[%s] %s: %s", fn.__name__, exc.__class__.__name__, exc)
            logger.debug("".join(traceback.format_exc()))
            raise LoaderError(str(exc)) from exc
    return _wrap

def debug_print(message: str, format_key: str = 'helper'):
    """
    Print debug messages if the corresponding format debug flag is enabled.
    Useful for conditional trace logging across formats like 'json', 'yaml', etc.
    """
    if get_debug_option_for(format_key):
        print(message)