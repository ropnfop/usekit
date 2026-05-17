# Path: usekit.classes.wrap.safe.use_safe.py
# ----------------------------------------------------------------------------------------------- #
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is safety & expansion —
# ----------------------------------------------------------------------------------------------- #

from usekit.classes.common.init.helper_lazy import lazy

# ----------------------------------------------------------------------------------------------- #
# Lazy Safe Wrapper with Background Loading
# ----------------------------------------------------------------------------------------------- #

class _LazySafe:
    """
    Lazy wrapper for safe mode that delays use_base import until first access.
    
    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like SafeWrapper)
        - Proper error handling delegation
    
    Performance:
        - Without preload: ~8s delay on first access
        - With preload:    ~0s delay (loaded in background)
    """
    
    def __init__(self):
        self._safe_lazy = lazy.value(self._create_safe)
    
    def _create_safe(self):
        """Factory that imports and wraps use in safe mode."""
        from usekit.classes.wrap.base.use_base import use
        from usekit.classes.common.errors.helper_safe import wrap_use_safe
        return wrap_use_safe(use, mode='safe', default=None)
    
    def __getattr__(self, name):
        """Transparent access to safe wrapper (loads on first access)."""
        # Don't catch exceptions here - let SafeWrapper handle them
        return getattr(self._safe_lazy(), name)
    
    def __call__(self, *args, **kwargs):
        """Enable direct invocation through safe wrapper."""
        return self._safe_lazy()(*args, **kwargs)
    
    def __repr__(self):
        if self._safe_lazy.is_computed:
            return f"<LazySafe [loaded]>"
        elif self._safe_lazy.is_loading:
            return f"<LazySafe [loading...]>"
        else:
            return f"<LazySafe [not loaded]>"
    
    def preload(self):
        """Start loading safe in background (non-blocking)."""
        self._safe_lazy.start_background_load()
        return self
    
    @property
    def is_loaded(self):
        """Check if safe has been loaded."""
        return self._safe_lazy.is_computed
    
    @property
    def is_loading(self):
        """Check if safe is currently loading in background."""
        return self._safe_lazy.is_loading

# Create lazy safe instance
safe = _LazySafe()

# Short alias
s = safe

# ----------------------------------------------------------------------------------------------- #
# Optional: Preload in background (uncomment to enable)
# ----------------------------------------------------------------------------------------------- #

# Immediately start loading safe in background
# This adds ~0.01s to import time but eliminates 8s delay on first use
# safe.preload()

# ----------------------------------------------------------------------------------------------- #
# Future extensions (currently commented out)
# ----------------------------------------------------------------------------------------------- #

# from usekit.classes.system.time.class_timehd import Time
# from usekit.classes.system.log.class_loghd import Log
# from usekit.classes.ai.class_aiusehd import AIUse

# stt = wrap_use_safe(SimpleNamespace(time=Time), mode='safe', default=None)   # Safe time tools
# sww = wrap_use_safe(SimpleNamespace(log=Log), mode='safe', default=None)     # Safe log tools
# sai = wrap_use_safe(AIUse, mode='safe', default=None)  # Safe AI tools

# ----------------------------------------------------------------------------------------------- #
# Public API
# ----------------------------------------------------------------------------------------------- #

__all__ = ['safe', 's']

# ----------------------------------------------------------------------------------------------- #
# [EOF] use_safe.py
# ----------------------------------------------------------------------------------------------- #
