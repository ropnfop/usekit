# Path: usekit.classes.support.base.init.ai.sbi_ai_job
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------
# AI Job — long-running CLI tasks decoupled from the HTTP request lifetime.
#
#   Why this exists:
#     stream_cli() reads the subprocess stdout synchronously and emits SSE
#     while the HTTP request is alive. For deep work (claude_code analyzing
#     a codebase, multi-file refactor, etc.) that may take many minutes,
#     the browser/network cannot reliably stay connected. A 30-second idle
#     means the user lost everything.
#
#   The design ("job + replay"):
#     start_job()    spawns the CLI as a background thread of the editor
#                    server process (which is itself nohup). Subprocess
#                    outlives any single HTTP request.
#     Each stream-json line is:
#       (1) appended to ~/.usekit/jobs/<job_id>/events.jsonl  (durable)
#       (2) pushed to in-memory subscribers (live SSE listeners)
#     When a client (re-)connects via stream_events():
#       (1) the full events.jsonl is replayed first  (catch up)
#       (2) then the live queue is drained as new events arrive
#       (3) the SSE ends when the job's terminal "done"/"error" event
#           has been sent.
#
#   Guarantees:
#     - Browser may disconnect / phone may sleep — subprocess keeps running.
#     - On reconnect, the client sees the complete history, in order, exactly once.
#     - session_id from the CLI is captured & saved so the user can `--resume`.
#     - Permission prompts can't stall the job: --permission-mode bypassPermissions.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import uuid
from typing import Any, Dict, Iterator, List, Optional


# ── filesystem layout ────────────────────────────────────────────────
# ~/.usekit/jobs/<job_id>/
#     meta.json         — provider, model, prompt(head), started, status, session_id...
#     events.jsonl      — every stream-json line, one per row, in arrival order
#     stderr.log        — CLI stderr (truncated on each line)

_JOBS_ROOT = os.path.expanduser("~/.usekit/jobs")


def _job_dir(job_id: str) -> str:
    return os.path.join(_JOBS_ROOT, job_id)


def _meta_path(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "meta.json")


def _events_path(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "events.jsonl")


def _stderr_path(job_id: str) -> str:
    return os.path.join(_job_dir(job_id), "stderr.log")


# ── in-memory registry ──────────────────────────────────────────────
# One entry per live job. Subscribers are added when an SSE client attaches.

_jobs_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}   # job_id -> {meta, subs:[Queue], lock, done:Event}


def _new_state(meta: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "meta": meta,
        "subs": [],                       # live subscriber queues (list[queue.Queue])
        "lock": threading.Lock(),         # protects subs / meta mutation
        "done": threading.Event(),        # set when subprocess fully finished
    }


# ── meta persistence ────────────────────────────────────────────────

def _write_meta(job_id: str, meta: Dict[str, Any]) -> None:
    p = _meta_path(job_id)
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _read_meta(job_id: str) -> Dict[str, Any]:
    p = _meta_path(job_id)
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


# ── claude_code command builder ─────────────────────────────────────
# We don't import cli/main.py to avoid coupling; we build the same
# argv it would build for `uk ai claude`. If the user installed
# claude-code in a different way, we still defer to `uk ai` as a
# fallback so behavior matches what they already use.

def _build_claude_cmd(prompt: str, *, model: Optional[str], session: Optional[str]) -> List[str]:
    """
    Build a command that runs claude_code in streaming JSON mode,
    using the existing `uk ai claude` wrapper so all auth/CLI discovery
    is reused. Adds --resume <session> when given.
    """
    cmd = ["uk", "ai", "claude"]
    if session:
        cmd.extend(["--resume", session])
    if model:
        cmd.extend(["--model", model])
    cmd.append(prompt)
    return cmd


def _project_cwd() -> Optional[str]:
    """Same cwd resolution `uk ai` uses, kept here to avoid import cycles."""
    for key in ("USEKIT_BASE", "BASE_PATH", "PROJECT_PATH"):
        v = os.environ.get(key)
        if v and os.path.isdir(v):
            return v
    try:
        from usekit.classes.core.env.loader_env import get_base_path
        p = str(get_base_path())
        if p and os.path.isdir(p):
            return p
    except Exception:
        pass
    return None


# ── runner thread ───────────────────────────────────────────────────

def _emit(job_id: str, ev: Dict[str, Any]) -> None:
    """Append one event to the job's jsonl + push to live subscribers."""
    # (1) durable append
    try:
        with open(_events_path(job_id), "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # (2) fan-out to live subscribers (best-effort, never block the runner)
    state = _jobs.get(job_id)
    if not state:
        return
    with state["lock"]:
        dead = []
        for q in state["subs"]:
            try:
                q.put_nowait(ev)
            except Exception:
                dead.append(q)
        for q in dead:
            try:
                state["subs"].remove(q)
            except ValueError:
                pass


def _update_meta(job_id: str, **fields) -> None:
    state = _jobs.get(job_id)
    if state:
        with state["lock"]:
            state["meta"].update(fields)
            _write_meta(job_id, state["meta"])
    else:
        m = _read_meta(job_id)
        m.update(fields)
        _write_meta(job_id, m)


def _runner(job_id: str, cmd: List[str], cwd: Optional[str]) -> None:
    """Background thread: spawn CLI, stream stdout, persist events."""
    _emit(job_id, {"event": "start", "ts": time.time(), "cmd": cmd})

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            text=True,
            cwd=cwd,
            bufsize=1,  # line-buffered
        )
    except FileNotFoundError as e:
        _emit(job_id, {"event": "error", "ts": time.time(),
                       "error": f"spawn failed: {e}"})
        _update_meta(job_id, status="error", error=str(e), ended=time.time())
        state = _jobs.get(job_id)
        if state:
            state["done"].set()
        return

    _update_meta(job_id, status="running", pid=proc.pid)

    session_id_captured: Optional[str] = None
    final_text = ""
    had_error = False

    # Drain stderr in a side-thread so it never blocks stdout reading.
    def _drain_stderr():
        try:
            with open(_stderr_path(job_id), "a", encoding="utf-8") as f:
                for line in proc.stderr:
                    f.write(line)
        except Exception:
            pass
    threading.Thread(target=_drain_stderr, name=f"job-{job_id}-stderr",
                     daemon=True).start()

    # Main stdout loop — one stream-json object per line.
    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                # forward raw line for transparency; clients can ignore
                _emit(job_id, {"event": "raw", "ts": time.time(), "line": line})
                continue

            # capture session_id wherever it appears
            sid = obj.get("session_id")
            if sid and sid != session_id_captured:
                session_id_captured = sid
                _update_meta(job_id, session_id=sid)
                _emit(job_id, {"event": "session", "ts": time.time(),
                               "session_id": sid})

            msg_type = obj.get("type")

            if msg_type == "assistant":
                content = obj.get("message", {}).get("content")
                texts: List[str] = []
                if isinstance(content, list):
                    for block in content:
                        bt = block.get("type")
                        if bt == "text" and block.get("text"):
                            texts.append(block["text"])
                        elif bt == "tool_use":
                            _emit(job_id, {"event": "tool_use", "ts": time.time(),
                                           "name": block.get("name"),
                                           "input": block.get("input")})
                elif isinstance(content, str) and content:
                    texts.append(content)
                if texts:
                    _emit(job_id, {"event": "delta", "ts": time.time(),
                                   "text": "".join(texts)})

            elif msg_type == "user":
                # tool results coming back to claude — emit lightweight signal
                _emit(job_id, {"event": "tool_result", "ts": time.time()})

            elif msg_type == "result":
                if obj.get("is_error"):
                    had_error = True
                    final_text = obj.get("result", "unknown error")
                else:
                    final_text = obj.get("result", "")

            else:
                # forward unknown types so nothing is lost
                _emit(job_id, {"event": "raw_msg", "ts": time.time(),
                               "type": msg_type, "obj": obj})
    finally:
        proc.wait()

    # Persist final session id at the global "last session" file too,
    # so `uk ai claude -c` from shell still works.
    if session_id_captured:
        try:
            sf = os.path.expanduser("~/.usekit/last_session")
            os.makedirs(os.path.dirname(sf), exist_ok=True)
            with open(sf, "w") as f:
                f.write(session_id_captured)
        except Exception:
            pass

    status = "error" if (had_error or proc.returncode not in (0, None)) else "done"
    _emit(job_id, {
        "event": status,                    # "done" or "error"
        "ts": time.time(),
        "returncode": proc.returncode,
        "text": final_text,
        "session_id": session_id_captured,
    })
    _update_meta(job_id, status=status, ended=time.time(),
                 returncode=proc.returncode, result=final_text,
                 session_id=session_id_captured)

    state = _jobs.get(job_id)
    if state:
        state["done"].set()


# ── public API ──────────────────────────────────────────────────────

def start(
    prompt: str,
    *,
    provider: str = "claude",
    model: Optional[str] = None,
    session: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Start a long-running AI job.

    Returns immediately with {job_id, status:"queued"}. The actual work
    runs in a background thread of the calling process and survives
    HTTP request disconnects.

    Currently only provider="claude" is implemented (CLI path).
    """
    prov = (provider or "claude").lower().strip()
    if prov != "claude":
        return {"ok": False, "error": f"job runner only supports claude (got {prov})"}
    if not prompt or not prompt.strip():
        return {"ok": False, "error": "empty prompt"}

    job_id = uuid.uuid4().hex[:12]
    os.makedirs(_job_dir(job_id), exist_ok=True)

    meta = {
        "job_id": job_id,
        "provider": prov,
        "model": model,
        "prompt_head": prompt[:200],
        "session_id_in": session,
        "session_id": None,
        "status": "queued",
        "started": time.time(),
        "ended": None,
    }
    _write_meta(job_id, meta)
    _jobs[job_id] = _new_state(meta)

    cmd = _build_claude_cmd(prompt, model=model, session=session)
    cwd = _project_cwd()
    t = threading.Thread(target=_runner, args=(job_id, cmd, cwd),
                         name=f"job-{job_id}", daemon=True)
    t.start()
    return {"ok": True, "job_id": job_id, "status": "queued"}


def status(job_id: str) -> Dict[str, Any]:
    """Current status snapshot (cheap, no streaming)."""
    state = _jobs.get(job_id)
    if state:
        with state["lock"]:
            return dict(state["meta"])
    # fall back to disk for jobs from previous editor sessions
    m = _read_meta(job_id)
    return m or {"ok": False, "error": "unknown job_id"}


def list_jobs(limit: int = 20) -> List[Dict[str, Any]]:
    """List recent jobs (most recent first), reading from disk."""
    try:
        entries = []
        for jid in os.listdir(_JOBS_ROOT):
            m = _read_meta(jid)
            if m:
                entries.append(m)
        entries.sort(key=lambda e: e.get("started", 0), reverse=True)
        return entries[:limit]
    except FileNotFoundError:
        return []


def stream_events(job_id: str, *, from_start: bool = True) -> Iterator[Dict[str, Any]]:
    """
    Iterate events for SSE. Replays history (events.jsonl) first, then
    follows live updates until the job's terminal event has been yielded.

    Safe to call after disconnect/reconnect: history is the source of truth.
    """
    import queue

    # 1) replay historical events from disk
    seen = 0
    if from_start:
        try:
            with open(_events_path(job_id), encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    seen += 1
        except FileNotFoundError:
            pass

    # 2) attach as a live subscriber for new events
    state = _jobs.get(job_id)
    if not state:
        # job not in-memory: either already finished (history is complete) or unknown
        return

    q: "queue.Queue[Dict[str,Any]]" = queue.Queue(maxsize=10000)
    with state["lock"]:
        # only attach if not already terminal
        if state["done"].is_set():
            # job finished while we were replaying; we already have all events
            return
        state["subs"].append(q)

    try:
        while True:
            try:
                ev = q.get(timeout=15.0)
            except queue.Empty:
                # heartbeat — lets the HTTP layer keep the connection healthy
                yield {"event": "ping", "ts": time.time()}
                if state["done"].is_set():
                    # job finished but no more events to drain
                    return
                continue
            yield ev
            if ev.get("event") in ("done", "error"):
                return
    finally:
        with state["lock"]:
            try:
                state["subs"].remove(q)
            except ValueError:
                pass


def cancel(job_id: str) -> Dict[str, Any]:
    """Best-effort: terminate the underlying subprocess if still running."""
    state = _jobs.get(job_id)
    if not state:
        m = _read_meta(job_id)
        return {"ok": False, "error": "not running"} if not m else {"ok": True, "status": m.get("status")}
    meta = state["meta"]
    pid = meta.get("pid")
    if pid and not state["done"].is_set():
        try:
            import signal
            os.kill(pid, signal.SIGTERM)
            _emit(job_id, {"event": "cancel", "ts": time.time()})
            _update_meta(job_id, status="cancelled", ended=time.time())
            state["done"].set()
            return {"ok": True, "status": "cancelled"}
        except ProcessLookupError:
            return {"ok": True, "status": meta.get("status", "unknown")}
        except Exception as e:
            return {"ok": False, "error": str(e)}
    return {"ok": True, "status": meta.get("status", "done")}


__all__ = ["start", "status", "list_jobs", "stream_events", "cancel"]

# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
