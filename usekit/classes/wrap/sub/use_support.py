# Path: usekit.classes.wrap.sub.use_support.py
# ----------------------------------------------------------------------------------------------- 
#  a creation by: THE Little Prince, in harmony with ROP and FOP
#  — memory is support & utilities —
# ----------------------------------------------------------------------------------------------- 

from usekit.classes.common.init.helper_lazy import lazy

# ----------------------------------------------------------------------------------------------- 
# Lazy Support Wrappers with Background Loading
# ----------------------------------------------------------------------------------------------- 

class _LazyTime:
    """
    Lazy wrapper for TimeHandler that delays import until first access.
    
    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like TimeHandler)
    
    Performance:
        - Without preload: ~0.1s delay on first access
        - With preload:    ~0s delay (loaded in background)
    """
    
    def __init__(self):
        self._time_lazy = lazy.value(self._create_time)
    
    def _create_time(self):
        """Factory that imports and returns TimeHandler instance."""
        from usekit.classes.support.base.init.time.sbi_time import ut
        return ut
    
    def __getattr__(self, name):
        """Transparent access to TimeHandler (loads on first access)."""
        return getattr(self._time_lazy(), name)
    
    def __call__(self, *args, **kwargs):
        """Allow direct call forwarding to TimeHandler."""
        return self._time_lazy()(*args, **kwargs)
    
    def __repr__(self):
        if self._time_lazy.is_computed:
            return f"<LazyTime [loaded]>"
        elif self._time_lazy.is_loading:
            return f"<LazyTime [loading...]>"
        else:
            return f"<LazyTime [not loaded]>"
    
    def preload(self):
        """Start loading TimeHandler in background (non-blocking)."""
        self._time_lazy.start_background_load()
        return self
    
    @property
    def is_loaded(self):
        """Check if TimeHandler has been loaded."""
        return self._time_lazy.is_computed
    
    @property
    def is_loading(self):
        """Check if TimeHandler is currently loading in background."""
        return self._time_lazy.is_loading


class _LazyWatch:
    """
    Lazy wrapper for WatchHandler that delays import until first access.
    
    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like WatchHandler)
    
    Performance:
        - Without preload: ~0.1s delay on first access
        - With preload:    ~0s delay (loaded in background)
    """
    
    def __init__(self):
        self._watch_lazy = lazy.value(self._create_watch)
    
    def _create_watch(self):
        """Factory that imports and returns WatchHandler instance."""
        from usekit.classes.support.base.init.watch.sbi_watch import uw
        return uw
    
    def __getattr__(self, name):
        """Transparent access to WatchHandler (loads on first access)."""
        return getattr(self._watch_lazy(), name)
    
    def __call__(self, *args, **kwargs):
        """Allow direct call forwarding to WatchHandler."""
        return self._watch_lazy()(*args, **kwargs)
    
    def __repr__(self):
        if self._watch_lazy.is_computed:
            return f"<LazyWatch [loaded]>"
        elif self._watch_lazy.is_loading:
            return f"<LazyWatch [loading...]>"
        else:
            return f"<LazyWatch [not loaded]>"
    
    def preload(self):
        """Start loading WatchHandler in background (non-blocking)."""
        self._watch_lazy.start_background_load()
        return self
    
    @property
    def is_loaded(self):
        """Check if WatchHandler has been loaded."""
        return self._watch_lazy.is_computed
    
    @property
    def is_loading(self):
        """Check if WatchHandler is currently loading in background."""
        return self._watch_lazy.is_loading


class _LazyDB:
    """
    Lazy wrapper for DBHandler that delays import until first access.
    
    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like DBHandler)
    
    Performance:
        - Without preload: ~0.1s delay on first access
        - With preload:    ~0s delay (loaded in background)
    """
    
    def __init__(self):
        self._db_lazy = lazy.value(self._create_db)
    
    def _create_db(self):
        """Factory that imports and returns DBHandler instance."""
        from usekit.classes.support.base.init.db.sbi_db import ud
        return ud
    
    def __getattr__(self, name):
        """Transparent access to DBHandler (loads on first access)."""
        return getattr(self._db_lazy(), name)
    
    def __call__(self, *args, **kwargs):
        """Allow direct call forwarding to DBHandler."""
        return self._db_lazy()(*args, **kwargs)
    
    def __repr__(self):
        if self._db_lazy.is_computed:
            return f"<LazyDB [loaded]>"
        elif self._db_lazy.is_loading:
            return f"<LazyDB [loading...]>"
        else:
            return f"<LazyDB [not loaded]>"
    
    def preload(self):
        """Start loading DBHandler in background (non-blocking)."""
        self._db_lazy.start_background_load()
        return self
    
    @property
    def is_loaded(self):
        """Check if DBHandler has been loaded."""
        return self._db_lazy.is_computed
    
    @property
    def is_loading(self):
        """Check if DBHandler is currently loading in background."""
        return self._db_lazy.is_loading


# ----------------------------------------------------------------------------------------------- 
# Create lazy support instances
# ----------------------------------------------------------------------------------------------- 

# ut: Time utilities (now, format, stamp, diff, timer, sleep, etc.)
ut = _LazyTime()

# uw: Watch utilities (p, info, warn, err, ok, here, history, debug, etc.)
uw = _LazyWatch()

# ud: Database utilities (query, execute, insert, update, delete, etc.)
ud = _LazyDB()

# ----------------------------------------------------------------------------------------------- 
# Optional: Preload in background (uncomment to enable)
# ----------------------------------------------------------------------------------------------- 

# Immediately start loading support modules in background
# This adds ~0.01s to import time but eliminates delay on first use
# ut.preload()
# uw.preload()
# ud.preload()

# Or preload all in parallel
# from usekit.classes.common.init.helper_lazy import lazy
# lazy.preload(ut._time_lazy, uw._watch_lazy, ud._db_lazy, max_workers=3)

# ----------------------------------------------------------------------------------------------- 
# Public API
# ----------------------------------------------------------------------------------------------- 

__all__ = ['ut', 'uw', 'ud']

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ]  
# ----------------------------------------------------------------------------------------------- 
