# Path: usekit.classes.common.errors.helper_safe.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is connection —
# -----------------------------------------------------------------------------------------------
#  Simplified Safe Wrapper: Deep chain protection with deferred error handling
#  Philosophy: Wrap everything in the chain, catch errors only at final call
# -----------------------------------------------------------------------------------------------

import types
from usekit.classes.common.utils.helper_const import get_const

def get_debug_option_safer():
    """Check debug flag for safe wrapper."""
    try:
        value = get_const('DEBUG_OPTIONS.safer')
        if isinstance(value, str):
            return value.lower() in ('1', 'true', 'yes', 'on')
        return bool(value)
    except Exception:
        return True

DEBUG = get_debug_option_safer()

# ===============================================================================
# Simplified Safe Wrapper
# ===============================================================================

class SafeWrapper:
    """
    Deep chain safe wrapper with deferred error handling.
    
    Philosophy:
        - Wrap every intermediate step in the chain
        - Only catch exceptions at the final __call__ point
        - Simple, fast, and covers all cases
    
    This approach is superior because:
        1. Errors naturally propagate to the final call
        2. No need to wrap individual methods with try-except
        3. Minimal performance overhead
        4. Easy to understand and maintain
    
    Examples
    --------
    >>> # All intermediate steps are wrapped, errors caught at final call
    >>> safe.read.json.base("no_file")  # → None (FileNotFoundError caught)
    >>> safe.rjb("no_file")             # → None (FileNotFoundError caught)
    >>> 
    >>> # Normal use throws errors as expected
    >>> use.read.json.base("no_file")   # → FileNotFoundError raised
    """
    
    def __init__(self, target, mode='safe', default=None):
        """
        Initialize safe wrapper.
        
        Parameters
        ----------
        target : any
            Object to wrap with safe error handling
        mode : str, default='safe'
            'safe' returns default on error, 'raise' re-raises exceptions
        default : any, default=None
            Value to return on error when mode='safe'
        """
        self._target = target
        self._mode = mode
        self._default = default
    
    def __getattr__(self, name):
        """
        Safe attribute access with recursive wrapping.
        
        Flow:
            1. Try to get attribute from target
            2. If AttributeError and mode='safe' → return default
            3. If SimpleNamespace → recursive wrap
            4. If callable or has __dict__ → recursive wrap
            5. Otherwise → return as-is
        
        The key insight: We don't need to catch exceptions here.
        Just wrap everything and let __call__ handle the error at the end.
        """
        # Step 1: Try to get attribute
        try:
            attr = getattr(self._target, name)
        except AttributeError as e:
            if DEBUG:
                print(f"[SafeWrapper] AttributeError: {name} not in {type(self._target).__name__}")
            if self._mode == 'safe':
                return self._default
            else:
                raise
        
        # Step 2: SimpleNamespace → recursive wrap
        if isinstance(attr, types.SimpleNamespace):
            if DEBUG:
                print(f"[SafeWrapper] Wrapping SimpleNamespace: {name}")
            return SafeWrapper(attr, mode=self._mode, default=self._default)
        
        # Step 3: Callable or object with attributes → recursive wrap
        # This covers: functions, methods, classes, callable objects, nested objects
        if hasattr(attr, "__call__") or hasattr(attr, "__dict__"):
            if DEBUG:
                print(f"[SafeWrapper] Wrapping callable/object: {name}")
            return SafeWrapper(attr, mode=self._mode, default=self._default)
        
        # Step 4: Plain value → return as-is
        if DEBUG:
            print(f"[SafeWrapper] Returning plain value: {name}")
        return attr
    
    def __call__(self, *args, **kwargs):
        """
        Execute the final call with error handling.
        
        This is where all errors are caught - the terminal point of the chain.
        All intermediate steps just wrap, this step actually executes.
        
        Raises
        ------
        TypeError
            If wrapped target is not callable (in 'raise' mode)
        
        Returns
        -------
        any
            Result of the call, or default value if error caught in 'safe' mode
        """
        # Check if target is callable
        if not callable(self._target):
            error_msg = f"SafeWrapper target {self._target!r} is not callable"
            if self._mode == 'safe':
                if DEBUG:
                    print(f"[SafeWrapper] {error_msg} (returning default)")
                return self._default
            else:
                raise TypeError(error_msg)
        
        # Execute with error handling
        try:
            if DEBUG:
                print(f"[SafeWrapper] Calling {self._target} with args={args}, kwargs={kwargs}")
            return self._target(*args, **kwargs)
        except Exception as e:
            if DEBUG:
                print(f"[SafeWrapper] Exception caught: {type(e).__name__}: {e}")
                print(f"[SafeWrapper] Mode={self._mode}, returning default={self._default}")
            
            if self._mode == 'safe':
                return self._default
            else:
                raise
    
    def __repr__(self):
        """String representation for debugging."""
        target_type = type(self._target).__name__
        return f"<SafeWrapper target={target_type} mode={self._mode}>"

# ===============================================================================
# Public API
# ===============================================================================

def wrap_use_safe(target, mode='safe', default=None):
    """
    Wrap an object with safe error handling.
    
    This is the main entry point for creating safe wrappers.
    
    Parameters
    ----------
    target : any
        Object to wrap (typically 'use' namespace)
    mode : str, default='safe'
        'safe' returns default on error, 'raise' re-raises exceptions
    default : any, default=None
        Value to return on error when mode='safe'
    
    Returns
    -------
    SafeWrapper
        Wrapped object with safe error handling
    
    Examples
    --------
    >>> from usekit.classes.wrap.base.use_base import use
    >>> safe = wrap_use_safe(use, mode='safe', default=None)
    >>> 
    >>> # These all return None on error instead of raising
    >>> result = safe.read.json.base("missing.json")
    >>> result = safe.rjb("missing.json")
    >>> result = safe.json.rjb("missing.json")
    """
    return SafeWrapper(target, mode=mode, default=default)

# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    'SafeWrapper',
    'wrap_use_safe',
]

# -----------------------------------------------------------------------------------------------
# [EOF] helper_safe.py
# -----------------------------------------------------------------------------------------------
