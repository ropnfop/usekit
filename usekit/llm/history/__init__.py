# Path: usekit.llm.history.__init__.py
# -----------------------------------------------------------------------
#  Conversation history with meta-driven compression.
#
#  Each turn: {role, meta, text, _full}
#    - meta.s  = summary (always kept)
#    - _full   = original text (evictable)
#
#  Re-feed modes:
#    compress → summaries only
#    full     → recent N full + rest summaries
#    auto     → importance-based selection
# -----------------------------------------------------------------------

from __future__ import annotations
from typing import Any, Dict, List, Optional
import os
import sys


# ── P1-3: surface otherwise-silent DB failures ───────────────────────────
# Previously every DB op (save_turn/load_turns/create_session/...) swallowed
# its exception unless USEKIT_DB_DEBUG=1. That hid memory↔DB divergence
# (e.g. turn_count drift, "묘하게 사라진" 대화). We now (1) emit a one-line
# stderr warning by default, (2) keep a process-wide counter for post-hoc
# inspection, and (3) still print a full traceback when USEKIT_DB_DEBUG=1.
# Set USEKIT_DB_SILENT=1 to suppress the default one-liner (counter still ticks).
_DB_FAIL_COUNTS: Dict[str, int] = {}


def db_fail_counts() -> Dict[str, int]:
    """Return a copy of the per-operation DB failure counter (P1-3)."""
    return dict(_DB_FAIL_COUNTS)


def _db_fail(op: str, err: Exception, **ctx):
    """Record + surface a DB-layer failure that would otherwise be silent."""
    _DB_FAIL_COUNTS[op] = _DB_FAIL_COUNTS.get(op, 0) + 1
    debug = os.getenv("USEKIT_DB_DEBUG") == "1"
    silent = os.getenv("USEKIT_DB_SILENT") == "1"
    if not silent:
        ctx_s = " ".join(f"{k}={v}" for k, v in ctx.items())
        n = _DB_FAIL_COUNTS[op]
        print(f"[usekit.db FAIL] {op} (#{n}) {ctx_s} err={err!r}", file=sys.stderr)
    if debug:
        import traceback
        traceback.print_exc()


class History:
    """
    Conversation history with compressed re-feed.

    Usage:
        h = History(max_turns=20, keep_full=5)
        h.add("user", "분석해줘", meta={...})
        h.add("assistant", "결과...", meta={"i":7, "kw":["버그"], "s":"3건 발견"})

        messages = h.build()            # default: auto
        messages = h.build("compress")  # summaries only
        messages = h.build("full")      # recent N full + rest summary
    """

    def __init__(
        self,
        max_turns: int = 30,
        keep_full: int = 6,
        system: str = "",
        session_id: str = "",
    ):
        self._turns: List[Dict[str, Any]] = []
        self.max_turns = max_turns
        self.keep_full = keep_full
        self.system = system
        self.session_id = session_id

    # ── add / clear ───────────────────────────────────────────

    def add(self, role: str, text: str, meta: dict = None):
        """
        Add a turn to history.

        Args:
            role: "user" | "assistant" | "system"
            text: full response text
            meta: {i, kw, s} from LLM or fallback
        """
        meta = meta or {"i": 5, "kw": [], "s": text[:50]}
        idx = len(self._turns)
        turn = {
            "role": role,
            "meta": dict(meta),
            "text": text,  # summary용
            "_full": text,  # 원문 보존
        }
        self._turns.append(turn)

        # persist to DB
        if self.session_id:
            try:
                from usekit.llm.base.init.lli_db import save_turn
                # §4.8/4.9: lifecycle flags ride in meta (set by the temp-session
                # path in S3). Absent => normal durable turn (0/1/1/main).
                save_turn(
                    self.session_id, idx, role, text, meta,
                    is_temporary=int(meta.get("is_temporary", 0)),
                    include_in_summary=int(meta.get("include_in_summary", 1)),
                    include_in_context=int(meta.get("include_in_context", 1)),
                    context_group=meta.get("context_group", "main"),
                )
            except Exception as _e:
                # DB write failed -> memory-only for this turn. Surfaced (P1-3).
                _db_fail("save_turn", _e, sid=self.session_id, idx=idx)

        # evict old _full beyond keep_full window
        self._evict()

        # C-0.5: expose the saved turn seq so callers (ua.chat) can join this
        # turn to its TSK_CALL telemetry row via record_call(msg_seq=...).
        # idx == TSK_MESSAGE.seq (save_turn is idempotent on (session_id, seq)).
        return idx

    def clear(self):
        """Clear all history (memory + DB)."""
        self._turns.clear()
        if self.session_id:
            try:
                from usekit.llm.base.init.lli_db import clear_session
                clear_session(self.session_id)
            except Exception as _e:
                _db_fail("clear_session", _e, sid=self.session_id)

    def reset_memory(self):
        """Clear in-memory turns ONLY — never touches the DB.

        Used when starting a brand-new session (conn() mints a new session_id).
        Unlike clear(), this does NOT run DELETE FROM TSK_MESSAGE, so the prior
        session's persisted rows are preserved (P0-2 invariant). Without this,
        a New session inherits the previous session's _turns in memory and
        build() would leak old context into the fresh session — i.e. Continue
        OFF would still "remember" the prior conversation.
        """
        self._turns.clear()

    def load(self, session_id: str = None):
        """
        Load turns from DB into memory.

        ua.history.load()              # load current session
        ua.history.load("session_id")  # load specific session
        """
        sid = session_id or self.session_id
        if not sid:
            return self
        try:
            from usekit.llm.base.init.lli_db import load_turns
            rows = load_turns(sid)
            self._turns.clear()
            for r in rows:
                meta = {"i": r.get("i", 5), "kw": r.get("kw", []), "s": r.get("s", "")}
                text = r.get("text", "")
                self._turns.append({
                    "role": r.get("role", "user"),
                    "meta": meta,
                    "text": text,
                    "_full": text,
                })
            if session_id:
                self.session_id = session_id
            # Apply eviction to loaded turns
            self._evict()
        except Exception as _e:
            # Restore failed — context will be missing. Surfaced (P1-3).
            _db_fail("load_turns", _e, sid=sid)
        return self

    def search(self, keyword: str, limit: int = 20) -> list:
        """
        Search across all sessions by keyword.

        ua.history.search("버그")
        """
        try:
            from usekit.llm.base.init.lli_db import search_turns
            return search_turns(keyword, limit)
        except Exception:
            return []

    def sessions(self, limit: int = 20) -> list:
        """
        List recent sessions.

        ua.history.sessions()
        """
        try:
            from usekit.llm.base.init.lli_db import list_sessions
            return list_sessions(limit)
        except Exception:
            return []

    def db_path(self) -> str:
        """Return DB file path."""
        try:
            from usekit.llm.base.init.lli_db import db_path
            return db_path()
        except Exception:
            return ""

    # ── build messages for re-feed ────────────────────────────

    def build(self, mode: str = "auto") -> List[Dict[str, str]]:
        """
        Build messages array for LLM API call.

        Modes:
            compress → all turns as summary
            full     → recent keep_full as full text, rest as summary
            auto     → importance >= 6 get full, rest summary,
                        plus always keep last keep_full full

        Returns:
            [{role, content}, ...] ready for messages param
        """
        if not self._turns:
            return self._with_system([])

        if mode == "compress":
            return self._with_system(self._build_compress())
        elif mode == "full":
            return self._with_system(self._build_full())
        else:  # auto
            return self._with_system(self._build_auto())

    def _compact(self, data) -> str:
        """Compact serialize — zero whitespace, minimal tokens."""
        try:
            from usekit import u
            return u.ejm(data, compact=True)
        except Exception:
            import json
            return json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    def _summary_text(self, t: dict) -> str:
        """Build compact summary string for a turn, tagged to prevent format mimicry."""
        meta = t["meta"]
        s = meta.get("s", "") or t.get("text", "")[:50]
        kw = meta.get("kw", [])
        if kw:
            return f"[CTX] {s} ({','.join(kw[:3])})"
        return f"[CTX] {s}"

    def _build_compress(self) -> List[Dict[str, str]]:
        """All turns as compact summary."""
        msgs = []
        for t in self._turns:
            msgs.append({"role": t["role"], "content": self._summary_text(t)})
        return msgs

    def _build_full(self) -> List[Dict[str, str]]:
        """Recent keep_full as full, rest as compact summary."""
        msgs = []
        n = len(self._turns)
        cut = max(0, n - self.keep_full)

        for i, t in enumerate(self._turns):
            if i >= cut:
                content = t.get("_full") or t["text"]
            else:
                content = self._summary_text(t)
            msgs.append({"role": t["role"], "content": content})
        return msgs

    def _build_auto(self) -> List[Dict[str, str]]:
        """Importance-based: high importance + recent get full, rest compact."""
        msgs = []
        n = len(self._turns)
        cut = max(0, n - self.keep_full)

        for i, t in enumerate(self._turns):
            importance = t["meta"].get("i", 5)
            is_recent = (i >= cut)
            is_important = (importance >= 6)
            has_full = (t.get("_full") is not None)

            if (is_recent or is_important) and has_full:
                content = t["_full"]
            else:
                content = self._summary_text(t)
            msgs.append({"role": t["role"], "content": content})
        return msgs

    def _with_system(self, msgs: list) -> list:
        """Prepend system message if set."""
        if self.system:
            return [{"role": "system", "content": self.system}] + msgs
        return msgs

    # ── eviction ──────────────────────────────────────────────

    def _evict(self):
        """Evict oldest _full texts beyond keep_full window."""
        n = len(self._turns)
        if n <= self.max_turns:
            # Just evict _full from old turns
            cut = max(0, n - self.keep_full)
            for i in range(cut):
                self._turns[i].pop("_full", None)
            return

        # Over max_turns: drop oldest turns entirely
        overflow = n - self.max_turns
        self._turns = self._turns[overflow:]
        # Then evict _full from old
        cut = max(0, len(self._turns) - self.keep_full)
        for i in range(cut):
            self._turns[i].pop("_full", None)

    # ── accessors ─────────────────────────────────────────────

    @property
    def turns(self) -> List[Dict]:
        """All turns (read-only view)."""
        return list(self._turns)

    @property
    def count(self) -> int:
        return len(self._turns)

    def debug(self, mode: str = "auto") -> List[Dict[str, str]]:
        """Show what build() would send to LLM. For debugging."""
        return self.build(mode)

    @property
    def keywords(self) -> List[str]:
        """All keywords from all turns, ordered by recency."""
        kws = []
        for t in reversed(self._turns):
            for kw in t["meta"].get("kw", []):
                if kw not in kws:
                    kws.append(kw)
        return kws

    def summary_table(self) -> List[Dict]:
        """Compact view for inspection."""
        rows = []
        for i, t in enumerate(self._turns):
            rows.append({
                "idx": i,
                "role": t["role"],
                "i": t["meta"].get("i", 5),
                "kw": t["meta"].get("kw", []),
                "s": t["meta"].get("s", ""),
                "has_full": t.get("_full") is not None,
            })
        return rows

    def table(self) -> List[Dict]:
        """Alias for summary_table()."""
        return self.summary_table()

    def __repr__(self):
        return f"<History turns={len(self._turns)} keep={self.keep_full}>"

    def __len__(self):
        return len(self._turns)


__all__ = ["History"]
