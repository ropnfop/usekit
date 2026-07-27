# Path: usekit.llm.base.load.lll_warm.py
# -----------------------------------------------------------------------
#  Session warmup / ping
# -----------------------------------------------------------------------

WARM_TTL_SEC = 300


def classify_state(elapsed: float) -> str:
    """Classify model state by ping latency."""
    if elapsed <= 1.5:
        return "full_warm"
    if elapsed <= 5:
        return "semi_warm"
    if elapsed <= 15:
        return "loading"
    if elapsed <= 40:
        return "cold_load"
    return "busy_or_unstable"


def is_warm(session: dict, ttl: float = WARM_TTL_SEC) -> bool:
    """Check if session is still warm."""
    import time
    last = session.get("last_ping_time")
    if not last:
        return False
    return (time.time() - last) <= ttl
