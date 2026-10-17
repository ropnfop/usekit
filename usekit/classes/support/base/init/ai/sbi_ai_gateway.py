# Path: usekit.classes.support.base.init.ai.sbi_ai_gateway
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------
# AI Gateway — the central control point ("the narrow waist of the hourglass").
#
#   Philosophy:  wide in  ·  narrow center  ·  wide out
#     - wide in   : serve_chat / serve_chat_v2 / stream_cli / workers — any entrance
#     - narrow    : EVERY call passes through gateway.call() exactly once
#     - wide out  : adapters (ua / cli / local) — one per provider family
#
#   All safety lives HERE and only here:
#     PRE   — health() : if a provider is rate-limited (future retry_after), do NOT call.
#     CALL  — cap      : never exceed max_calls outbound requests for one request.
#     POST  — classify : 429/5xx → fatal (+retry_after). never retry/recirculate.
#             record   — persist state to ~/.usekit/llm_providers.json (_state).
#     FALLBACK         — try next provider in chain; if none, stop (no infinite loop).
#
#   Invariant: a dead/429 provider costs at most ONE probe (and usually ZERO,
#   because PRE health blocks it). This is what prevents runaway cost.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional


# ── result shape ────────────────────────────────────────────────────
# Every adapter and gateway.call() returns this dict shape:
#   {ok, text, provider, model, status_code, fatal, retry_after,
#    elapsed, calls_used, error}

def _result(
    *,
    ok: bool,
    text: str = "",
    provider: str = "",
    model: str = "",
    status_code: Optional[int] = None,
    fatal: bool = False,
    retry_after: Optional[float] = None,
    elapsed: float = 0.0,
    calls_used: int = 0,
    error: Optional[str] = None,
    busy: bool = False,
    raw: Any = None,
    usage: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "text": text,
        "provider": provider,
        "model": model,
        "status_code": status_code,
        "fatal": fatal,
        "retry_after": retry_after,
        "elapsed": round(elapsed, 3),
        "calls_used": calls_used,
        "error": error,
        "busy": busy,
        "raw": raw,
        "usage": usage or {},
    }


# ── provider type resolution (which exit?) ──────────────────────────

def _provider_type(provider: str) -> str:
    """Return 'cli' or 'ua' (HTTP/OpenAI-compatible). Defaults to 'ua'."""
    prov = (provider or "").lower().strip()
    # legacy alias
    if prov == "claude":
        return "cli"
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import is_cli
        if is_cli(prov):
            return "cli"
    except ImportError:
        if prov in ("claude", "claude_code", "codex"):
            return "cli"
    return "ua"


# ── health (PRE) ────────────────────────────────────────────────────

def health(provider: str) -> Dict[str, Any]:
    """
    Cheap, non-network health check based on persisted state.

    A provider is unhealthy when its recorded retry_after_ts is still in the
    future (rate-limited / blocked). We do NOT ping the network here — that
    would itself cost a call. Network truth is learned lazily from real calls.

    Returns: {"healthy": bool, "reason": str, "retry_after_ts": float|None}
    """
    prov = (provider or "").lower().strip()
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_config import get_state
        st = get_state(prov)
    except Exception:
        st = {}

    now = time.time()
    ra_ts = st.get("retry_after_ts")
    ps = st.get("probe_state")        # last probe liveness, if any
    if ra_ts and ra_ts > now:
        wait = int(ra_ts - now)
        return {
            "healthy": False,
            "reason": f"rate-limited; retry in ~{wait}s",
            "retry_after_ts": ra_ts,
            "probe_state": ps or "quota",
        }
    return {"healthy": True, "reason": "ok", "retry_after_ts": None, "probe_state": ps}


# ── probe (ACTIVE liveness check) ───────────────────────────────────
# Unlike health() (which is free and reads persisted state only), probe()
# actually hits the network with a cheap, token-free request to learn
# whether a provider is reachable RIGHT NOW. Intended for free / no-key
# providers (groq, ollama) — we skip key-gated ones so a probe never
# burns a paid quota or trips a real billing call.

def probe(provider: str, *, timeout: int = 5) -> Dict[str, Any]:
    """
    Active liveness check for a single provider.

    Strategy (no tokens spent):
      - OpenAI-compatible base_url ending in /v1 → GET {base_url}/models
      - other ua base_url                        → GET base_url root
      - CLI providers                            → check binary on PATH

    Records the outcome via _record_state so a later free health() reflects
    reality. Key-gated providers (key_env set) are skipped by default.

    Returns the standard result dict (see _result), plus "skipped": bool.
    """
    prov = (provider or "").lower().strip()
    t0 = time.time()

    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import providers as _meta
    except Exception as e:
        r = _result(ok=False, provider=prov, error=f"meta unavailable: {e}")
        r["state"] = "dead"
        return r

    pdata = _meta().get(prov) or {}
    if not pdata:
        r = _result(ok=False, provider=prov, error="unknown provider")
        r["state"] = "dead"
        return r

    # ── Auth model drives probe strategy (auth is the source of truth) ──
    # Explicit `auth` in yaml; fall back to legacy inference for old configs:
    #   key_env present       → api_key
    #   tier == cli           → cli
    #   otherwise             → none
    auth = pdata.get("auth")
    if not auth:
        if pdata.get("key_env"):
            auth = "api_key"
        elif pdata.get("tier") == "cli":
            auth = "cli"
        else:
            auth = "none"

    # api_key: never probe — pinging without a key is pointless and may bill.
    if auth == "api_key":
        r = _result(ok=False, provider=prov, error="skipped (requires API key)")
        r["skipped"] = True
        r["state"] = "gated"          # reachable status unknown; key-gated
        return r

    # cli: liveness = external binary present on PATH (auth handled by the CLI).
    if auth == "cli":
        import shutil
        bin_name = pdata.get("cli_check") or prov
        found = shutil.which(bin_name) is not None
        res = _result(
            ok=found, provider=prov,
            status_code=200 if found else None,
            error=None if found else f"cli '{bin_name}' not on PATH",
            elapsed=time.time() - t0,
        )
        res["skipped"] = False
        res["state"] = "alive" if found else "dead"
        _record_state(prov, res)
        return res

    # none (free / no-auth, incl. proxied endpoints like g4f): cheap GET.
    base_url = (pdata.get("base_url") or "").rstrip("/")
    if not base_url:
        r = _result(ok=False, provider=prov, error="no base_url to probe")
        r["skipped"] = False
        r["state"] = "dead"
        return r

    # /v1 endpoints expose a model list — the canonical free liveness check.
    url = f"{base_url}/models" if base_url.endswith("/v1") else base_url

    try:
        import urllib.request
        import urllib.error
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
        # No-auth endpoint answered → server is alive.
        res = _result(
            ok=True, provider=prov, status_code=code,
            elapsed=time.time() - t0,
        )
        res["state"] = "alive"
    except urllib.error.HTTPError as e:
        # The host RESPONDED, so it is alive. For a no-auth provider a 4xx
        # (e.g. g4f proxy 403/405 on a bare GET) does NOT mean blocked — the
        # chat POST still works. Only 429 is a real rate-limit.
        code = e.code
        if code == 429:
            res = _result(
                ok=False, provider=prov, status_code=code, fatal=True,
                retry_after=_retry_after_from(e),
                error="rate-limited (429)", elapsed=time.time() - t0,
            )
            res["state"] = "quota"
        else:
            res = _result(
                ok=True, provider=prov, status_code=code,
                elapsed=time.time() - t0,
            )
            res["state"] = "alive"     # reachable; no-auth GET quirk, not a block
    except Exception as e:
        res = _result(
            ok=False, provider=prov,
            error=f"unreachable: {e}", elapsed=time.time() - t0,
        )
        res["state"] = "dead"          # connection refused / timeout / DNS

    res["skipped"] = False
    _record_state(prov, res)
    return res


def _retry_after_from(http_err) -> Optional[float]:
    """Parse a Retry-After header (seconds) from an HTTPError, if present."""
    try:
        val = http_err.headers.get("Retry-After")
        return float(val) if val else None
    except Exception:
        return None


def probe_all(*, only_free: bool = True, timeout: int = 5) -> Dict[str, Dict[str, Any]]:
    """
    Probe every enabled provider and return {name: result}.

    only_free=True  → probe only providers without a key_env (free / local).
                      Key-gated providers are reported as skipped.
    Runs probes concurrently, bounded by the worker semaphore.
    """
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            providers as _meta, enabled_providers,
        )
    except Exception:
        return {}

    names = enabled_providers()
    if only_free:
        meta = _meta()
        names = [n for n in names if not (meta.get(n) or {}).get("key_env")]

    results: Dict[str, Dict[str, Any]] = {}
    threads = []

    def _run(name: str):
        with _worker_sema:
            results[name] = probe(name, timeout=timeout)

    for n in names:
        th = _threading.Thread(target=_run, args=(n,), daemon=True)
        th.start()
        threads.append(th)
    for th in threads:
        th.join(timeout=timeout + 2)

    return results


def _record_state(provider: str, res: Dict[str, Any]) -> None:
    """Persist outcome of a call to provider state (best-effort)."""
    prov = (provider or "").lower().strip()
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_config import set_state, get_state
    except Exception:
        return

    now = time.time()
    prev = {}
    try:
        prev = get_state(prov) or {}
    except Exception:
        prev = {}

    ok = bool(res.get("ok"))
    state: Dict[str, Any] = {
        "healthy": ok,
        "last_status": res.get("status_code"),
        "last_error": res.get("error"),
        "checked_at": now,
        "consecutive_fails": 0 if ok else int(prev.get("consecutive_fails", 0)) + 1,
    }
    # Persist liveness state when the caller computed one (probe only).
    # call()/dispatch_one() omit it → None → field left untouched (no regression).
    _ps = res.get("state")
    if _ps:
        state["probe_state"] = _ps
    # Compute absolute retry_after timestamp if provider gave a window.
    ra = res.get("retry_after")
    if ra:
        try:
            state["retry_after_ts"] = now + float(ra)
        except (TypeError, ValueError):
            pass
    elif ok:
        state["retry_after_ts"] = None  # clear any old block on success

    try:
        set_state(prov, **state)
    except Exception:
        pass


# ── adapters (the wide exit) ────────────────────────────────────────
# Each adapter: same signature, same return shape. Gateway stays type-agnostic.

def _build_ua_conn(provider: str, model: Optional[str],
                   config: Dict[str, Any]) -> Dict[str, Any]:
    """Layered ua connection kwargs (shared by _adapter_ua and the streaming
    path): yaml defaults → env key → stored → per-call overrides → resolved
    model. on_delta is a chat-time arg, never a connection arg — stripped here.
    """
    conn: Dict[str, Any] = {}
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_config import get_provider
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            providers as _meta_providers, resolve_model, default_model,
        )
    except ImportError:
        get_provider = None
        _meta_providers = lambda: {}
        resolve_model = lambda m, provider=None: m
        default_model = lambda p: None
    ymeta = _meta_providers().get(provider) or {}
    if ymeta.get("base_url"):
        conn["base_url"] = ymeta["base_url"]
    key_env = ymeta.get("key_env")
    if key_env:
        env_key = os.environ.get(key_env)
        if env_key:
            conn["api_key"] = env_key
    if get_provider:
        try:
            stored = get_provider(provider)
            if stored:
                conn.update(stored)
        except Exception:
            pass
    if config:
        conn.update(config)
    chosen = model or conn.get("model") or default_model(provider)
    if chosen:
        conn["model"] = resolve_model(chosen, provider=provider)
    conn.pop("on_delta", None)   # chat-time arg, not a connection arg
    return conn


def _adapter_ua(
    provider: str, prompt: str, *,
    model: Optional[str], config: Dict[str, Any], timeout: int,
) -> Dict[str, Any]:
    """Exit → ua (OpenAI-compatible: qwen, groq, gemini, openai, ...)."""
    t0 = time.time()
    try:
        from usekit import ua
    except ImportError as e:
        return _result(ok=False, provider=provider, fatal=False,
                       error=f"ua unavailable: {e}", elapsed=time.time() - t0)

    conn = _build_ua_conn(provider, model, config)
    # 261017: the call's `timeout` used to stop here — the adapter never saw it.
    # Set EVERY call (ua's config is sticky across conn()), caller override wins.
    conn["http_timeout"] = (config or {}).get("http_timeout") or timeout

    try:
        ua.conn(provider, **conn)
        result = ua.run(prompt)  # single call — no parallel, no recursion
    except Exception as e:
        return _result(ok=False, provider=provider, model=conn.get("model", ""),
                       fatal=False, error=f"ua call failed: {e}",
                       elapsed=time.time() - t0)
    return _shape_ua_result(provider, conn, result, t0)


def _shape_ua_result(provider: str, conn: Dict[str, Any], result, t0: float) -> Dict[str, Any]:
    """ua.run()-shaped dict -> gateway-standard result (shared by the shared-ua
    adapter and the isolated adapter, so callers cannot tell them apart)."""
    rd = result if isinstance(result, dict) else {}
    text = rd.get("text", "") if rd else str(result)
    ok = bool(text)
    # REAL TRANSPORT SIGNALS (260917 어린왕자): the parser now carries the HTTP
    # status (REST) or the code read from the SDK exception, plus retry_after
    # from a 429 body. Before this every ua exit reported 200/None and the
    # caller had to GUESS a quota hit from elapsed time (pj01 fop.py QUOTA
    # BENCH heuristic). `raw` is kept slim — status/error/finish only, never
    # the response body.
    inner_raw = rd.get("raw") if isinstance(rd.get("raw"), dict) else {}
    sc = rd.get("status_code")
    if sc is None:
        sc = inner_raw.get("_status_code")
    if sc is None and ok:
        sc = 200
    err = None if ok else (rd.get("error") or inner_raw.get("_error") or "empty response")
    fatal = bool(sc) and (sc == 429 or 500 <= int(sc) < 600)
    return _result(
        ok=ok, text=text, provider=provider, model=conn.get("model", ""),
        status_code=sc, fatal=fatal, retry_after=rd.get("retry_after"),
        error=err, elapsed=time.time() - t0,
        usage=rd.get("usage") if rd else None,
        raw=({"status_code": sc, "error": err, "finish": rd.get("finish"),
              # 260919: how many images the provider ACTUALLY attached (None
              # when the provider does not report it). A photo-reading call
              # that went out with 0 images is a fabricated reading, and the
              # caller must be able to see that without the request body.
              "n_images": inner_raw.get("_n_images"),
              "n_images_asked": inner_raw.get("_n_images_asked")} if rd else None),
    )


def _adapter_cli(
    provider: str, prompt: str, *,
    model: Optional[str], config: Dict[str, Any], timeout: int,
) -> Dict[str, Any]:
    """Exit → CLI subprocess (claude_code, codex, ...)."""
    t0 = time.time()
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_chat import serve_via_cli
    except ImportError:
        # fall back to the private name if not exported
        try:
            from usekit.classes.support.base.init.ai.sbi_ai_chat import _serve_via_cli as serve_via_cli  # type: ignore
        except ImportError as e:
            return _result(ok=False, provider=provider, fatal=False,
                           error=f"cli adapter unavailable: {e}", elapsed=time.time() - t0)
    try:
        r = serve_via_cli(provider=provider, prompt=prompt, model=model,
                          config=config, timeout=timeout)
    except Exception as e:
        return _result(ok=False, provider=provider, fatal=False,
                       error=f"cli call failed: {e}", elapsed=time.time() - t0)

    ok = bool(r.get("ok")) if isinstance(r, dict) else False
    return _result(
        ok=ok, text=(r.get("text", "") if isinstance(r, dict) else str(r)),
        provider=provider, model=(r.get("model", "") if isinstance(r, dict) else ""),
        status_code=200 if ok else None, fatal=False,
        error=(None if ok else (r.get("error") if isinstance(r, dict) else "cli error")),
        elapsed=time.time() - t0,
    )


# ── isolated adapter (261017, pj01 multi-user) ──────────────────────
# _adapter_ua drives the process-wide `ua` singleton: conn() writes the model,
# api_key, images... into shared state and run() reads them back. Two threads
# doing that at once could send A's prompt with B's key — so call() serializes
# EVERY gemini call server-wide (the in-flight lock), and with per-student BYOK
# keys that is pure loss: student B waits on (or is refused by) student A's
# call although their keys and quotas are unrelated.
# This adapter builds a FRESH provider object per call, connects it with this
# call's own config, sends, parses, closes. Nothing is shared, so no lock is
# needed; concurrency is bounded by _isolated_sema instead. Result shape is
# identical to _adapter_ua (same _shape_ua_result).
def _adapter_isolated(
    provider: str, prompt: str, *,
    model: Optional[str], config: Dict[str, Any], timeout: int,
) -> Dict[str, Any]:
    t0 = time.time()
    try:
        from usekit.llm.base.init.lli_conn import resolve_provider, get_default_url
        from usekit.llm.base.init.lli_config import LLMConfig
        from usekit.llm.base.post.llp_recv import recv as _recv
    except ImportError as e:
        return _result(ok=False, provider=provider, fatal=False,
                       error=f"isolated adapter unavailable: {e}",
                       elapsed=time.time() - t0)

    conn = _build_ua_conn(provider, model, config)
    conn["http_timeout"] = (config or {}).get("http_timeout") or timeout
    cfg = LLMConfig().merge(conn)          # generation defaults + this call
    if not cfg.get("base_url"):
        _u = get_default_url(provider)
        if _u:
            cfg["base_url"] = _u
    cfg.setdefault("images", [])
    cfg.setdefault("search", False)

    adapter = None
    try:
        adapter = resolve_provider(provider)   # new instance every call
        adapter.connect(cfg)
        raw = adapter.send(prompt, cfg)
        result = _recv(raw, provider=provider)
    except Exception as e:
        return _result(ok=False, provider=provider, model=cfg.get("model", ""),
                       fatal=False, status_code=_status_from(e),
                       error=f"isolated call failed: {e}", elapsed=time.time() - t0)
    finally:
        try:
            if adapter is not None:
                adapter.close()
        except Exception:
            pass
    return _shape_ua_result(provider, cfg, result, t0)


_ADAPTERS = {"ua": _adapter_ua, "cli": _adapter_cli}

# Opt-in, process-wide: a SERVER (pj01 api) turns this on at start-up; the
# interactive tools (editor / shell) keep the shared-ua path untouched.
# Env USEKIT_AI_ISOLATED=1 does the same without code.
_ISOLATED = os.environ.get("USEKIT_AI_ISOLATED", "").strip() in ("1", "true", "yes")
_ISOLATED_MAX = 8
_isolated_sema = None


def set_isolated_calls(on: bool = True, max_concurrent: int = 8) -> bool:
    """Route ua-type providers through _adapter_isolated (no shared state, no
    per-provider lock; at most `max_concurrent` calls in flight). Returns on."""
    global _ISOLATED, _ISOLATED_MAX, _isolated_sema
    _ISOLATED = bool(on)
    _ISOLATED_MAX = max(1, int(max_concurrent))
    _isolated_sema = None
    return _ISOLATED


def _iso_sema():
    global _isolated_sema
    if _isolated_sema is None:
        import threading as _th
        _isolated_sema = _th.BoundedSemaphore(_ISOLATED_MAX)
    return _isolated_sema


# ── in-flight guard (re-entrancy) ───────────────────────────────────
# Prevents hitting the SAME provider again while a call is still running.
# Not a queue: if busy, we inform the caller (busy=True) instead of
# launching a duplicate request. This stops RUN-mashing / double-submit
# from multiplying backend load.
import threading as _threading

_inflight_lock = _threading.Lock()      # guards the dict below
# provider -> [owner_thread_ident, depth].
# RE-ENTRANT per thread: the gateway call() acquires a provider, then the
# adapter's own guard (ua.send -> guarded_direct_call) re-acquires the SAME
# provider on the SAME thread. A plain set rejected that nesting, so every
# ua-type provider (groq_api, qwen, gemini, ...) silently returned an empty
# response via us.ai.call(). We allow same-thread re-entry while still blocking
# a DIFFERENT thread from issuing a concurrent duplicate call to that provider.
_inflight: dict = {}                    # providers currently being called


def _acquire(provider: str) -> bool:
    """Mark provider in-flight. True if newly acquired OR re-entered by the same
    thread. False only when a DIFFERENT thread already holds it."""
    me = _threading.get_ident()
    with _inflight_lock:
        cur = _inflight.get(provider)
        if cur is None:
            _inflight[provider] = [me, 1]
            return True
        if cur[0] == me:                # same thread → nested call, allow
            cur[1] += 1
            return True
        return False                    # another thread mid-call → busy


def _release(provider: str) -> None:
    me = _threading.get_ident()
    with _inflight_lock:
        cur = _inflight.get(provider)
        if not cur:
            return
        if cur[0] == me:
            cur[1] -= 1
            if cur[1] <= 0:
                _inflight.pop(provider, None)
        else:
            _inflight.pop(provider, None)   # non-owner release: clear defensively


# ── guarded direct call (fast/single safety net) ────────────────────
# For paths that call the adapter DIRECTLY (ua_handler _send/_send_messages,
# i.e. fast/single chat) instead of going through call()/dispatch_one.
#
# Why a callback (fn) instead of routing into dispatch_one:
#   the gateway's own _adapter_ua() does `from usekit import ua; ua.conn(); ua.run()`.
#   If ua.run/send were routed back into dispatch_one, that adapter would call ua
#   again → infinite recursion. So instead the caller passes the adapter call as a
#   thunk; we only wrap it with PRE health + in-flight guard + POST state record.
#
# fn() returns whatever the adapter returns (often a provider-raw dict, NOT a
# standard gateway result). We normalize for _record_state via _normalize_direct.
def guarded_direct_call(provider: str, fn, *, timeout: int = 120) -> Dict[str, Any]:
    """Apply health gate + in-flight lock + state recording around a direct
    adapter call fn(). Returns the gateway-standard dict (with 'raw' carrying
    fn()'s original return on success).

    On unhealthy/busy: returns ok=False without ever calling fn (cost saved).
    """
    prov = (provider or "").lower().strip()

    # PRE — health gate (zero network). Blocks rate-limited providers.
    h = health(prov)
    if not h["healthy"]:
        return _result(ok=False, provider=prov, fatal=True,
                       retry_after=h.get("retry_after_ts"),
                       error=f"unhealthy: {h['reason']}")

    # IN-FLIGHT — block duplicate concurrent calls to the same provider.
    if not _acquire(prov):
        return _result(ok=False, provider=prov, busy=True,
                       error=f"{prov} is already processing a request")

    try:
        raw = fn()
        res = _normalize_direct(prov, raw)
    except Exception as e:  # adapter raised — record as fatal-ish, surface status
        res = _result(ok=False, provider=prov, fatal=True,
                      status_code=_status_from(e),
                      retry_after=_retry_after_from(e),
                      error=str(e))
    finally:
        _release(prov)  # always release, even on exception

    # POST — record state (success clears blocks; 429/5xx records retry_after).
    _record_state(prov, res)
    return res


def _normalize_direct(provider: str, raw) -> Dict[str, Any]:
    """Coerce a direct adapter return into a gateway-standard result dict.

    IMPORTANT: provider-raw shapes differ (OpenAI puts text under
    choices[0].message.content, etc). Parsing that is recv()/parser's job, NOT
    the guard's. So if the adapter returned ANYTHING without raising, we treat
    it as ok and pass the original raw through untouched (res["raw"]); the
    caller (ua.recv) extracts text. We only flag failure on a standard error
    dict (ok=False) or a None/empty return.
    """
    if isinstance(raw, dict) and raw.get("ok") is False:
        # adapter already produced a standard failure dict — honor it
        return _result(ok=False, provider=provider,
                       status_code=raw.get("status_code"),
                       error=raw.get("error") or "adapter error", raw=raw)
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return _result(ok=False, provider=provider, error="empty response", raw=raw)
    # Anything else: adapter returned a payload. Pass raw through; recv parses it.
    return _result(ok=True, provider=provider, raw=raw)


def _status_from(err) -> Optional[int]:
    """Best-effort HTTP status extraction from an adapter exception."""
    for attr in ("status_code", "status", "code"):
        v = getattr(err, attr, None)
        if isinstance(v, int):
            return v
    resp = getattr(err, "response", None)
    if resp is not None:
        v = getattr(resp, "status_code", None)
        if isinstance(v, int):
            return v
    return None


def in_flight() -> list:
    """Providers currently being called (for status/inspection)."""
    with _inflight_lock:
        return sorted(_inflight)


# ── concurrency cap for INTERNAL parallel workers ───────────────────
# The entry lock (above) blocks *external* re-entry (RUN mashing).
# Internal parallel — multiple workers hitting the SAME provider on
# purpose within one task — must stay OPEN. We don't block it; we bound
# how many run at once with a semaphore (the "4 burners" rule).
# Termux-safe default; tune via set_worker_concurrency().
_MAX_CONCURRENT_WORKERS = 4
_worker_sema = _threading.BoundedSemaphore(_MAX_CONCURRENT_WORKERS)


def set_worker_concurrency(n: int) -> int:
    """Set the max number of concurrent internal workers. Returns the value."""
    global _MAX_CONCURRENT_WORKERS, _worker_sema
    n = max(1, int(n))
    _MAX_CONCURRENT_WORKERS = n
    _worker_sema = _threading.BoundedSemaphore(n)
    return n


def worker_concurrency() -> int:
    return _MAX_CONCURRENT_WORKERS


# ── the narrow waist ────────────────────────────────────────────────

def call(
    provider: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
    max_calls: Optional[int] = None,
    fallback: Optional[List[str]] = None,
    on_status=None,
) -> Dict[str, Any]:
    """
    The single control point every AI call must pass through.

    Args:
        provider:  any entrance — "claude" | "groq" | "qwen" | ...
        prompt:    user prompt
        model:     model alias/name override
        config:    per-call connection overrides
        timeout:   seconds
        max_calls: max number of providers to try in the chain.
                   None (default) → try the whole chain (primary + all fallbacks).
                   The chain is finite, so it never loops. Set a number only to
                   cap it shorter (e.g. max_calls=1 = primary only, no fallback).
        fallback:  ordered provider chain to try if the primary is unhealthy/fatal.
                   None → no fallback (stop on failure; never loop).

    Returns: standard result dict (see _result), with calls_used set.
    """
    config = config or {}
    if not prompt or not prompt.strip():
        return _result(ok=False, provider=provider, error="empty prompt")

    # cap = how many providers in the chain we may try (not a block on
    # fallback). Trying a fallback after a failure is the whole point of the
    # chain; the chain is finite, so it cannot loop. Runaway parallelism is
    # bounded separately by the worker semaphore, not here.
    full_chain = [provider] + list(fallback or [])
    limit = len(full_chain) if max_calls is None else max(1, max_calls)
    chain = full_chain[:limit]
    calls_used = 0
    last: Dict[str, Any] = _result(ok=False, provider=provider, error="no provider tried")

    def _emit(stage, msg, **extra):
        if on_status:
            try:
                on_status(stage, msg, extra)
            except Exception:
                pass

    for prov in chain:
        prov = (prov or "").lower().strip()
        if not prov:
            continue

        # PRE — health gate. Costs zero network. Blocks rate-limited providers.
        h = health(prov)
        if not h["healthy"]:
            _emit("health", f"{prov} 건너뜀 ({h['reason']})", provider=prov)
            last = _result(ok=False, provider=prov, fatal=True,
                           retry_after=h.get("retry_after_ts"),
                           error=f"unhealthy: {h['reason']}", calls_used=calls_used)
            continue  # try next in chain (or end → stop)

        ptype = _provider_type(prov)
        adapter = _ADAPTERS.get(ptype, _adapter_ua)

        # ISOLATED (261017): no shared ua state -> no duplicate-call hazard ->
        # no lock. Concurrency is bounded by the isolated semaphore instead.
        if _ISOLATED and adapter is _adapter_ua:
            _emit("call", f"{prov} 호출 중...", provider=prov, type="isolated")
            with _iso_sema():
                res = _adapter_isolated(prov, prompt, model=model, config=config,
                                        timeout=timeout)
            calls_used += 1
            res["calls_used"] = calls_used
            _record_state(prov, res)
            if res.get("ok"):
                return res
            last = res
            if res.get("fatal"):
                _emit("fatal", f"{prov} 치명적 오류 — 폴백 시도", provider=prov)
            continue

        # IN-FLIGHT — if this provider is already being called, do not launch
        # a duplicate. Inform the caller it's busy instead.
        if not _acquire(prov):
            _emit("busy", f"{prov} 처리 중 — 잠시 후 다시", provider=prov)
            return _result(ok=False, provider=prov, busy=True,
                           error=f"{prov} is already processing a request",
                           calls_used=calls_used)

        _emit("call", f"{prov} 호출 중...", provider=prov, type=ptype)
        try:
            res = adapter(prov, prompt, model=model, config=config, timeout=timeout)
        finally:
            _release(prov)  # always release, even on adapter exception
        calls_used += 1
        res["calls_used"] = calls_used

        # POST — record state (success clears blocks, 429/5xx records retry_after).
        _record_state(prov, res)

        if res.get("ok"):
            return res

        # Failure: try the next provider in the (finite) chain.
        last = res
        if res.get("fatal"):
            _emit("fatal", f"{prov} 치명적 오류 — 폴백 시도", provider=prov)
        # loop continues to next provider in chain (if any). No retry of same provider.

    return last


# ── INTERNAL worker entry (parallel-friendly) ───────────────────────
# Used by the parallel pipeline (ua.chat workers). Unlike call():
#   - does NOT take the per-provider entry lock → many workers may run
#     against the same provider concurrently (this is intended parallelism)
#   - IS bounded by the worker semaphore (max concurrent)
#   - STILL passes the health gate and records state (429/fatal honored)
# This is the "burners" path: parallel stays open, but capped.

def dispatch_one(
    provider: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
) -> Dict[str, Any]:
    """One worker call. Parallel-safe, semaphore-bounded, health-gated."""
    config = config or {}
    prov = (provider or "").lower().strip()

    # health gate — a worker must not hammer a rate-limited provider either.
    h = health(prov)
    if not h["healthy"]:
        return _result(ok=False, provider=prov, fatal=True,
                       retry_after=h.get("retry_after_ts"),
                       error=f"unhealthy: {h['reason']}")

    ptype = _provider_type(prov)
    adapter = _ADAPTERS.get(ptype, _adapter_ua)

    # bound concurrency (NOT mutual exclusion) — N workers at a time.
    with _worker_sema:
        res = adapter(prov, prompt, model=model, config=config, timeout=timeout)
    res["calls_used"] = 1
    _record_state(prov, res)
    return res


# ── streaming entrance (CLI only for now) ───────────────────────────

def call_stream(
    provider: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 300,
):
    """
    Streaming variant for CLI providers. Yields SSE-ready dicts.

    Still passes the PRE health gate so a rate-limited provider yields a
    single error event instead of hammering the backend.
    """
    config = config or {}
    prov = (provider or "").lower().strip()

    h = health(prov)
    if not h["healthy"]:
        yield {"event": "error", "error": f"unhealthy: {h['reason']}",
               "fatal": True, "retry_after": h.get("retry_after_ts")}
        return

    if _provider_type(prov) == "cli":
        from usekit.classes.support.base.init.ai.sbi_ai_chat import stream_cli
        # IN-FLIGHT guard for streaming too (streams run long → high dup risk).
        if not _acquire(prov):
            yield {"event": "error", "error": f"{prov} is already processing a request",
                   "busy": True}
            return
        final = {"ok": False}
        try:
            for chunk in stream_cli(provider=prov, prompt=prompt, model=model,
                                    config=config, timeout=timeout):
                if chunk.get("event") == "done":
                    final = chunk
                yield chunk
        finally:
            _release(prov)
        _record_state(prov, {
            "ok": bool(final.get("ok")),
            "status_code": 200 if final.get("ok") else None,
            "error": final.get("error"),
        })
        return

    # Non-CLI (Gemini/qwen/openai/...): REAL token streaming, RAW path.
    # ua.run(prompt, on_delta=...) is the no-pipeline single call (no system /
    # history / meta injection — the caller, e.g. flow, owns the full prompt).
    # With the prov_openai.send Gemini→_gemini_native routing, on_delta makes it
    # stream real tokens. ua.run's send() is already gateway-guarded (_guarded →
    # guarded_direct_call: health + in-flight lock + state) and does NOT re-enter
    # dispatch_one → no double-lock, no recursion. We bridge on_delta → queue →
    # yield so the gateway stays a generator. (PRE health gate above pre-checked.)
    #
    # NOTE: mid-stream provider fallback is intentionally not attempted — once
    # tokens are emitted you cannot switch providers. A mid-stream failure
    # surfaces as an error event so the caller may retry non-streaming (which
    # keeps the full fallback chain via call()).
    import threading
    import queue as _queue

    q: "_queue.Queue" = _queue.Queue()
    box: Dict[str, Any] = {}

    def _work():
        try:
            from usekit import ua
            conn = _build_ua_conn(prov, model, config)
            ua.conn(prov, **conn)
            # raw single call; on_delta streams tokens as they arrive.
            res = ua.run(prompt, on_delta=lambda piece: q.put(("delta", piece)))
            box["res"] = res if isinstance(res, dict) else {"text": str(res)}
        except Exception as e:
            box["err"] = str(e)
        finally:
            q.put(("end", None))

    threading.Thread(target=_work, daemon=True).start()

    while True:
        kind, val = q.get()
        if kind == "delta":
            if val:
                yield {"event": "delta", "text": val}
        else:
            break

    if box.get("err"):
        _record_state(prov, {"ok": False, "status_code": None, "error": box["err"]})
        yield {"event": "error", "error": box["err"], "fatal": False}
        return

    res = box.get("res") or {"text": "", "_gw_blocked": "stream worker lost"}
    # ua.run returns the unified result; empty text or a gateway-blocked marker = fail.
    text = res.get("text", "")
    blocked = res.get("_gw_blocked")
    ok = bool(text) and not blocked
    _record_state(prov, {"ok": ok, "status_code": 200 if ok else None,
                         "error": None if ok else (blocked or "empty response")})
    if ok:
        yield {"event": "done", "ok": True, "text": text, "provider": prov}
    else:
        yield {"event": "error", "error": blocked or "empty response",
               "fatal": False}


__all__ = ["call", "call_stream", "dispatch_one", "health", "probe",
           "probe_all", "in_flight", "set_worker_concurrency",
           "worker_concurrency"]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
