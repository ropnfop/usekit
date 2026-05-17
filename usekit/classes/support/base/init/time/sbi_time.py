# Path: usekit.classes.support.base.init.time.sbi_time.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone, tzinfo
from functools import lru_cache
import time
from typing import Any, Dict, Iterator, Optional, Union

DateLike = Union[datetime, int, float]

try:
    from zoneinfo import ZoneInfo
except Exception:  # pragma: no cover
    ZoneInfo = None


def resolve_tz(tz_name: Optional[str]) -> Optional[tzinfo]:
    """Resolve a timezone name to tzinfo.

    Notes
    -----
    - None / "local" / "naive" => None (naive local time; depends on runtime, e.g., Colab may be UTC).
    - "UTC" => timezone.utc
    - IANA timezone names (e.g., "Asia/Seoul") => ZoneInfo(name) if available.
    """
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
    """Load TIME.default_tz from sys_const.yaml.

    Returns "local" if unavailable.
    """
    try:
        # Lazy import to reduce startup overhead.
        from usekit.classes.common.utils.helper_const import get_const
        return str(get_const("TIME.default_tz"))
    except Exception:
        return "local"


@lru_cache(maxsize=1)
def _sys_default_tzinfo() -> Optional[tzinfo]:
    """Resolved tzinfo for sys default timezone."""
    return resolve_tz(_sys_default_tz_name())


class TimeHandler:
    """Practical time utilities for usekit.

    Notes
    -----
    - If tz_default is None, now() returns naive local datetime (runtime-defined).
      In Colab, this is often UTC unless TZ is set via tzset().
    - If tz_default is set, now() returns timezone-aware datetime in that timezone.
    """

    def __init__(self, tz_default: Optional[tzinfo] = None):
        self.tz_default = tz_default

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def set_tz(self, tz: Optional[tzinfo]) -> "TimeHandler":
        """Set default timezone for this handler (in-place)."""
        self.tz_default = tz
        return self

    def set_tz_name(self, tz_name: Optional[str]) -> "TimeHandler":
        """Set default timezone by name (in-place)."""
        self.tz_default = resolve_tz(tz_name)
        return self

    def now(self, tz: Optional[tzinfo] = None) -> datetime:
        """Return current time.

        Parameters
        ----------
        tz:
            Overrides default timezone for this call. If None, uses tz_default.

        Returns
        -------
        datetime
            Current datetime.
        """
        if tz is None:
            tz = self.tz_default
        return datetime.now(tz=tz)

    def format(self, dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format a datetime to string."""
        if dt is None:
            dt = self.now()
        return dt.strftime(fmt)

    # Backward compatible alias.
    def str(self, dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        return self.format(dt=dt, fmt=fmt)

    def file(self, dt: Optional[datetime] = None) -> str:
        """Filename-safe timestamp: YYYY-MM-DD_HHMMSS."""
        return self.format(dt=dt, fmt="%Y-%m-%d_%H%M%S")

    def tag(self, dt: Optional[datetime] = None) -> str:
        """Compact tag timestamp: YYYYMMDD_HHMMSS."""
        return self.format(dt=dt, fmt="%Y%m%d_%H%M%S")

    def log(self, dt: Optional[datetime] = None) -> str:
        """Log prefix: [YYYY-MM-DD HH:MM:SS]."""
        return f"[{self.format(dt=dt)}]"

    def iso(self, dt: Optional[datetime] = None) -> str:
        """ISO 8601 datetime string."""
        if dt is None:
            dt = self.now()
        return dt.isoformat()

    def date(self, dt: Optional[datetime] = None) -> str:
        """Date string: YYYY-MM-DD."""
        return self.format(dt=dt, fmt="%Y-%m-%d")

    def time(self, dt: Optional[datetime] = None) -> str:
        """Time string: HH:MM:SS."""
        return self.format(dt=dt, fmt="%H:%M:%S")

    # ------------------------------------------------------------------
    # Conversions
    # ------------------------------------------------------------------

    def stamp(self, dt: Optional[datetime] = None) -> int:
        """Return unix timestamp as int."""
        if dt is None:
            return int(time.time())
        return int(dt.timestamp())

    def from_stamp(self, ts: Union[int, float], tz: Optional[tzinfo] = None) -> datetime:
        """Convert unix timestamp to datetime.

        If tz is None, uses tz_default (may return naive local if tz_default is None).
        """
        if tz is None:
            tz = self.tz_default
        return datetime.fromtimestamp(float(ts), tz=tz)

    def parse(self, s: str, fmt: str = "%Y-%m-%d %H:%M:%S", *, allow_iso_fallback: bool = True) -> datetime:
        """Parse a string into datetime (naive by default)."""
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            if allow_iso_fallback:
                return datetime.fromisoformat(s)
            raise

    # ------------------------------------------------------------------
    # Arithmetic
    # ------------------------------------------------------------------

    def add(
        self,
        dt: Optional[datetime] = None,
        *,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Return dt + delta (or now() + delta if dt is None)."""
        if dt is None:
            dt = self.now()
        return dt + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def sub(
        self,
        dt: Optional[datetime] = None,
        *,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> datetime:
        """Return dt - delta (or now() - delta if dt is None)."""
        if dt is None:
            dt = self.now()
        return dt - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def ago(self, *, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
        """Shortcut for sub(now(), ...)."""
        return self.sub(days=days, hours=hours, minutes=minutes, seconds=seconds)

    def after(self, *, days: int = 0, hours: int = 0, minutes: int = 0, seconds: int = 0) -> datetime:
        """Shortcut for add(now(), ...)."""
        return self.add(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # ------------------------------------------------------------------
    # Difference / timing
    # ------------------------------------------------------------------

    def _to_datetime(self, value: DateLike) -> datetime:
        """Normalize supported input types to datetime."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, (int, float)):
            # Use tz_default so "timestamp -> datetime" is consistent with handler timezone.
            return self.from_stamp(value, tz=self.tz_default)
        raise TypeError(f"Unsupported datetime input type: {type(value)!r}")

    def diff(
        self,
        dt1: DateLike,
        dt2: Optional[DateLike] = None,
        *,
        unit: str = "seconds",
        absolute: bool = False,
    ) -> float:
        """Compute dt2 - dt1 in a selected unit."""
        d1 = self._to_datetime(dt1)
        d2 = self._to_datetime(dt2) if dt2 is not None else self.now()

        seconds = (d2 - d1).total_seconds()
        if absolute:
            seconds = abs(seconds)

        factors = {
            "seconds": 1.0,
            "minutes": 60.0,
            "hours": 3600.0,
            "days": 86400.0,
        }
        denom = factors.get(unit, 1.0)
        return seconds / denom

    def elapsed(self, start: DateLike) -> float:
        """Return seconds elapsed since start (always positive)."""
        return self.diff(start, None, unit="seconds", absolute=True)

    def perf(self) -> float:
        """High resolution monotonic clock (seconds)."""
        return time.perf_counter()

    def tock(self, start: float, *, unit: str = "seconds") -> float:
        """Return elapsed perf time since start."""
        delta = time.perf_counter() - float(start)
        if unit == "seconds":
            return delta
        if unit == "milliseconds":
            return delta * 1000.0
        if unit == "minutes":
            return delta / 60.0
        if unit == "hours":
            return delta / 3600.0
        return delta

    @contextmanager
    def timer(self, *, unit: str = "seconds") -> Iterator[Dict[str, Any]]:
        """Context manager for timing blocks."""
        info: Dict[str, Any] = {"start": time.perf_counter(), "elapsed": None, "unit": unit}
        try:
            yield info
        finally:
            info["elapsed"] = self.tock(info["start"], unit=unit)

    # ------------------------------------------------------------------
    # Sleep helpers
    # ------------------------------------------------------------------

    def sleep(self, seconds: Union[int, float]) -> None:
        """Sleep for seconds."""
        time.sleep(float(seconds))

    def sleep_ms(self, ms: Union[int, float]) -> None:
        """Sleep for milliseconds."""
        time.sleep(float(ms) / 1000.0)


# ------------------------------------------------------------------
# Recommended singletons
# ------------------------------------------------------------------

# ut: uses sys_const.yaml TIME.default_tz (local by default; set to Asia/Seoul for Korea)
ut = TimeHandler(tz_default=_sys_default_tzinfo())

# Optional explicit handlers
ut_utc = TimeHandler(tz_default=timezone.utc)
ut_kst = TimeHandler(tz_default=resolve_tz("Asia/Seoul"))

__all__ = ["TimeHandler", "resolve_tz", "ut", "ut_utc", "ut_kst"]
