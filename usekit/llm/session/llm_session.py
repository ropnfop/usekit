# Path: usekit.llm.session.llm_session.py
# -----------------------------------------------------------------------
#  Session state — usekit native (u.wjb/rjb)
# -----------------------------------------------------------------------

import time
from datetime import datetime

SESSION_KEY = "llm_session"


def _now_iso():
    return datetime.now().isoformat()


def save(meta: dict):
    """Save session to usekit json store."""
    try:
        from usekit import u
        u.wjb(meta, SESSION_KEY)
    except Exception:
        pass  # standalone mode, skip persist


def load() -> dict:
    """Load session from usekit json store."""
    try:
        from usekit import u
        if u.hjb(SESSION_KEY):
            return u.rjb(SESSION_KEY)
    except Exception:
        pass
    return {}


def make_session(provider: str, model: str, config: dict, ping_result: dict = None) -> dict:
    """Build session metadata dict."""
    meta = {
        "provider": provider,
        "model": model,
        "config": config,
        "connected_at": _now_iso(),
        "last_ping_time": time.time() if ping_result else None,
        "last_ping_elapsed": ping_result.get("elapsed") if ping_result else None,
        "warm_state": ping_result.get("ok", False) if ping_result else False,
    }
    return meta
