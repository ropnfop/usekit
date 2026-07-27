# Path: usekit.llm.handler.ua_handler.py
# -----------------------------------------------------------------------
#  UA — AI/LLM Handler (same level as ud/ut/uw)
#
#  ua.conn("qwen")          connect provider
#  ua.send("prompt")        send → raw response
#  ua.recv(res)             parse → unified dict
#  ua.ask("prompt")         one-shot → text
#  ua.run("prompt")         one-shot → full dict
#  ua.chat("prompt")        smart dispatch (single/parallel/auto)
#  ua.close()               close session
#
#  ua.set(k=v)              config (temperature, max_tokens, model)
#  ua.get("k")              read config
#  ua.key("sk-xxx")         set api key
#  ua.ping()                health check
#  ua.warm()                ensure model warm
#  ua.info()                session info
# -----------------------------------------------------------------------

from usekit.llm.base.init.lli_conn import resolve_provider, get_default_url, get_provider_config
from usekit.llm.base.init.lli_config import LLMConfig
from usekit.llm.base.init.lli_key import KeyStore
from usekit.llm.base.load.lll_send import send as _send
from usekit.llm.base.load.lll_warm import classify_state, is_warm
from usekit.llm.base.post.llp_recv import recv as _recv
from usekit.llm.base.post.llp_meta import extract_meta as _extract_meta
from usekit.llm.base.init.lli_prompt import get_system_prompt
from usekit.llm.history import History, _db_fail
from usekit.llm.session import llm_session
import re as _re


# ── gateway guard (lazy) ───────────────────────────────────────
# Wraps a direct adapter call with the gateway safety net (health gate +
# in-flight lock + state record). Lazy import avoids a circular import
# (gateway._adapter_ua imports ua). If the gateway is unavailable for any
# reason, fall back to calling fn() directly (no worse than before).
def _meta_diag(where: str, meta_system: str) -> None:
    """[META-DIAG] Surface which project_meta.md the server actually read and
    whether it carried content.

    A "meta not injected" symptom (markers missing from the model's answer) is
    almost always a wrong BASE_PATH: the server reading a marker-less source/
    bundle project_meta.md (via get_usekit_path()'s `.usekit`->`usekit/` legacy
    fallback, or a cwd-derived base) instead of the project's `.usekit` active
    file. Logging the resolved path + system length turns a multi-hour code
    trace into a one-line check. (P1-3: expose silent failure on stderr, never
    raise.)
    """
    try:
        import sys
        from usekit.llm.base.init.lli_project_meta import get_project_meta_path
        p = get_project_meta_path()
        n = len(meta_system) if meta_system else 0
        warn = "  <-- EMPTY: check BASE_PATH / .usekit active file" if n == 0 else ""
        print(
            f"[META-DIAG] {where} read={p} exists={p.exists()} system_len={n}{warn}",
            file=sys.stderr,
        )
    except Exception:
        pass


def _guarded(provider, fn, *, timeout: int = 120):
    try:
        from usekit.classes.support.base.init.ai.sbi_ai_gateway import guarded_direct_call
        return guarded_direct_call(provider or "", fn, timeout=timeout)
    except Exception:
        try:
            raw = fn()
        except Exception as e:
            return {"ok": False, "raw": None, "error": str(e), "fatal": True}
        return {"ok": True, "raw": raw, "error": None}


# ── Auto quality detection ─────────────────────────────────────

# Quality → internal policy mapping
QUALITY_POLICY = {
    "fast":   {"max_workers": 0, "final_judge": False},
    "normal": {"max_workers": 2, "final_judge": False},
    "review": {"max_workers": 3, "final_judge": True},
}


def _auto_quality(prompt="", input_text="", workers=1, worker_prov=None):
    """
    Decide quality level from prompt + input characteristics.

    Returns: "fast" | "normal" | "review"

    Order matters:
        1. Review keywords first (even with workers=1)
        2. Large input → review
        3. No worker provider → fast
        4. Multi-task → normal
        5. Single task + input → normal (parallel intended)
        6. Medium input → normal
        7. Default → fast (BUT normal if parallel explicitly set)
    """
    p = (prompt or "").lower()
    input_lines = input_text.count("\n") + 1 if input_text else 0
    parallel_intended = bool(worker_prov) and workers > 1

    # [1] Review signals — check BEFORE worker count
    review_signals = [
        "설계", "design", "아키텍", "architect", "리팩", "refactor",
        "문서화", "document", "보고서", "report", "검토", "review",
        "리뷰", "전체 분석", "코드 리뷰",
    ]
    if any(s in p for s in review_signals):
        return "review"
    if input_lines > 80:
        return "review"

    # [2] No parallel capability → fast
    if not worker_prov or workers <= 1:
        return "fast"

    # [3] Multi-task signals → normal
    task_keywords = [
        "분석", "analyze", "버그", "bug", "수정", "fix",
        "문서", "doc", "요약", "summar", "검색", "search",
        "테스트", "test", "개선", "improve", "비교", "compare",
        "설명", "explain", "최적", "optim",
    ]
    task_count = sum(1 for k in task_keywords if k in p)

    multi_signals = [
        "그리고", "또한", "또", "비교", "각각", "동시에", "함께",
        "and", "also", "compare", "each", "추가로",
    ]

    if task_count >= 2 or any(s in p for s in multi_signals):
        return "normal"
    if input_lines > 30:
        return "normal"

    # [4] Single task + input_text → parallel can still help
    #     e.g. "분석해줘" + input_text=code → workers should analyze
    if parallel_intended and input_text and task_count >= 1:
        return "normal"

    # [5] Parallel explicitly intended → floor to normal
    #     User passed worker+workers>1, respect that intent
    if parallel_intended:
        return "normal"

    # [6] Default
    return "fast"


class AIHandler:
    """
    AI/LLM handler — symmetric with DBHandler (ud).

    Examples:
        ua.conn("qwen", base_url="https://qwen.ai.unturf.com/v1")
        ua.set(temperature=0.5, max_tokens=2000)

        text = ua.ask("Summarize this code")

        result = ua.run("Analyze this data")
        print(result["text"], result["elapsed"])

        # Smart chat — auto-routes single/parallel
        ua.chat("Find bugs and suggest fixes")

        # Parallel workers
        ua.set(worker="qwen", workers=3)
        ua.chat("Analyze codebase and draft docs")

        raw = ua.send("Complex task")
        out = ua.recv(raw)
    """

    def __init__(self):
        self._adapter = None
        self._provider_name = None
        self._config = LLMConfig()
        self._keys = KeyStore()
        self._session = {}
        self._history = History()
        self._meta_mode = "meta"  # "meta" | "plain"
        self._project_meta_on = False  # set by conn(project_meta=...); suppresses legacy guide
        # §4.8/4.9 Temporary session. When True, chat() tags turns with the
        # temporary lifecycle flags (1/0/0/'temporary') so they persist for audit
        # but are excluded from restore/summary (load_turns filters them out).
        # Set per request by serve_chat_v2 (Continue OFF -> temp_sid path).
        self._temp_mode = False

        # ua.emo — emotion journaler (write-time judge; EMO RAG slice 1).
        # Subhandler takes a back-ref to this ua instance (DI), so ua_emo never
        # imports ua_handler -> no import cycle. ue (pure codecs) stays untouched.
        from usekit.llm.handler.ua_emo import EmoAIHandler
        self.emo = EmoAIHandler(self)

    # ── temporary session (§4.8/4.9) ───────────────────────────

    def set_temp(self, on: bool) -> "AIHandler":
        """Toggle temporary-session tagging for subsequent chat() turns.

        on=True  -> turns saved as 1/0/0/'temporary' (audit-only, no restore/summary).
        on=False -> turns saved as the normal 0/1/1/'main' durable turns.
        Idempotent; serve_chat_v2 sets this each request based on Continue.
        """
        self._temp_mode = bool(on)
        return self

    def sync_project_meta(self, on: bool) -> None:
        """Re-sync project_meta state on a REUSED session (conn was skipped).

        conn() is the ONLY place that sets _project_meta_on, the legacy-guide
        suppression, and the system-slot meta injection (see conn [4b]).
        Continue-ON session reuse (serve_chat_v2 already/restore branch) skips
        conn(), so those three would stay frozen at the session's FIRST conn:
        toggling General USEKIT Project mid-session had no effect, and the
        legacy LLM.md/CLAUDE.md guide kept leaking (the SRS NOTE leak). Call
        this on reuse to re-apply the flag, the suppression, and — when ON —
        the system meta, so a reused session honors the current toggle.
        """
        self._project_meta_on = bool(on)
        try:
            from usekit.llm.parallel.llp_chat import suppress_guide
            suppress_guide(self._project_meta_on)
        except Exception:
            pass
        if self._project_meta_on:
            try:
                from usekit.llm.base.init.lli_project_meta import load_system_meta
                _meta_system = load_system_meta()
                _meta_diag("sync", _meta_system)  # [META-DIAG] expose read path + content
                if _meta_system:
                    self._config.set(system=_meta_system)
            except Exception:
                pass  # never let meta loading break a reused connection

    def _temp_meta(self, meta: dict) -> dict:
        """Attach lifecycle flags to a turn's meta based on _temp_mode.

        Flags ride in meta so History.add() forwards them to save_turn (S1).
        Normal mode leaves meta untouched (absent keys default 0/1/1/main).
        """
        if not self._temp_mode:
            return meta
        m = dict(meta or {})
        m["is_temporary"] = 1
        m["include_in_summary"] = 0
        m["include_in_context"] = 0
        m["context_group"] = "temporary"
        return m

    # ── connection ─────────────────────────────────────────────

    def conn(self, provider: str = "qwen", **kw) -> "AIHandler":
        """
        Connect to LLM provider.

        sys_ai.yaml provides defaults (base_url, model, api_key from env).
        Explicit kwargs override yaml values.

        ua.conn()                           # yaml default provider (qwen)
        ua.conn("qwen")                     # yaml base_url + model auto
        ua.conn("gemini")                   # yaml gemini defaults
        ua.conn("gemini", model="G25P")     # alias resolved via yaml
        ua.conn("openai", api_key="sk-x")   # override key
        """
        # close previous adapter — but NEVER delete persisted history here.
        # (reconnect must not wipe TSK_MESSAGE of the prior session)
        if self._adapter:
            self.close(clear_history=False)

        self._provider_name = provider.lower().strip()

        # ── [1] Load yaml defaults ─────────────────────────────
        yaml_cfg = get_provider_config(self._provider_name)

        # ── [2] Resolve adapter ────────────────────────────────
        self._adapter = resolve_provider(self._provider_name)

        # ── [3] Apply yaml defaults → then user overrides ──────
        # base_url
        if "base_url" not in kw and yaml_cfg.get("base_url"):
            self._config.set(base_url=yaml_cfg["base_url"])

        # model — resolve alias if needed
        if "model" in kw:
            # User passed model — try alias resolution
            try:
                from usekit.classes.support.base.init.ai.sbi_ai_meta import resolve_model
                resolved = resolve_model(kw["model"], self._provider_name)
                self._config.set(model=resolved)
            except Exception:
                self._config.set(model=kw["model"])
        elif yaml_cfg.get("model"):
            self._config.set(model=yaml_cfg["model"])

        # api_key — explicit > env > stored
        if "api_key" in kw:
            self._keys.set(kw["api_key"], self._provider_name)
        elif yaml_cfg.get("api_key"):
            self._keys.set(yaml_cfg["api_key"], self._provider_name)

        # base_url from explicit kw (overrides yaml)
        if "base_url" in kw:
            self._config.set(base_url=kw["base_url"])

        # ── [4] Set remaining kw params ────────────────────────
        # project_meta & slot are routing flags, not config fields — keep them out of _config.
        skip = {"model", "base_url", "api_key", "project_meta", "slot"}
        extra = {k: v for k, v in kw.items() if k not in skip}
        if extra:
            self._config.set(**extra)

        # ── [4b] Project base-meta → system slot (confirmed routing) ──
        # When enabled and the caller did NOT pass an explicit system prompt,
        # load ## Project/User/Meta from .usekit/sys/sys_yaml/project_meta.md
        # into _config["system"]. ## Request is NOT injected here (user layer).
        # Explicit system= always wins; missing/empty file is a no-op.
        # Also remember the flag: when project_meta is ON, the project identity
        # lives in the system prompt, so the legacy LLM.md/CLAUDE.md guide
        # injection is suppressed (avoids double-injecting a competing guide).
        self._project_meta_on = bool(kw.get("project_meta"))
        # Suppress the legacy LLM.md/CLAUDE.md guide process-wide when project_meta
        # is on, so parallel/recall paths (which call _load_guide directly) also
        # skip it — not just the fast path.
        try:
            from usekit.llm.parallel.llp_chat import suppress_guide
            suppress_guide(self._project_meta_on)
        except Exception:
            pass
        if kw.get("project_meta") and "system" not in kw:
            try:
                from usekit.llm.base.init.lli_project_meta import load_system_meta
                _meta_system = load_system_meta()
                _meta_diag("conn", _meta_system)  # [META-DIAG] expose read path + content
                if _meta_system:
                    self._config.set(system=_meta_system)
            except Exception:
                pass  # never let meta loading break a connection

        # ── [5] Connect adapter + session ──────────────────────
        cfg = self._build_config(kw)
        conn_info = self._adapter.connect(cfg)
        self._session = llm_session.make_session(
            self._provider_name, cfg.get("model", ""), cfg
        )
        llm_session.save(self._session)

        # ── [6] DB session + history binding ───────────────────
        import uuid
        sid = f"{self._provider_name}_{uuid.uuid4().hex[:8]}"
        # New session starts here. Drop the previous session's in-memory turns
        # so they don't leak into this fresh session via build(). DB rows of the
        # prior session are preserved (reset_memory does NOT delete) — P0-2.
        # Note: Continue ON reuses the live session when one already exists
        # (serve_chat_v2 already/restore branch skips conn). On the FIRST ON send
        # there is no live session yet, so serve_chat_v2's `elif continue_` branch
        # calls conn() here to mint the main session — that path relies on this.
        self._history.reset_memory()
        self._history.session_id = sid
        try:
            from usekit.llm.base.init.lli_db import create_session
            create_session(sid, self._provider_name, cfg.get("model", ""), cfg,
                           slot=kw.get("slot", ""))
        except Exception as _e:
            # DB unavailable -> stay memory-only for this session. Surfaced (P1-3).
            _db_fail("create_session", _e, sid=sid)

        return self

    def close(self, clear_history: bool = False):
        """Close current provider session.

        IMPORTANT: by default this does NOT delete persisted history.
        history.clear() runs a DELETE FROM TSK_MESSAGE — it must only happen on
        an explicit user request (clear_history=True), never as a side effect of
        reconnecting. conn() calls close(clear_history=False).
        """
        if self._adapter:
            self._adapter.close()
        self._adapter = None
        self._provider_name = None
        self._session = {}
        if clear_history:
            self._history.clear()

    # ── send / recv ────────────────────────────────────────────

    def send(self, prompt: str, **kw) -> dict:
        """Send prompt → raw provider response."""
        self._ensure_conn()
        cfg = self._build_config(kw)
        # fast/run path also goes through the guard (health + in-flight + state).
        res = _guarded(self._provider_name, lambda: _send(self._adapter, prompt, cfg))
        if not res.get("ok"):
            return {"text": "", "_gw_blocked": res.get("error") or "blocked",
                    "_gw": res}
        return res.get("raw") if res.get("raw") is not None else res

    def recv(self, raw: dict) -> dict:
        """Parse raw response → unified result dict."""
        return _recv(raw, provider=self._provider_name or "openai")

    # ── shortcuts ──────────────────────────────────────────────

    def ask(self, prompt: str, **kw) -> str:
        """
        Smart chat → text only.

        Routes through ua.chat() so parallel workers, quality modes,
        and recall all work. Returns just the text string.

        ua.ask("분석해줘")                    # auto quality
        ua.ask("분석해줘", worker="qwen", workers=3)  # parallel
        ua.ask("분석해줘", quality="review")  # force review
        ua.ask("u.wjb 예제", recirculate=True)  # recall
        ua.ask("분석해줘", verbose=True)      # print route debug

        For raw single LLM call without pipeline, use ua.run().
        """
        verbose = kw.pop("verbose", False)
        result = self.chat(prompt, **kw)
        if verbose:
            r = result.get("_route", {})
            print(f"[ua.ask] quality={result.get('quality')} "
                  f"mode={result.get('effective_mode')} "
                  f"workers={result.get('workers_requested',0)} "
                  f"elapsed={result.get('elapsed',0)}s "
                  f"route={r}")
        return result.get("text", "")

    def run(self, prompt: str, **kw) -> dict:
        """send + recv → full result dict."""
        raw = self.send(prompt, **kw)
        return self.recv(raw)

    # ── chat (feedback loop + parallel dispatch) ────────────────

    def chat(self, prompt: str, **kw) -> dict:
        """
        Feedback-loop chat with optional parallel dispatch.

        Modes:
            ua.chat("질문")                           # single (default)
            ua.chat("분석해줘", mode="parallel",
                    worker="qwen", workers=3)         # parallel workers
            ua.chat("복잡한 요청", mode="auto",
                    worker="qwen", workers=3)         # auto-detect

        Single mode:
            1. Add user prompt to history
            2. Build messages (compressed context from history)
            3. Inject system prompt (meta format)
            4. Send → recv → extract meta
            5. Add assistant response to history
            6. Return {text, meta, elapsed}

        Parallel mode:
            1. Add user prompt to history
            2. Plan subtasks (via connected provider)
            3. Dispatch workers (Qwen via ThreadPool)
            4. Assemble results → text
            5. Extract meta from assembled text
            6. Add assistant response to history
            7. Return {text, meta, elapsed, mode, workers_used}

        Options:
            feed="compress"|"full"|"auto"     # history compression
            meta=False                        # skip meta extraction
            mode="single"|"parallel"|"auto"   # dispatch mode
            worker="qwen"                     # worker provider name
            workers=3                         # max parallel workers
            on_status=callback                # stage progress callback
                callback(stage, msg, extra={})
                stages: "quality", "plan", "worker", "judge",
                        "assemble", "final_judge", "recall", "done"

        History:
            ua.history.table()      # summary table
            ua.history.clear()      # clear history
            ua.history.turns        # all turns
            ua.history.keywords     # collected keywords
        """
        self._ensure_conn()
        import time

        feed_mode = kw.pop("feed", "auto")
        # Visible path vs background path (the robust, mobile-first default):
        #   • Streaming → PLAIN text: fastest first token, and the system/persona
        #     prompt stays clean (no "append JSON" pollution — matters for SRSNote
        #     characters). The model writes pure prose.
        #   • Meta (i/kw/s) is derived AFTER the stream by _extract_meta's fallback
        #     — meta may lag the screen with zero UX cost.
        # Opt-in: force_meta=True keeps the inline [[META]] marker even while
        # streaming (only when the model's OWN structured output is essential,
        # e.g. an emotion self-report that can't be derived server-side).
        _streaming_now = kw.get("on_delta") is not None
        _force_meta = bool(kw.pop("force_meta", False))
        use_meta = (kw.pop("meta", True) and self._meta_mode == "meta"
                    and (not _streaming_now or _force_meta))
        mode = kw.pop("mode", None) or self._config.get("mode", "single")
        workers = kw.pop("workers", None) or self._config.get("workers", 1)
        worker_prov = kw.pop("worker", None) or self._config.get("worker")
        on_status = kw.pop("on_status", None)  # callback(stage, msg, extra)
        # Image attachments ride as generation config so they reach the adapter
        # via _build_config (self._config.merge). Default [] resets every turn —
        # without it a prior image would leak into a later text-only message.
        self._config.set(images=kw.pop("images", []))
        # Google Search grounding flag, also reset every turn from the request.
        self._config.set(search=kw.pop("search", False))
        # Streaming callback: when present, the adapter streams token chunks to it
        # in real-time. Reset to None every turn so a prior stream never leaks.
        self._config.set(on_delta=kw.pop("on_delta", None))
        quality = kw.get("quality", "auto")  # peek, don't pop
        workers_requested = workers  # save before cap

        def _emit(stage, msg, **extra):
            """Fire on_status callback if provided."""
            if on_status:
                try:
                    on_status(stage, msg, extra)
                except Exception:
                    pass

        t0 = time.time()

        # [0] Auto-quality: decide fast/normal/review from prompt + input
        if quality == "auto":
            quality = _auto_quality(
                prompt,
                input_text=kw.get("input_text", ""),
                workers=workers,
                worker_prov=worker_prov,
            )
            kw["quality"] = quality

        _emit("quality", f"quality={quality}", quality=quality)

        # [0.5] Apply quality policy — cap workers
        policy = QUALITY_POLICY.get(quality, QUALITY_POLICY["fast"])
        if policy["max_workers"] < workers:
            workers = policy["max_workers"]

        # [1] Add user to history
        user_meta = {"i": 5, "kw": [], "s": prompt[:50]}
        self._history.add("user", prompt, meta=self._temp_meta(user_meta))

        # [2] Route by quality + mode
        if mode == "auto":
            from usekit.llm.parallel.llp_chat import _detect_mode
            mode = _detect_mode(prompt, workers)

        # Debug trace — shows in ua.chat() return dict
        _route_info = {
            "quality": quality,
            "mode": mode,
            "workers": workers,
            "worker_prov": worker_prov or "",
            "has_input": bool(kw.get("input_text")),
        }

        if quality == "fast" or workers == 0:
            _emit("route", "fast mode", effective_mode="fast")
            result = self._chat_fast(prompt, feed_mode, use_meta, kw)
            effective_mode = "fast"
        elif mode == "parallel" and workers > 1 and worker_prov:
            _emit("route", f"parallel {quality}", effective_mode=f"parallel_{quality}", workers=workers)
            # Parallel workers would interleave token streams into nonsense, so
            # streaming is single/fast only — drop the callback here.
            self._config.set(on_delta=None)
            result = self._chat_parallel(prompt, worker_prov, workers, feed_mode, use_meta, kw, on_status=on_status)
            effective_mode = f"parallel_{quality}"
        else:
            _emit("route", "single mode", effective_mode="single")
            result = self._chat_single(prompt, feed_mode, use_meta, kw)
            effective_mode = "single"

        elapsed = round(time.time() - t0, 3)

        # [3] Add assistant to history
        meta = result.get("meta", {"i": 5, "kw": [], "s": ""})
        text = result.get("text", "")
        asst_seq = self._history.add("assistant", text, meta=self._temp_meta(meta))

        out = {
            "text": text,
            "reasoning": result.get("reasoning", ""),
            "meta": meta,
            "elapsed": elapsed,
            "mode": result.get("mode", "single"),
            "quality": quality,
            "effective_mode": effective_mode,
            "workers_requested": workers_requested,
            "_route": _route_info,  # debug — remove after stable
        }
        # parallel extras
        if "workers_used" in result:
            out["workers_used"] = result["workers_used"]
        if "worker_results" in result:
            out["worker_results"] = result["worker_results"]
        # telemetry extras (usage/finish from recv; single/fast paths only —
        # parallel would need per-worker usage summation, left for follow-up).
        if result.get("usage") is not None:
            out["usage"] = result["usage"]
        if result.get("finish") is not None:
            out["finish"] = result["finish"]
        # context telemetry: how history was fed this call (compress/full/auto)
        # + how many turns merged in. Answers "summary or full" per call.
        if result.get("ctx_mode") is not None:
            out["ctx_mode"] = result["ctx_mode"]
        if result.get("turns_merged") is not None:
            out["turns_merged"] = result["turns_merged"]
        # C2-fix: carry the real assembled model input up to serve_chat_v2 so the
        # Memory Editor card [Input] shows the final prompt, not the raw user text.
        if result.get("final_prompt") is not None:
            out["final_prompt"] = result["final_prompt"]
        # recirculation extras
        if "judge" in result:
            out["judge"] = result["judge"]
        if "recirculated" in result:
            out["recirculated"] = result["recirculated"]
        if "rounds" in result:
            out["rounds"] = result["rounds"]

        # C-0.5: link this assistant turn to its telemetry row. asst_seq ==
        # TSK_MESSAGE.seq; serve_chat_v2 forwards it as record_call(msg_seq=...),
        # which is how the Memory Editor card joins a turn to its TSK_CALL/log_ref.
        if asst_seq is not None:
            out["assistant_seq"] = asst_seq

        _emit("done", f"완료 ({elapsed}s)", elapsed=elapsed, quality=quality)
        return out

    def _chat_single(self, prompt, feed_mode, use_meta, kw) -> dict:
        """Single-provider feedback loop path."""
        # Build messages from history
        messages = self._history.build(feed_mode)

        # Inject system prompt
        base_system = self._config.get("system", "")
        sys_prompt = get_system_prompt(base_system, "meta" if use_meta else "plain")

        # Send with messages
        cfg = self._build_config(kw)
        raw = self._send_messages(messages, sys_prompt, cfg)

        # Recv + meta extract
        result = self.recv(raw)
        if use_meta:
            result = _extract_meta(result)

        # C2-fix: flatten the exact sent messages into a readable final prompt
        # ([ROLE]\n content blocks), so the card [Input] shows the real model input.
        _fm = getattr(self, "_last_sent_msgs", None) or []
        final_prompt = "\n\n".join(
            "[" + str(m.get("role", "user")).upper() + "]\n" + str(m.get("content", ""))
            for m in _fm
        )

        return {
            "text": result.get("text", ""),
            "reasoning": result.get("reasoning", ""),
            "meta": result.get("meta", {"i": 5, "kw": [], "s": ""}),
            "usage": result.get("usage"),    # {prompt,completion,total} from recv
            "finish": result.get("finish"),  # stop|length|... (telemetry)
            "ctx_mode": feed_mode,           # compress|full|auto — what was fed
            "turns_merged": sum(1 for m in messages if m.get("role") != "system"),
            "final_prompt": final_prompt,    # C2-fix: real assembled model input
            "mode": "single",
        }

    def _chat_fast(self, prompt, feed_mode, use_meta, kw) -> dict:
        """
        Fast mode — single LLM call, but WITH conversation history.

        LLM 1 call total. No workers, no judge, no final editor.
        Target: 1-3 seconds.

        History note: chat() already did _history.add("user", prompt) before
        routing here, so the build() output ends with the current user turn.
        Earlier this path called run(prompt) directly, which sent ONLY the bare
        prompt (plus the project guide) and dropped all prior turns — so even
        with Continue ON the model saw no context ("이름을 알지 못합니다", and the
        guide text leaked in as the apparent "memory"). We now build messages
        from history like _chat_single, and fold the fast-mode extras (project
        guide + input_text) into the latest user message only.
        """
        input_text = kw.pop("input_text", "")
        kw.pop("input_paths", None)
        kw.pop("quality", None)
        kw.pop("recirculate", None)
        kw.pop("max_rounds", None)

        # Build messages from history (includes the current user turn).
        messages = self._history.build(feed_mode)

        # Fast-mode extras attach to the CURRENT user turn only, so prior
        # context stays clean and the guide/input don't repeat every turn.
        extras = []
        guide = ""
        # When General USEKIT Project (project_meta) is ON, the project identity
        # is already in the system prompt — skip the legacy LLM.md/CLAUDE.md
        # guide so it doesn't compete (this was the SRS NOTE leak source).
        # Instead, attach the ## Request section (user layer, per confirmed
        # routing design §4.6: Request is volatile → user prompt front, NOT system).
        if getattr(self, "_project_meta_on", False):
            try:
                from usekit.llm.base.init.lli_project_meta import load_request_meta
                _req = load_request_meta()
                if _req:
                    extras.append(f"[REQUEST]\n{_req}\n")
            except Exception:
                pass
        else:
            try:
                from usekit.llm.parallel.llp_chat import _load_guide
                guide = _load_guide()
            except Exception:
                pass
        if guide:
            extras.append(f"[PROJECT GUIDE]\n{guide[:1000]}\n")
        if input_text:
            extras.append(f"\nINPUT:\n```\n{input_text.strip()}\n```")

        if extras and messages:
            # Find the last user message and augment it in place.
            for i in range(len(messages) - 1, -1, -1):
                if messages[i].get("role") == "user":
                    base = messages[i].get("content", "")
                    messages[i] = {
                        **messages[i],
                        "content": "\n".join(extras + [base]),
                    }
                    break
        elif extras:
            # No history at all → fall back to a single user message.
            messages = [{"role": "user", "content": "\n".join(extras + [prompt])}]

        # System prompt (same path as _chat_single).
        base_system = self._config.get("system", "")
        sys_prompt = get_system_prompt(base_system, "meta" if use_meta else "plain")

        cfg = self._build_config(kw)
        raw = self._send_messages(messages, sys_prompt, cfg)
        result = self.recv(raw)
        if use_meta:
            result = _extract_meta(result)

        return {
            "text": result.get("text", ""),
            "reasoning": result.get("reasoning", ""),
            "meta": result.get("meta", {"i": 5, "kw": [], "s": result.get("text", "")[:50]}),
            "usage": result.get("usage"),    # {prompt,completion,total} from recv
            "finish": result.get("finish"),  # stop|length|... (telemetry)
            "ctx_mode": feed_mode,           # compress|full|auto — what was fed
            "turns_merged": sum(1 for m in messages if m.get("role") != "system"),
            "final_prompt": "\n\n".join(   # C2-fix: real assembled model input (fast path)
                "[" + str(m.get("role", "user")).upper() + "]\n" + str(m.get("content", ""))
                for m in (getattr(self, "_last_sent_msgs", None) or [])
            ),
            "mode": "fast",
            "workers_used": 0,
            "quality": "fast",
        }

    def _chat_parallel(self, prompt, worker_prov, workers, feed_mode, use_meta, kw, on_status=None) -> dict:
        """
        Parallel dispatch path — workers process subtasks, results join history.

        Flow:
            plan → dispatch workers → assemble → meta extract
        """
        from usekit.llm.parallel.llp_chat import dispatch_parallel

        # Build context summary from history for workers
        context = self._history.build("compress")
        context_text = "\n".join(
            f"[{m['role']}] {m['content']}" for m in context
        ) if context else ""

        # Dispatch
        result = dispatch_parallel(
            handler=self,
            prompt=prompt,
            worker_prov=worker_prov,
            max_workers=workers,
            context=context_text,
            on_status=on_status,
            **kw,
        )

        text = result.get("text", "")

        # Meta extract from assembled text
        if use_meta:
            meta_result = _extract_meta({"text": text})
            meta = meta_result.get("meta", {"i": 5, "kw": [], "s": ""})
        else:
            meta = {"i": 5, "kw": [], "s": text[:50]}

        return {
            "text": text,
            "meta": meta,
            "mode": result.get("mode", "parallel"),
            "workers_used": result.get("workers_used", 0),
            "worker_results": result.get("results", []),
            "judge": result.get("judge"),
            "recirculated": result.get("recirculated", False),
            "rounds": result.get("rounds", 1),
        }

    @property
    def history(self):
        """
        History accessor. Returns the History object directly.

        ua.history              → History object
        ua.history.table()      → summary table
        ua.history.turns        → all turns
        ua.history.keywords     → collected keywords
        ua.history.count        → turn count
        ua.history.clear()      → clear history
        """
        return self._history

    # ── config ─────────────────────────────────────────────────

    def set(self, **kw):
        """
        Set generation params.

        ua.set(temperature=0.5, max_tokens=2000)
        ua.set(model="Qwen3-Coder-30B")
        """
        self._config.set(**kw)
        return self

    def get(self, key: str, default=None):
        """Get config value."""
        return self._config.get(key, default)

    # ── key ────────────────────────────────────────────────────

    def key(self, api_key: str = None, provider: str = None):
        """
        Set or get API key.

        ua.key("sk-xxx")          # set
        ua.key()                  # get masked
        """
        prov = provider or self._provider_name or "_default"
        if api_key is not None:
            self._keys.set(api_key, prov)
            return self
        return self._keys.masked(prov)

    # ── status ─────────────────────────────────────────────────

    def ping(self) -> dict:
        """Health check → {ok, elapsed}."""
        self._ensure_conn()
        cfg = self._build_config()
        result = self._adapter.ping(cfg)
        # update session
        import time
        self._session["last_ping_time"] = time.time()
        self._session["last_ping_elapsed"] = result.get("elapsed", 0)
        self._session["warm_state"] = result.get("ok", False)
        llm_session.save(self._session)
        return result

    def warm(self) -> dict:
        """Ensure model is warm. Returns state info."""
        if self._session and is_warm(self._session):
            return {
                "warm": True,
                "elapsed": self._session.get("last_ping_elapsed", 0),
                "state": classify_state(self._session.get("last_ping_elapsed", 99)),
            }
        result = self.ping()
        state = classify_state(result.get("elapsed", 99))
        return {
            "warm": result.get("ok", False),
            "elapsed": result.get("elapsed", 0),
            "state": state,
        }

    def info(self) -> dict:
        """Current session info."""
        return {
            "provider": self._provider_name,
            "model": self._config.get("model", ""),
            "connected": self._adapter is not None,
            "config": self._config.to_dict(),
            "key": self._keys.masked(self._provider_name or "_default"),
            "session": self._session,
        }

    # ── internal ───────────────────────────────────────────────

    def _ensure_conn(self):
        if not self._adapter:
            raise RuntimeError("[ua] no provider connected. call ua.conn() first.")

    def _send_messages(self, messages: list, system: str, config: dict) -> dict:
        """
        Send messages array (multi-turn) to provider.

        Injects system prompt and calls adapter with full messages.
        Falls back to single-prompt send for adapters that don't support messages.
        """
        # Build full messages with system
        full_msgs = []
        if system:
            full_msgs.append({"role": "system", "content": system})
        full_msgs.extend(messages)
        # C2-fix: stash the exact assembled input (system + history + user) so the
        # caller can surface what the model REALLY received (349-token reality),
        # not the raw user text. This is the RAG-debugger "final input".
        self._last_sent_msgs = full_msgs

        # Try messages-aware send if adapter supports it.
        # Wrap the direct adapter call with the gateway guard (health gate +
        # in-flight lock + state record) WITHOUT routing into dispatch_one
        # (which would recurse via _adapter_ua → ua.run). The guard preserves
        # the provider-raw return in res["raw"] so recv() keeps its contract.
        if hasattr(self._adapter, "send_messages"):
            res = _guarded(self._provider_name,
                           lambda: self._adapter.send_messages(full_msgs, config))
            if not res.get("ok"):
                # health/busy/fatal — return an empty raw so recv() yields empty
                # text and the pipeline treats it as a (non-retried) failure.
                return {"text": "", "_gw_blocked": res.get("error") or "blocked",
                        "_gw": res}
            return res.get("raw") if res.get("raw") is not None else res

        # Fallback: flatten to single prompt for basic adapters
        # Concat all messages into one prompt string
        parts = []
        for m in full_msgs:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"[SYSTEM]\n{content}")
            elif role == "user":
                parts.append(f"[USER]\n{content}")
            elif role == "assistant":
                parts.append(f"[ASSISTANT]\n{content}")
        flat_prompt = "\n\n".join(parts)
        res = _guarded(self._provider_name,
                       lambda: self._adapter.send(flat_prompt, config))
        if not res.get("ok"):
            return {"text": "", "_gw_blocked": res.get("error") or "blocked",
                    "_gw": res}
        return res.get("raw") if res.get("raw") is not None else res

    def _build_config(self, overrides: dict = None) -> dict:
        """Merge config + key + defaults."""
        cfg = self._config.merge(overrides)

        # inject stored api_key if not in overrides
        prov = self._provider_name or "_default"
        if "api_key" not in cfg or not cfg["api_key"]:
            stored_key = self._keys.get(prov)
            if stored_key:
                cfg["api_key"] = stored_key

        # inject default base_url
        if "base_url" not in cfg or not cfg["base_url"]:
            default_url = get_default_url(prov)
            if default_url:
                cfg["base_url"] = default_url

        return cfg

    def __repr__(self):
        if self._adapter:
            model = self._config.get("model", "?")
            return f"<ua [{self._provider_name}] model={model}>"
        return "<ua [disconnected]>"


# ── Singleton ──────────────────────────────────────────────────

ua = AIHandler()

__all__ = ["AIHandler", "ua"]
