# Path: usekit.classes.support.base.init.ai.sbi_ai.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------
# AI system management handler — sibling to dbms (sbi_db.py).
#
#   us.ai vs ua:
#     ua  — pure provider layer. "어떤 모델이든 같은 방식으로 호출"
#           ua.conn / ua.send / ua.recv / ua.ask / ua.run …
#     us.ai — system management above ua.
#           CLI bridge, session/history, config file, editor serving.
#
#   Usage:
#       us.ai.providers()                       # available provider names
#       us.ai.configured()                      # providers that have stored config
#       us.ai.config("qwen")                    # read stored config
#       us.ai.config("qwen", base_url="...", api_key="...", model="...")  # write
#       us.ai.connect("qwen")                   # ua.conn() + load stored config
#       us.ai.status()                          # current connection / session info
#       us.ai.serve_chat(provider, prompt, ...) # editor entry point
#       us.ai.history()                         # recent turns (in-memory)
#       us.ai.clear()                           # clear history
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional


# Cap on in-memory history. Persistent history lives in the editor's
# OPFS slot store — this ring is just for programmatic inspection.
_HISTORY_CAP = 100


class AIManager:
    """
    AI system manager — accessed via ``us.ai``.

    Splits responsibilities cleanly:
      - this class:           management (config, status, history, dispatch)
      - sbi_ai_config:        on-disk provider config
      - sbi_ai_chat:          chat serving (ua path + CLI path)
      - usekit.llm (ua):      actual API calls
    """

    def __init__(self) -> None:
        self._history: Deque[Dict[str, Any]] = deque(maxlen=_HISTORY_CAP)

    # ── provider discovery ─────────────────────────────────────────────

    def providers(self) -> List[str]:
        """All providers known to the ua layer + 'claude' (CLI-only)."""
        names: List[str] = []
        try:
            from usekit.llm.base.init.lli_conn import list_providers
            names.extend(list_providers())
        except ImportError:
            pass
        # 'claude' lives in the CLI path, not in lli_conn — surface it explicitly.
        if "claude" not in names:
            names.append("claude")
        return sorted(set(names))

    def configured(self) -> List[str]:
        """Providers with stored config in ~/.usekit/llm_providers.json."""
        from usekit.classes.support.base.init.ai.sbi_ai_config import list_configured
        return list_configured()

    # ── config ─────────────────────────────────────────────────────────

    def config(self, provider: str, **fields) -> Dict[str, Any]:
        """
        Read or write a provider's stored config.

        Read:
            us.ai.config("qwen")                  # → {"base_url": "...", ...}

        Write (merge):
            us.ai.config("qwen", base_url="...", api_key="...", model="...")

        Clear a field:
            us.ai.config("qwen", api_key=None)
        """
        from usekit.classes.support.base.init.ai.sbi_ai_config import (
            get_provider,
            save_provider,
        )
        if not fields:
            return get_provider(provider)
        return save_provider(provider, **fields)

    def config_path(self) -> str:
        """Absolute path to ~/.usekit/llm_providers.json."""
        from usekit.classes.support.base.init.ai.sbi_ai_config import config_path
        return config_path()

    def forget(self, provider: str) -> bool:
        """Delete a provider's stored config. Returns True if it existed."""
        from usekit.classes.support.base.init.ai.sbi_ai_config import delete_provider
        return delete_provider(provider)

    # ── connection (delegates to ua) ───────────────────────────────────

    def connect(self, provider: str = "qwen", **overrides) -> Any:
        """
        Open a ua connection using stored config + ad-hoc overrides.

        Stored fields (base_url, api_key, model, ...) are auto-loaded;
        overrides win.

        Example:
            us.ai.connect("qwen")                          # use saved config
            us.ai.connect("qwen", model="Qwen3-Coder-30B") # override model
        """
        from usekit import ua
        kwargs = dict(self.config(provider))
        kwargs.update(overrides)
        return ua.conn(provider, **kwargs)

    def status(self) -> Dict[str, Any]:
        """
        Current ua connection status, or {'connected': False} if nothing open.
        """
        try:
            from usekit import ua
        except ImportError:
            return {"connected": False, "reason": "ua unavailable"}
        info = ua.info() if hasattr(ua, "info") else {}
        return info or {"connected": False}

    # ── central gateway (the narrow waist) ─────────────────────────────
    # All AI calls should flow through here: us.ai.call(provider, prompt, ...)
    # Safety (health gate, 429/fatal, call cap, state, fallback) lives in the
    # gateway module — this is just the public entry point.

    def call(self, provider: str, prompt: str, **kw) -> Dict[str, Any]:
        """
        Route one AI call through the gateway.

            us.ai.call("claude", "hi")
            us.ai.call("groq", "hi", fallback=["qwen"], max_calls=2)

        kw: model, config, timeout, max_calls, fallback, on_status
        """
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import call as _gw_call
        return _gw_call(provider, prompt, **kw)

    def call_stream(self, provider: str, prompt: str, **kw):
        """Streaming variant (yields SSE-ready dicts) through the gateway."""
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import call_stream as _gw_stream
        return _gw_stream(provider, prompt, **kw)

    def health(self, provider: str) -> Dict[str, Any]:
        """Cheap, non-network health check for a provider (reads stored state)."""
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import health as _gw_health
        return _gw_health(provider)

    def probe(self, provider: str, *, timeout: int = 5) -> Dict[str, Any]:
        """
        Active liveness check for a single provider (no tokens spent).

            us.ai.probe("groq")
            us.ai.probe("openai", timeout=10)

        Returns a result dict (state/ok/elapsed/...). Network call, unlike health().
        """
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import probe as _gw_probe
        return _gw_probe(provider, timeout=timeout)

    def probe_all(self, *, only_free: bool = True, timeout: int = 5) -> Dict[str, Dict[str, Any]]:
        """
        Probe every enabled provider → {name: result}.

            us.ai.probe_all()                 # free/local providers only
            us.ai.probe_all(only_free=False)   # include key-gated providers

        only_free=True reports key-gated providers as skipped (no key needed).
        """
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import probe_all as _gw_probe_all
        return _gw_probe_all(only_free=only_free, timeout=timeout)

    def in_flight(self) -> List[str]:
        """Providers currently processing a request (re-entrancy inspection)."""
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import in_flight as _gw_inflight
        return _gw_inflight()

    def worker_concurrency(self, n: Optional[int] = None) -> int:
        """
        Get or set the max number of concurrent INTERNAL parallel workers.

            us.ai.worker_concurrency()      # read current cap
            us.ai.worker_concurrency(4)      # set cap (Termux-safe default)

        This bounds parallelism inside one task (the "burners" rule); it does
        not affect the external re-entry lock that blocks RUN-mashing.
        """
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import (
            set_worker_concurrency, worker_concurrency,
        )
        if n is None:
            return worker_concurrency()
        return set_worker_concurrency(n)

    # ── long-running jobs (deep work, decoupled from HTTP) ────────────
    # For tasks longer than a few seconds (deep analysis, multi-file
    # refactor, codebase exploration), the HTTP request cannot reliably
    # stay open. Jobs run in a background thread of the editor server,
    # persist every stream-json event to disk, and let clients (re-)attach
    # via SSE at any time — full history is replayed on reconnect.

    def job_start(self, prompt: str, *, provider: str = "claude",
                  model: Optional[str] = None,
                  session: Optional[str] = None) -> Dict[str, Any]:
        """Start a background AI job. Returns immediately with job_id."""
        from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
        return _jb.start(prompt, provider=provider, model=model, session=session)

    def job_status(self, job_id: str) -> Dict[str, Any]:
        """Cheap status snapshot of a job."""
        from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
        return _jb.status(job_id)

    def job_list(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Recent jobs, most recent first."""
        from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
        return _jb.list_jobs(limit=limit)

    def job_stream(self, job_id: str, *, from_start: bool = True):
        """Iterator of events for SSE. Replays history then follows live."""
        from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
        return _jb.stream_events(job_id, from_start=from_start)

    def job_cancel(self, job_id: str) -> Dict[str, Any]:
        """Best-effort cancel of a running job."""
        from usekit.classes.support.base.init.ai import sbi_ai_job as _jb
        return _jb.cancel(job_id)

    # ── editor chat serving ────────────────────────────────────────────

    def serve_chat(
        self,
        provider: str,
        prompt: str,
        *,
        model: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """
        One chat turn — dispatch to ua (API) or subprocess (CLI),
        record into in-memory history, return the result dict.

        Called by the editor's ``/api/ai_chat`` endpoint.
        """
        from usekit.classes.support.base.init.ai.sbi_ai_chat import serve_chat
        t0 = time.time()
        result = serve_chat(
            provider, prompt,
            model=model, config=config, timeout=timeout,
        )
        # Record: user prompt + ai response as a single turn.
        self._history.append({
            "time": t0,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "prompt": prompt,
            "ok": result.get("ok"),
            "text": result.get("text", ""),
            "error": result.get("error"),
            "elapsed": result.get("elapsed", 0),
        })
        return result

    # ── history ────────────────────────────────────────────────────────

    def history(self, n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Return the last `n` chat turns (oldest first).
        Without `n`, returns all in-memory turns.
        """
        items = list(self._history)
        if n is not None and n > 0:
            items = items[-n:]
        return items

    def clear(self) -> int:
        """Empty in-memory history. Returns number of turns cleared."""
        n = len(self._history)
        self._history.clear()
        return n

    # ── repr ───────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        n = len(self._history)
        return f"<AIManager turns={n}>"


# ── Singleton instance ─────────────────────────────────────────────────
# Note: us.ai accesses a fresh AIManager via the SysHandler property;
# this module-level singleton is here for direct import (``from
# usekit.classes.support.base.init.ai.sbi_ai import ai``) and tests.

ai = AIManager()

__all__ = ["AIManager", "ai"]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
