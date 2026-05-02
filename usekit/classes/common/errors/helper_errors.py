# Path: usekit.classes.common.errors.helper_errors.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is emotion —
# ----------------------------------------------------------------------------------------------- #

class LoaderError(RuntimeError):
    """Base exception for all loader-related errors raised by loader modules."""
    pass
    
from usekit.classes.common.utils.helper_const import get_const

def get_debug_option(key):
    value = get_const(f'DEBUG_OPTIONS.{key}')
    if isinstance(value, str):
        return value.lower() in ('1', 'true', 'yes', 'on')
    return bool(value)

# Example
# debug_json = get_debug_option('json')
# print(f\"DEBUG_OPTIONS.json: {debug_json}\")  # False (bool)