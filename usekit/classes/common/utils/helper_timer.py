# Path: usekit/classes/common/utils/helper_timer.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is echo —
# -----------------------------------------------------------------------------------------------

from usekit.classes.common.utils.helper_const import get_const
import time
from typing import List, Tuple, Optional


def _is_timer_debug_enabled() -> bool:
    """Check if DEBUG_OPTIONS.timer is enabled in sys_const."""
    try:
        value = get_const("DEBUG_OPTIONS.timer")
    except Exception:
        return False
    if isinstance(value, str):
        return value.lower() in ("1", "true", "yes", "on")
    return bool(value)

# ───────────────────────────────────────────────────────────────
# Disabled Mode: define no-op stubs (safe import)
# ───────────────────────────────────────────────────────────────
if not _is_timer_debug_enabled():

    def _tick(label: str, reset: bool = False) -> float:
        return 0.0

    def summary(sort_by_duration: bool = False):
        return None

    def get_last_delta():
        return None

    def get_total():
        return None

    def _clear():
        pass

# ───────────────────────────────────────────────────────────────
# Enabled Mode: full timing implementation
# ───────────────────────────────────────────────────────────────
else:
    _timeline: List[Tuple[str, float]] = []

    def _tick(label: str, reset: bool = False) -> float:
        """
        Record a timing checkpoint.
        """
        global _timeline
        if reset:
            _timeline = []

        now = time.perf_counter()
        _timeline.append((label, now))

        if len(_timeline) == 1:
            print(f"[⚙️] {label:<30} start...")
            return 0.0
        else:
            delta = now - _timeline[-2][1]
            total = now - _timeline[0][1]
            print(f"[⏱] {label:<30} | Δ{delta:>6.3f}s | total {total:>6.3f}s")
            return delta

    def summary(sort_by_duration: bool = False) -> Optional[float]:
        """
        Print a summary of all recorded timing checkpoints.
        """
        if not _timeline:
            print("⏳ No records found.")
            return None

        if len(_timeline) == 1:
            print(f"[⚙️] Only start recorded: {_timeline[0][0]}")
            return 0.0

        total = _timeline[-1][1] - _timeline[0][1]
        segments = [
            (i, _timeline[i][0], _timeline[i][1] - _timeline[i - 1][1])
            for i in range(1, len(_timeline))
        ]

        print("\n📊 Timeline summary:")

        if sort_by_duration:
            for idx, label, dur in sorted(segments, key=lambda x: x[2], reverse=True):
                pct = (dur / total * 100) if total > 0 else 0
                print(f"  {idx:02d}. {label:<25} Δ{dur:>6.3f}s ({pct:>5.1f}%)")
        else:
            cumulative = 0.0
            for idx, label, dur in segments:
                cumulative += dur
                print(f"  {idx:02d}. {label:<25} Δ{dur:>6.3f}s | cum {cumulative:>6.3f}s")

        print(f"— total: {total:.3f}s —")
        return total

    def get_last_delta() -> Optional[float]:
        """Return duration of the last section."""
        if len(_timeline) < 2:
            return None
        return _timeline[-1][1] - _timeline[-2][1]

    def get_total() -> Optional[float]:
        """Return total elapsed time."""
        if not _timeline:
            return None
        return _timeline[-1][1] - _timeline[0][1]

    def _clear():
        """Clear the recorded timeline (no output)."""
        global _timeline
        _timeline = []