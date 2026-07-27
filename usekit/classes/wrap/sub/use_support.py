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
        from usekit.classes.support.base.init.dbms.sbi_db import ud
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


class _LazySys:
    """
    Lazy wrapper for SysHandler that delays import until first access.
    
    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like SysHandler)
    """
    
    def __init__(self):
        self._sys_lazy = lazy.value(self._create_sys)
    
    def _create_sys(self):
        """Factory that imports and returns SysHandler instance."""
        from usekit.classes.support.base.init.sys.sbi_sys import us
        return us
    
    def __getattr__(self, name):
        """Transparent access to SysHandler (loads on first access)."""
        return getattr(self._sys_lazy(), name)
    
    def __call__(self, *args, **kwargs):
        """Allow direct call forwarding to SysHandler."""
        return self._sys_lazy()(*args, **kwargs)
    
    def __repr__(self):
        if self._sys_lazy.is_computed:
            return f"<LazySys [loaded]>"
        elif self._sys_lazy.is_loading:
            return f"<LazySys [loading...]>"
        else:
            return f"<LazySys [not loaded]>"
    
    def preload(self):
        """Start loading SysHandler in background (non-blocking)."""
        self._sys_lazy.start_background_load()
        return self
    
    @property
    def is_loaded(self):
        """Check if SysHandler has been loaded."""
        return self._sys_lazy.is_computed
    
    @property
    def is_loading(self):
        """Check if SysHandler is currently loading in background."""
        return self._sys_lazy.is_loading


class _LazyKM:
    """
    Lazy wrapper for KMHandler that delays import until first access.

    Benefits:
        - Zero initialization cost (no import on module load)
        - Background loading support for faster startup
        - Transparent access (behaves like KMHandler)
    """

    def __init__(self):
        self._km_lazy = lazy.value(self._create_km)

    def _create_km(self):
        """Factory that imports and returns KMHandler instance."""
        from usekit.classes.support.base.init.km.sbi_km import uk
        return uk

    def __getattr__(self, name):
        """Transparent access to KMHandler (loads on first access)."""
        return getattr(self._km_lazy(), name)

    def __call__(self, *args, **kwargs):
        """Allow direct call forwarding to KMHandler."""
        return self._km_lazy()(*args, **kwargs)

    def __repr__(self):
        if self._km_lazy.is_computed:
            return f"<LazyKM [loaded]>"
        elif self._km_lazy.is_loading:
            return f"<LazyKM [loading...]>"
        else:
            return f"<LazyKM [not loaded]>"

    def preload(self):
        """Start loading KMHandler in background (non-blocking)."""
        self._km_lazy.start_background_load()
        return self

    @property
    def is_loaded(self):
        """Check if KMHandler has been loaded."""
        return self._km_lazy.is_computed

    @property
    def is_loading(self):
        """Check if KMHandler is currently loading in background."""
        return self._km_lazy.is_loading


class _LazyUtil:
    """Lazy wrapper for UtilHandler (uu) — usekit utilities (task generator, etc.)."""

    def __init__(self):
        self._util_lazy = lazy.value(self._create_util)

    def _create_util(self):
        from usekit.classes.support.base.init.util.sbi_util import uu
        return uu

    def __getattr__(self, name):
        return getattr(self._util_lazy(), name)

    def __call__(self, *args, **kwargs):
        return self._util_lazy()(*args, **kwargs)

    def __repr__(self):
        if self._util_lazy.is_computed:
            return f"<LazyUtil [loaded]>"
        elif self._util_lazy.is_loading:
            return f"<LazyUtil [loading...]>"
        else:
            return f"<LazyUtil [not loaded]>"

    def preload(self):
        self._util_lazy.start_background_load()
        return self

    @property
    def is_loaded(self):
        return self._util_lazy.is_computed

    @property
    def is_loading(self):
        return self._util_lazy.is_loading


class _LazyEmo:
    """Lazy wrapper for EmoHandler (ue) — emotion/knowledge pure utilities."""

    def __init__(self):
        self._emo_lazy = lazy.value(self._create_emo)

    def _create_emo(self):
        from usekit.classes.support.base.init.emo.sbi_emo import ue
        return ue

    def __getattr__(self, name):
        return getattr(self._emo_lazy(), name)

    def __call__(self, *args, **kwargs):
        return self._emo_lazy()(*args, **kwargs)

    def __repr__(self):
        if self._emo_lazy.is_computed:
            return f"<LazyEmo [loaded]>"
        elif self._emo_lazy.is_loading:
            return f"<LazyEmo [loading...]>"
        else:
            return f"<LazyEmo [not loaded]>"

    def preload(self):
        self._emo_lazy.start_background_load()
        return self

    @property
    def is_loaded(self):
        return self._emo_lazy.is_computed

    @property
    def is_loading(self):
        return self._emo_lazy.is_loading


# ----------------------------------------------------------------------------------------------- 
# Create lazy support instances
# ----------------------------------------------------------------------------------------------- 

# ut: Time utilities (now, format, stamp, diff, timer, sleep, etc.)
ut = _LazyTime()

# uw: Watch utilities (p, info, warn, err, ok, here, history, debug, etc.)
uw = _LazyWatch()

# ud: Database utilities (query, execute, insert, update, delete, etc.)
ud = _LazyDB()

# us: System utilities (env, key, keys, base, platform, exists, join, mkdir, etc.)
us = _LazySys()

# uk: KeyMemory utilities (read, write, add, remove, list, clear, info, etc.)
uk = _LazyKM()

# uu: Utility tools (task work-unit generator: new/step/list/show/done, etc.)
uu = _LazyUtil()

# ue: Emotion utilities (pure coordinate transforms: hslva, later ersdf/dhsl/meta)
ue = _LazyEmo()

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

__all__ = ['ut', 'uw', 'ud', 'us', 'uk', 'uu']

# ----------------------------------------------------------------------------------------------- 
#  [ withropnfop@gmail.com ]  
# ----------------------------------------------------------------------------------------------- 
