# Path: usekit.classes.support.base.init.watch.sbi_watch.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone, tzinfo
from functools import lru_cache
import json
from typing import Any, Optional, Union

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


def resolve_tz(tz_name: Optional[str]) -> Optional[tzinfo]:
    """Resolve timezone name to tzinfo"""
    if not tz_name:
        return None
    
    key = str(tz_name).strip()
    if not key:
        return None
    
    low = key.lower()
    if low in ("local", "naive"):
        return None
    
    if key.upper() == "UTC":
        return timezone.utc
    
    if ZoneInfo is None:
        return None
    
    try:
        return ZoneInfo(key)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _sys_default_tz_name() -> str:
    """Load TIME.default_tz from sys_const.yaml"""
    try:
        from usekit.classes.common.utils.helper_const import get_const
        return str(get_const("TIME.default_tz"))
    except Exception:
        return "local"


@lru_cache(maxsize=1)
def _sys_default_tzinfo() -> Optional[tzinfo]:
    """Resolved tzinfo for system default timezone"""
    return resolve_tz(_sys_default_tz_name())


class WatchHandler:
    """
    Monitoring, logging, and debugging utilities
    
    Features:
    - Enhanced print with history and styling
    - Structured logging (info, warn, err, ok)
    - Path debugging (here, path)
    - Print history management
    - Timezone-aware timestamps (KST support via sys_const.yaml)
    """
    
    def __init__(self, max_history: int = 50, tz_default: Optional[tzinfo] = None):
        self._history = deque(maxlen=max_history)
        self._count = 0
        self._once_set = set()
        self._debug_mode = False
        # Use system default timezone (KST if configured)
        self.tz_default = tz_default if tz_default is not None else _sys_default_tzinfo()
    
    # ========================================================================
    # Core: Enhanced Print
    # ========================================================================
    
    def p(self, *args, **kwargs):
        """
        Enhanced print with styling, timestamps, and history
        
        Args:
            *args: Values to print
            time (bool): Add timestamp [HH:MM:SS]
            stamp (bool): Add unix timestamp
            style (str): 'ok', 'warn', 'err', 'info'
            fmt (str): 'json' for JSON formatting
            once (bool): Print only once (deduplicate)
            log (bool): Also log to info
            debug (bool): Show debug metadata
        
        Examples:
            uw.p("Hello")
            uw.p("Warning", style="warn")
            uw.p(data, fmt="json")
            uw.p("Started", time=True)
            uw.p("Only once", once=True)
        """
        # Extract options
        show_time = kwargs.pop("time", False)
        show_stamp = kwargs.pop("stamp", False)
        style = kwargs.pop("style", None)
        fmt = kwargs.pop("fmt", None)
        once = kwargs.pop("once", False)
        log_flag = kwargs.pop("log", False)
        debug = kwargs.pop("debug", self._debug_mode)
        
        # Build message
        if args:
            msg = " ".join(str(a) for a in args)
        else:
            msg = f"[USEKIT - {self._now()}]"
        
        # Once mode - deduplicate
        if once:
            if msg in self._once_set:
                return
            self._once_set.add(msg)
        
        # Format
        if fmt == "json":
            try:
                # Try to parse and pretty print JSON
                parsed = json.loads(msg) if isinstance(msg, str) else msg
                msg = json.dumps(parsed, indent=2, ensure_ascii=False)
            except Exception:
                msg = f"[Invalid JSON] {msg}"
        
        # Timestamp prefix
        prefix = ""
        if show_stamp:
            prefix = f"[{self._timestamp()}] "
        elif show_time:
            prefix = f"[{self._now()}] "
        
        msg = f"{prefix}{msg}"
        
        # Update history
        self._count += 1
        self._history.append(msg)
        
        # Output with style
        if style == "ok":
            self.ok(msg)
        elif style == "warn":
            self.warn(msg)
        elif style == "err":
            self.err(msg)
        elif style == "info":
            self.info(msg)
        else:
            print(msg)
        
        # Additional logging
        if log_flag:
            self._log("INFO", f"[u.p LOG] {msg}", symbol=">", color="\033[94m")
        
        if debug:
            self._log("DEBUG", f"idx={self._count} msg={msg}", symbol="*", color="\033[95m")
    
    # ========================================================================
    # Logging: Structured output
    # ========================================================================
    
    def info(self, msg: str):
        """Log info message [INFO] in blue"""
        self._log("INFO", msg, symbol=">", color="\033[94m")
    
    def warn(self, msg: str):
        """Log warning message [WARN] in yellow"""
        self._log("WARN", msg, symbol="!", color="\033[93m")
    
    def err(self, msg: str):
        """Log error message [FAIL] in red"""
        self._log("FAIL", msg, symbol="X", color="\033[91m")
    
    def ok(self, msg: str):
        """Log success message [OK] in green"""
        self._log("OK", msg, symbol="✓", color="\033[92m")
    
    def tag(self, msg: str, tag: str = "LOG"):
        """Log with custom tag"""
        self._log(tag.upper(), msg, symbol="-", color="\033[94m")
    
    def meta(self, msg: str, **kwargs):
        """Log with metadata"""
        extra = " ".join(f"{k}={v}" for k, v in kwargs.items())
        full_msg = f"{msg} | {extra}" if kwargs else msg
        self._log("META", full_msg, symbol="*", color="\033[95m")
    
    def raw(self, msg: str):
        """Plain print with no formatting"""
        print(msg)
    
    # ========================================================================
    # Path: Debugging location
    # ========================================================================
    
    def here(self):
        """Log current working directory"""
        try:
            import os
            path = os.getcwd()
            self.tag(f"Working at: {path}", tag="HERE")
        except Exception as e:
            self.warn(f"Cannot get path: {e}")
    
    def path(self) -> str:
        """Get current working directory path"""
        try:
            import os
            return os.getcwd()
        except Exception:
            return "[unknown]"
    
    # ========================================================================
    # History: Print history management
    # ========================================================================
    
    def history(self, n: Optional[int] = None) -> list:
        """
        Get print history
        
        Args:
            n: Number of recent items (None = all)
        
        Returns:
            List of messages
        """
        hist = list(self._history)
        if n is not None:
            return hist[-n:]
        return hist
    
    def clear(self):
        """Clear print history"""
        self._history.clear()
        self._once_set.clear()
        self._count = 0
    
    def count(self) -> int:
        """Get total print count"""
        return self._count
    
    # ========================================================================
    # Config: Settings
    # ========================================================================
    
    def debug(self, value: Optional[bool] = None) -> bool:
        """
        Get or set debug mode
        
        Args:
            value: True/False to set, None to get
        
        Returns:
            Current debug mode
        """
        if value is not None:
            self._debug_mode = bool(value)
        return self._debug_mode
    
    def set_tz(self, tz: Optional[tzinfo]) -> "WatchHandler":
        """Set default timezone for this handler"""
        self.tz_default = tz
        return self
    
    def set_tz_name(self, tz_name: Optional[str]) -> "WatchHandler":
        """Set default timezone by name (e.g., 'Asia/Seoul', 'UTC')"""
        self.tz_default = resolve_tz(tz_name)
        return self
    
    # ========================================================================
    # Internal helpers
    # ========================================================================
    
    def _now(self) -> str:
        """Current time HH:MM:SS with timezone support"""
        dt = datetime.now(tz=self.tz_default)
        return dt.strftime("%H:%M:%S")
    
    def _timestamp(self) -> int:
        """Unix timestamp"""
        return int(datetime.now(tz=self.tz_default).timestamp())
    
    def _log(self, level: str, msg: str, symbol: str = "", color: str = ""):
        """Internal logging with color and symbol"""
        prefix = f"[{self._now()}] {symbol} [{level}]"
        full_msg = f"{prefix} {msg}"
        self._count += 1
        self._history.append(full_msg)
        print(f"{color}{full_msg}\033[0m")


# ========================================================================
# Singleton instance
# ========================================================================

# uw: uses sys_const.yaml TIME.default_tz (Asia/Seoul if configured)
uw = WatchHandler(tz_default=_sys_default_tzinfo())

# Optional explicit handlers for different timezones
uw_utc = WatchHandler(tz_default=timezone.utc)
uw_kst = WatchHandler(tz_default=resolve_tz("Asia/Seoul"))

__all__ = ["WatchHandler", "resolve_tz", "uw", "uw_utc", "uw_kst"]
