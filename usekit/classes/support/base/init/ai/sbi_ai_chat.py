# Path: usekit.classes.support.base.init.ai.sbi_ai_chat.py
# -----------------------------------------------------------------------------------------------
#  Editor AI CHAT serving — provider dispatch.
#
#  Two paths:
#    _serve_via_ua()  →  ua.conn() + ua.run() (Qwen, Gemini, Ollama, ...)
#    _serve_via_cli() →  subprocess to a local CLI (Claude Code, ...)
#
#  Both return the same shape:
#    {"ok": bool, "text": str, "error": str | None,
#     "provider": str, "model": str, "elapsed": float}
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import os
import subprocess
import time
from typing import Any, Dict, Optional


# CLI tier (subprocess path) is determined from sys_ai.yaml.
# Legacy alias 'claude' (used by old float_ai.js shell path) is mapped to
# 'claude_code' on the fly so existing callers keep working.
_LEGACY_PROVIDER_ALIASES = {
    "claude": "claude_code",
}


def serve_chat(
    provider: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    Main entry — dispatch one chat turn to the right backend.

    Args:
        provider: 'qwen', 'gemini', 'ollama', 'openai', 'claude_code', ...
                  (legacy 'claude' is accepted and maps to 'claude_code')
        prompt:   full prompt text (already context-prefixed by the JS side)
        model:    optional model alias (e.g. 'G20F', 'GPT4O', 'SONNET') or full name
        config:   optional per-call overrides (temperature, max_tokens, base_url, api_key, ...)
        timeout:  seconds before giving up (applies to CLI path; ua respects this loosely)

    Returns:
        {"ok": True,  "text": "...", "provider": ..., "model": ..., "elapsed": ...}
        {"ok": False, "error": "...", "provider": ..., "model": ..., "elapsed": ...}
    """
    if not prompt or not prompt.strip():
        return _err(provider, model, "empty prompt", 0.0)

    prov = (provider or "").lower().strip()
    if not prov:
        return _err(provider, model, "no provider specified", 0.0)

    # Map legacy aliases (e.g. 'claude' → 'claude_code')
    prov = _LEGACY_PROVIDER_ALIASES.get(prov, prov)

    config = dict(config or {})

    # Route by sys_ai.yaml tier
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import is_cli
        cli_route = is_cli(prov)
    except ImportError:
        # Fallback if meta module missing — only legacy claude path
        cli_route = prov == "claude_code"

    if cli_route:
        return _serve_via_cli(prov, prompt, model=model, config=config, timeout=timeout)
    return _serve_via_ua(prov, prompt, model=model, config=config)


# ── ua path: OpenAI-compatible / Gemini / Ollama / ... ───────────────

def _serve_via_ua(
    provider: str,
    prompt: str,
    *,
    model: Optional[str],
    config: Dict[str, Any],
) -> Dict[str, Any]:
    """Route through the LLM API layer (ua).

    Uses ua.chat() in single/fast mode — no parallel workers.
    This is safe for worker dispatch (no recursion risk).
    For full pipeline (parallel + recall), use serve_chat_full().
    """
    t0 = time.time()
    try:
        from usekit import ua
        from usekit.classes.support.base.init.ai.sbi_ai_config import get_provider
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            providers as _meta_providers,
            resolve_model,
            default_model,
        )
    except ImportError as e:
        return _err(provider, model, f"ua not available: {e}", time.time() - t0)

    # Layered config:
    #   1. sys_ai.yaml defaults (base_url, key_env → env var)
    #   2. user-stored config (~/.usekit/llm_providers.json) — overrides yaml
    #   3. per-call overrides — overrides everything
    #   4. explicit model (alias → resolved full name)
    conn_kwargs: Dict[str, Any] = {}

    # 1. sys_ai.yaml — base_url + key_env lookup
    yaml_meta = _meta_providers().get(provider) or {}
    if yaml_meta.get("base_url"):
        conn_kwargs["base_url"] = yaml_meta["base_url"]
    key_env = yaml_meta.get("key_env")
    if key_env:
        env_key = os.environ.get(key_env)
        if env_key:
            conn_kwargs["api_key"] = env_key

    # 2. stored per-provider config
    stored = get_provider(provider)
    if stored:
        conn_kwargs.update(stored)

    # 3. per-call overrides
    conn_kwargs.update(config)

    # 4. resolve model: explicit > stored > yaml default
    chosen_model = model or conn_kwargs.get("model") or default_model(provider)
    if chosen_model:
        # alias → full name (e.g. 'G20F' → 'gemini-2.0-flash')
        conn_kwargs["model"] = resolve_model(chosen_model, provider=provider)

    try:
        ua.conn(provider, **conn_kwargs)
    except Exception as e:
        return _err(provider, model, f"conn failed: {e}", time.time() - t0)

    # fast/single dispatch — keep it single ON PURPOSE.
    #   WHY single: parallel/auto runs a planner that splits the prompt into
    #   subtasks for workers — short/simple prompts get "melted" (original
    #   intent smeared across fan-out). single keeps the prompt intact = safe.
    #   Also this path is called during worker dispatch, so parallel here
    #   would risk worker-calls-worker recursion. Full pipeline = serve_chat_full().
    #   Dial: single=intact(current) / parallel=fan-out(⚠ melt+recursion) / auto.
    # BUGFIX: this call was missing — `result` was read below without ever
    # being assigned (NameError).
    try:
        result = ua.chat(prompt, mode="single")
    except Exception as e:
        return _err(provider, model, f"chat failed: {e}", time.time() - t0)

    text = (result or {}).get("text", "") if isinstance(result, dict) else str(result)
    elapsed = time.time() - t0
    return {
        "ok": True,
        "text": text,
        "error": None,
        "provider": provider,
        "model": conn_kwargs.get("model", "") or "",
        "model_alias": chosen_model or "",
        "elapsed": round(elapsed, 3),
    }


# ── serve_chat_full: full pipeline via ua.chat() ─────────────────────

def serve_chat_full(
    provider: str,
    prompt: str,
    *,
    mode: Optional[str] = "auto",
    worker: Optional[str] = None,
    workers: int = 3,
    quality: str = "auto",
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    input_text: str = "",
    input_paths: Optional[list] = None,
    recirculate: bool = True,
    max_rounds: int = 2,
    on_status=None,
    timeout: int = 120,
) -> Dict[str, Any]:
    """
    Full pipeline chat via ua.chat() — blocking, returns dict.

    Unlike serve_chat (single LLM call via ua.run), this uses the
    full ua.chat() pipeline: auto-quality, parallel workers, recall,
    final_judge, etc.

    Safe to call from editor /api/ai_chat or Python scripts.
    NOT safe to call from worker dispatch (use serve_chat for workers).

    Returns: {ok, text, error, provider, model, elapsed, quality, effective_mode, ...}
    """
    t0 = time.time()
    prov = (provider or "").lower().strip()
    if not prov or not prompt or not prompt.strip():
        return _err(provider, model, "missing provider or prompt", 0.0)

    config = dict(config or {})

    try:
        from usekit import ua
        from usekit.classes.support.base.init.ai.sbi_ai_config import get_provider
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            providers as _meta_providers,
            resolve_model,
            default_model,
        )
    except ImportError as e:
        return _err(provider, model, f"ua not available: {e}", time.time() - t0)

    conn_kwargs: Dict[str, Any] = {}
    yaml_meta = _meta_providers().get(prov) or {}
    if yaml_meta.get("base_url"):
        conn_kwargs["base_url"] = yaml_meta["base_url"]
    key_env = yaml_meta.get("key_env")
    if key_env:
        env_key = os.environ.get(key_env)
        if env_key:
            conn_kwargs["api_key"] = env_key

    stored = get_provider(prov)
    if stored:
        conn_kwargs.update(stored)
    conn_kwargs.update(config)

    chosen_model = model or conn_kwargs.get("model") or default_model(prov)
    if chosen_model:
        conn_kwargs["model"] = resolve_model(chosen_model, provider=prov)

    try:
        ua.conn(prov, **conn_kwargs)
    except Exception as e:
        return _err(provider, model, f"conn failed: {e}", time.time() - t0)

    w_prov = worker or prov

    try:
        chat_result = ua.chat(
            prompt,
            mode=mode or "auto",
            worker=w_prov,
            workers=workers,
            quality=quality,
            input_text=input_text,
            input_paths=input_paths or [],
            recirculate=recirculate,
            max_rounds=max_rounds,
            on_status=on_status,
        )
    except Exception as e:
        return _err(provider, model, f"chat failed: {e}", time.time() - t0)
    text = chat_result.get("text", "")
    elapsed = time.time() - t0
    return {
        "ok": True,
        "text": text,
        "error": None,
        "provider": prov,
        "model": conn_kwargs.get("model", "") or "",
        "model_alias": chosen_model or "",
        "elapsed": round(elapsed, 3),
        "quality": chat_result.get("quality", ""),
        "effective_mode": chat_result.get("effective_mode", ""),
        "workers_used": chat_result.get("workers_used", 0),
        "workers_requested": chat_result.get("workers_requested", 0),
    }


# ── CLI path: Claude Code (and any other CLI we add later) ──────────

def _serve_via_cli(
    provider: str,
    prompt: str,
    *,
    model: Optional[str],
    config: Dict[str, Any],
    timeout: int,
) -> Dict[str, Any]:
    """
    Route through `uk ai <provider> -c <prompt>` subprocess.

    Why use uk and not call the CLI directly:
      uk ai already knows how to find the CLI, parse JSON Lines stream,
      handle session id, etc. (see usekit.cli.main._run_ai). Reusing it
      means one place to maintain CLI integration.

    Note: yaml uses 'claude_code' but the `uk ai` subcommand still expects
    'claude' as the provider name (it's the historical CLI identifier).
    We map here.
    """
    t0 = time.time()

    # yaml provider name → uk ai CLI name
    cli_name = _CLI_NAME_MAP.get(provider, provider)

    # Resolve alias to full name for the CLI's --model flag.
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            resolve_model, default_model,
        )
        chosen_model = model or default_model(provider)
        full_model = resolve_model(chosen_model, provider=provider) if chosen_model else ""
    except ImportError:
        chosen_model = model or ""
        full_model = chosen_model

    cmd = ["uk", "ai", cli_name, prompt]  # prompt is positional; never use -c (it means --continue)
    if full_model and full_model not in ("auto", ""):
        cmd.extend(["--model", full_model])

    # Resolve project root for CLI working directory
    pdir = None
    try:
        from usekit.classes.core.env.loader_env import get_base_path
        pdir = str(get_base_path())
    except Exception:
        pass
    if not pdir:
        pdir = os.environ.get("USEKIT_BASE") or os.environ.get("BASE_PATH")

    # Pass env so child `uk ai` and `node cli.js` also see USEKIT_BASE
    env = os.environ.copy()
    if pdir and os.path.isdir(pdir):
        env["USEKIT_BASE"] = str(pdir)

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=pdir if pdir and os.path.isdir(pdir) else None,
            env=env,
        )
    except FileNotFoundError:
        return _err(provider, model, "uk CLI not found on PATH", time.time() - t0)
    except subprocess.TimeoutExpired:
        return _err(provider, model, f"timeout after {timeout}s", time.time() - t0)

    elapsed = time.time() - t0
    text = (proc.stdout or "").strip()
    stderr = (proc.stderr or "").strip()

    if proc.returncode != 0:
        # Surface stderr — it usually contains the actionable message.
        msg = stderr or text or f"exit {proc.returncode}"
        return _err(provider, model, msg, elapsed)

    return {
        "ok": True,
        "text": text or "(no response)",
        "error": None,
        "provider": provider,
        "model": full_model,
        "model_alias": chosen_model or "",
        "elapsed": round(elapsed, 3),
    }


# ── CLI streaming path: yields SSE chunks instead of blocking ────────

def stream_cli(
    provider: str,
    prompt: str,
    *,
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    timeout: int = 300,
):
    """
    Generator that yields SSE-ready dicts from a CLI subprocess.

    Instead of blocking until completion, this uses Popen and reads
    stdout line-by-line, yielding parsed events as they arrive.

    Yields dicts with "event" key:
        {"event": "status", "type": "start", "provider": ...}
        {"event": "delta",  "text": "..."}
        {"event": "tool",   "name": "...", "status": "..."}
        {"event": "done",   "ok": True, "text": "...", "elapsed": ...}
        {"event": "error",  "error": "..."}
    """
    import json as _json

    prov = _LEGACY_PROVIDER_ALIASES.get(
        (provider or "").lower().strip(),
        (provider or "").lower().strip(),
    )
    cli_name = _CLI_NAME_MAP.get(prov, prov)

    # Resolve model
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_meta import (
            resolve_model, default_model,
        )
        chosen_model = model or default_model(prov)
        full_model = resolve_model(chosen_model, provider=prov) if chosen_model else ""
    except ImportError:
        chosen_model = model or ""
        full_model = chosen_model

    cmd = ["uk", "ai", cli_name, prompt]  # prompt is positional; never use -c (it means --continue)
    if full_model and full_model not in ("auto", ""):
        cmd.extend(["--model", full_model])

    # Project dir
    pdir = None
    try:
        from usekit.classes.core.env.loader_env import get_base_path
        pdir = str(get_base_path())
    except Exception:
        pass
    if not pdir:
        pdir = os.environ.get("USEKIT_BASE") or os.environ.get("BASE_PATH")

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"  # Force line-buffered stdout in child
    if pdir and os.path.isdir(pdir):
        env["USEKIT_BASE"] = str(pdir)

    t0 = time.time()

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,  # Line-buffered
            cwd=pdir if pdir and os.path.isdir(pdir) else None,
            env=env,
        )
    except FileNotFoundError:
        yield {"event": "error", "error": "uk CLI not found on PATH"}
        return

    yield {"event": "status", "type": "start", "provider": prov}

    full_text = ""

    try:
        # Use readline() instead of iterator — iterator buffers internally
        while True:
            line = proc.stdout.readline()
            if not line:
                # EOF — process finished or pipe closed
                break

            # Timeout check
            if time.time() - t0 > timeout:
                proc.kill()
                yield {"event": "error", "error": f"timeout after {timeout}s"}
                return

            line = line.strip()
            if not line:
                continue

            try:
                obj = _json.loads(line)
            except _json.JSONDecodeError:
                # Non-JSON output — treat as raw text delta
                full_text += line + "\n"
                yield {"event": "delta", "text": line + "\n"}
                continue

            msg_type = obj.get("type")

            if msg_type == "assistant":
                content = obj.get("message", {}).get("content")
                delta = ""
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") == "text" and block.get("text"):
                            delta += block["text"]
                elif isinstance(content, str):
                    delta = content
                if delta:
                    full_text += delta
                    yield {"event": "delta", "text": delta}

            elif msg_type == "result":
                is_error = obj.get("is_error", False)
                result_text = obj.get("result", "")
                if is_error:
                    yield {"event": "error", "error": result_text}
                # result is also captured in done event below

            elif msg_type in ("tool_use",):
                tool_name = ""
                inp = obj.get("message", {}).get("content")
                if isinstance(inp, list):
                    for block in inp:
                        if block.get("type") == "tool_use":
                            tool_name = block.get("name", "")
                yield {"event": "tool", "name": tool_name, "action": "start"}

            elif msg_type in ("tool_result",):
                yield {"event": "tool", "name": "", "action": "done"}

        proc.wait(timeout=max(1, timeout - int(time.time() - t0)))

    except subprocess.TimeoutExpired:
        proc.kill()
        yield {"event": "error", "error": f"timeout after {timeout}s"}
        return
    except Exception as e:
        try:
            proc.kill()
        except Exception:
            pass
        yield {"event": "error", "error": str(e)}
        return

    elapsed = round(time.time() - t0, 3)
    stderr_out = ""
    try:
        stderr_out = (proc.stderr.read() or "").strip()
    except Exception:
        pass

    ok = proc.returncode == 0
    if not ok and not full_text:
        full_text = stderr_out or f"exit {proc.returncode}"

    yield {
        "event": "done",
        "ok": ok,
        "text": full_text.strip(),
        "error": stderr_out if not ok else None,
        "provider": prov,
        "model": full_model,
        "model_alias": chosen_model or "",
        "elapsed": elapsed,
    }


# yaml-side name → `uk ai <name>` subcommand
_CLI_NAME_MAP = {
    "claude_code": "claude",
    # future: 'codex' → 'codex', 'gemini_cli' → 'gemini', etc.
}


# ── shared error shape ─────────────────────────────────────────────

def _err(provider: Any, model: Any, msg: str, elapsed: float) -> Dict[str, Any]:
    return {
        "ok": False,
        "text": "",
        "error": str(msg),
        "provider": str(provider or ""),
        "model": str(model or ""),
        "model_alias": str(model or ""),
        "elapsed": round(elapsed, 3),
    }


__all__ = ["serve_chat", "stream_cli", "serve_chat_v2", "serve_chat_full"]


# ── serve_chat_v2: generator that yields SSE-ready dicts ─────────────
#    Uses ua.chat() pipeline (quality modes, parallel workers, recall)
#    with on_status callback to emit intermediate progress.

def serve_chat_v2(
    provider: str,
    prompt: str,
    *,
    mode: Optional[str] = "auto",
    worker: Optional[str] = None,
    workers: int = 3,
    quality: str = "auto",
    model: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None,
    input_text: str = "",
    input_paths: Optional[list] = None,
    images: Optional[list] = None,
    search: bool = False,
    recirculate: bool = True,
    max_rounds: int = 2,
    timeout: int = 120,
    continue_: bool = False,
    client_session_id: str = "",
    slot: str = "",
):
    """
    Generator that yields SSE-ready dicts from ua.chat() pipeline.

    Unlike serve_chat (blocking), this uses on_status callbacks to
    yield intermediate stage progress in real-time.

    Yields:
        {"event": "status",      "stage": "quality",     "msg": "..."}
        {"event": "status",      "stage": "worker",      "msg": "...", "progress": "1/3"}
        {"event": "status",      "stage": "worker_done", "msg": "...", "progress": "2/3"}
        {"event": "status",      "stage": "judge",       "msg": "..."}
        {"event": "status",      "stage": "assemble",    "msg": "..."}
        {"event": "status",      "stage": "final_judge", "msg": "..."}
        {"event": "done",        "ok": True, "text": "...", "elapsed": ...}
        {"event": "error",       "error": "..."}
    """
    import queue
    import threading

    if not prompt or not prompt.strip():
        yield {"event": "error", "error": "empty prompt"}
        return

    prov = (provider or "").lower().strip()
    if not prov:
        yield {"event": "error", "error": "no provider specified"}
        return

    # Status queue — on_status callback pushes here, main thread yields
    status_q: queue.Queue = queue.Queue()

    def _on_status(stage, msg, extra=None):
        status_q.put({"event": "status", "stage": stage, "msg": msg, **(extra or {})})

    def _on_delta(piece):
        # Token chunk from the adapter → SSE 'delta' event (real-time text).
        if piece:
            status_q.put({"event": "delta", "text": piece})

    # Result container
    result_box: list = []
    error_box: list = []
    session_box: list = []  # active session_id (for client tracking)

    def _record_call(ok, finish, elapsed_ms=None, err_type=None, err_summary=None,
                     usage=None, ctx_mode=None, turns_merged=None, msg_seq=None,
                     output_text=None, input_text=None):
        """Persist one TSK_CALL telemetry row at a terminal event (done/error).

        One row per call, failures included (schema: "failures MUST be
        recorded"). Best-effort: a DB failure is surfaced (P1-3), never crashes
        the stream. usage={prompt,completion,total} when ua.chat exposes it
        (single/fast paths). ctx_mode/turns_merged answer "summary or full".
        """
        sid = session_box[0] if session_box else ""
        u = usage or {}
        # C1/C2: own the call_id so the JSONL body and the TSK_CALL row share it,
        # then write input/output bodies (debug/trace levels only) and keep log_ref.
        import uuid
        cid = f"call_{uuid.uuid4().hex[:12]}"
        log_ref = None
        tlevel = None
        try:
            from usekit.llm.base.init.lli_calllog import get_telemetry_level, append_call_log
            tlevel = get_telemetry_level()
            if ok and output_text is not None:
                log_ref = append_call_log(cid, level=tlevel,
                                          input_prompt=(input_text or prompt),
                                          output_text=output_text)
        except Exception as _e:
            from usekit.llm.history import _db_fail
            _db_fail("append_call_log", _e, sid=sid)
        try:
            from usekit.llm.base.init.lli_db import record_call
            record_call(
                session_id=sid, provider=prov, model=model or "",
                ok=ok, finish=finish, kind="live", elapsed_ms=elapsed_ms,
                ctx_mode=ctx_mode, turns_merged=turns_merged,
                prompt_tokens=u.get("prompt"),
                completion_tokens=u.get("completion"),
                total_tokens=u.get("total"),
                error_type=err_type, error_summary=err_summary,
                msg_seq=msg_seq, call_id=cid,
                log_ref=log_ref, telemetry_level=tlevel,
            )
        except Exception as _e:
            from usekit.llm.history import _db_fail
            _db_fail("record_call", _e, sid=sid)

    def _run_chat():
        """Run ua.chat() in a background thread."""
        try:
            from usekit import ua
            from usekit.classes.support.base.init.ai.sbi_ai_config import get_provider
            from usekit.classes.support.base.init.ai.sbi_ai_meta import (
                providers as _meta_providers,
                resolve_model,
                default_model,
            )

            # Build connection kwargs (same logic as _serve_via_ua)
            conn_kwargs: Dict[str, Any] = {}
            yaml_meta = _meta_providers().get(prov) or {}
            if yaml_meta.get("base_url"):
                conn_kwargs["base_url"] = yaml_meta["base_url"]
            key_env = yaml_meta.get("key_env")
            if key_env:
                env_key = os.environ.get(key_env)
                if env_key:
                    conn_kwargs["api_key"] = env_key

            stored = get_provider(prov)
            if stored:
                conn_kwargs.update(stored)
            if config:
                conn_kwargs.update(config)

            chosen_model = model or conn_kwargs.get("model") or default_model(prov)
            if chosen_model:
                conn_kwargs["model"] = resolve_model(chosen_model, provider=prov)

            # Slot ownership: rides as a conn() routing flag (skipped from adapter
            # config in ua.conn) so the minted session records its owning slot.
            # Single source of truth for Memory Editor LINKED/ORPHAN split.
            if slot:
                conn_kwargs["slot"] = slot

            # Session reuse (docs ua_chat.md L156: "한 번 conn, 세션 재사용").
            # Continue ON + same provider already connected → skip conn so the
            # ua history (and its TSK_SESSION row) carries over. Otherwise New:
            # a fresh conn() makes a new session_id. provider change always reconns.
            # Continue reuse guard: same provider + connected + an active live
            # session actually exists. Without the session_id check, "same
            # provider" alone could re-bind to a stale/global ua session.
            _active_sid = getattr(ua._history, "session_id", None)
            already = (
                (ua._provider_name == prov)
                and (ua._adapter is not None)
                and bool(_active_sid)
            )
            # P1-1: client round-trips the session id it last saw. If Continue is
            # ON and the client's id differs from the live ua session (typically
            # after a server restart, or when returning to a slot whose session
            # is no longer the live one), reattach the exact session and restore
            # its turns from TSK_MESSAGE. This must happen BEFORE add()/build():
            # without it, ua would start at seq=0 and ON CONFLICT(session_id, seq)
            # would overwrite the slot's existing rows (silent data loss), and the
            # model would also see no prior context.
            _restored_from_db = False
            if continue_ and client_session_id and client_session_id != _active_sid:
                # Need a connected adapter first (conn for this provider), but
                # without minting a brand-new session we then throw away.
                if not (ua._provider_name == prov and ua._adapter is not None):
                    ua.conn(prov, **conn_kwargs)
                try:
                    ua._history.load(client_session_id)  # sets session_id + _turns
                    _restored_from_db = bool(
                        getattr(ua._history, "session_id", "") == client_session_id
                    )
                except Exception:
                    _restored_from_db = False
                # Re-evaluate: if the load succeeded we now have the right session.
                _active_sid = getattr(ua._history, "session_id", None)
                already = _restored_from_db or already

            # Session isolation: a NEW slot/session sends an EMPTY client_session_id.
            # `already` only checks whether ANY live ua session exists — NOT whether
            # it belongs to THIS slot — so an empty id with a leftover live session
            # from a different slot would reuse it here and leak that slot's history
            # (the cross-slot SRS NOTE / marker leak: a fresh slot replying with a
            # prior slot's turns). Require a non-empty client_session_id to reuse; an
            # empty id falls through to `elif continue_` and mints a fresh MAIN
            # session (conn() reset_memory()s prior turns) — exactly that branch's
            # stated intent ("client had no id to round-trip -> new main session").
            if continue_ and client_session_id and (already or _restored_from_db):
                ua.set_temp(False)
                # Reuse keeps the live/restored session, so conn() is SKIPPED —
                # which means _project_meta_on + guide-suppression + system meta
                # would stay frozen at this session's first conn. Re-sync them to
                # THIS call's config so toggling General USEKIT Project mid-session
                # takes effect and the legacy LLM.md/CLAUDE.md guide stays
                # suppressed (SRS NOTE leak fix). history still accumulates under
                # the same sid.
                ua.sync_project_meta(bool(conn_kwargs.get("project_meta")))
            elif continue_:
                # Continue ON but no live/restored session yet — this is the FIRST
                # send of a new main session (no live ua session, and the client
                # had no id to round-trip). It must NOT fall into the temp branch:
                # Continue ON means "keep accumulating", so mint a real MAIN session.
                # conn() mints a fresh provider session id and create_session()s it
                # (kind='live'); set_temp(False) keeps turns durable (0/1/1/main).
                # The done event returns this main sid, so the client stores it in
                # _activeLiveSessionId and round-trips it on the next send — every
                # following ON turn then accumulates under this one TSK_SESSION,
                # and the first user message backfills the session title (H1).
                #
                # Bug history: previously Continue ON first-send dropped here into
                # the temp branch, so the client only ever got temp_ ids (stored in
                # _activeTempSessionId, never _activeLiveSessionId) → it kept sending
                # session_id="" → server kept minting temp/empty sessions every turn
                # (empty main rows + turns stranded in temp). Splitting ON out fixes it.
                ua.conn(prov, **conn_kwargs)
                ua.set_temp(False)
            else:
                # §4.8 Temporary (Continue OFF only): isolate from any main_sid. Mint a
                # temp_sid (or reuse the one the client round-trips so OFF turns
                # accumulate in ONE temp session, not a new one each send — §4.9
                # "하나의 temp_sid 누적"). conn() first to bind the adapter, then
                # swap history.session_id to the temp id. set_temp(True) makes
                # chat() tag every turn 1/0/0/'temporary' (restore/summary excluded).
                ua.conn(prov, **conn_kwargs)
                if client_session_id and client_session_id.startswith("temp_"):
                    temp_sid = client_session_id          # reuse → accumulate
                else:
                    import uuid as _uuid
                    temp_sid = f"temp_{prov}_{_uuid.uuid4().hex[:8]}"
                ua._history.session_id = temp_sid
                try:
                    from usekit.llm.base.init.lli_db import create_session
                    create_session(temp_sid, prov, conn_kwargs.get("model", ""), conn_kwargs,
                                   slot=conn_kwargs.get("slot", ""))
                except Exception as _e:
                    # Stay memory-only if the DB is unavailable, but surface it
                    # (P1-3). A swallowed error here is how a schema gap (e.g. a
                    # missing slot column) silently stranded sessions: turns kept
                    # saving while the parent TSK_SESSION row never got created.
                    from usekit.llm.history import _db_fail
                    _db_fail("create_session(temp)", _e, sid=temp_sid)
                ua.set_temp(True)

            # Capture the active session id so the client can display/track it.
            try:
                session_box.append(ua._history.session_id)
            except Exception:
                pass

            # Determine worker provider — default to same provider
            w_prov = worker or prov

            chat_result = ua.chat(
                prompt,
                mode=mode or "auto",
                worker=w_prov,
                workers=workers,
                quality=quality,
                input_text=input_text,
                input_paths=input_paths or [],
                images=images or [],
                search=search,
                recirculate=recirculate,
                max_rounds=max_rounds,
                on_status=_on_status,
                on_delta=_on_delta,
            )
            result_box.append(chat_result)
        except Exception as e:
            error_box.append(str(e))
        finally:
            status_q.put(None)  # sentinel

    # Start background thread
    yield {"event": "status", "stage": "start", "msg": "시작...", "provider": prov}
    t = threading.Thread(target=_run_chat, daemon=True)
    t.start()

    # Yield status events as they arrive
    while True:
        try:
            item = status_q.get(timeout=timeout)
        except queue.Empty:
            _record_call(0, "error", err_type="timeout",
                         err_summary=f"timeout after {timeout}s")
            yield {"event": "error", "error": f"timeout after {timeout}s"}
            return

        if item is None:
            # Thread finished
            break
        yield item

    # Final result
    if error_box:
        _record_call(0, "error", err_type="chat_error",
                     err_summary=str(error_box[0])[:200])
        yield {"event": "error", "error": error_box[0]}
    elif result_box:
        r = result_box[0]
        _record_call(1, r.get("finish") or "stop",
                     elapsed_ms=int(round(r.get("elapsed", 0) * 1000)),
                     usage=r.get("usage"),
                     ctx_mode=r.get("ctx_mode"),
                     turns_merged=r.get("turns_merged"),
                     msg_seq=r.get("assistant_seq"),
                     output_text=r.get("text", ""),
                     input_text=r.get("final_prompt"))
        yield {
            "event": "done",
            "ok": True,
            "text": r.get("text", ""),
            "reasoning": r.get("reasoning", ""),
            "elapsed": r.get("elapsed", 0),
            "quality": r.get("quality", ""),
            "effective_mode": r.get("effective_mode", ""),
            "workers_used": r.get("workers_used", 0),
            "provider": prov,
            "model": model or "",
            "session_id": (session_box[0] if session_box else ""),
        }
    else:
        _record_call(0, "error", err_type="no_result", err_summary="no result")
        yield {"event": "error", "error": "no result"}

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
