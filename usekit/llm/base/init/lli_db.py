# Path: usekit.llm.base.init.lli_db.py
# -----------------------------------------------------------------------
#  LLM system DB — unified usekit.db (TSK_SESSION / TSK_MESSAGE).
#
#  This module is the write/read path for "live" chat sessions. It no
#  longer owns its own schema: the tables are created by `uk setup`
#  (seeds 01_TSK .. 05_TSK_CALL) in the unified .usekit/sys/sys_db/usekit.db.
#  We only INSERT/SELECT here — never CREATE — so the seed schema and the
#  3-tier meta tables are the single source of truth.
#
#  8-function contract (callers ua_handler / History stay unchanged):
#    create_session / get_session / list_sessions
#    save_turn / save_turns / load_turns / search_turns / clear_session
#    db_path / close
#
#  Return-key contract: load_turns/search_turns yield dicts with the keys
#  the History layer reads — i / kw / s / text / role — mapped from the
#  TSK_MESSAGE columns importance / keywords / summary / content / role.
#
#  Mapping (live chat):
#    session  -> TSK_SESSION (kind='live', mode='chat', provider/model/meta)
#    turn     -> TSK_MESSAGE (seq=idx, importance=meta.i, keywords=meta.kw,
#                             summary=meta.s, content / content_path spillover)
#
#  Security: config is stored as meta with the api_key body stripped
#  (api_key -> api_key_ref). The key body is NEVER written to the DB.
#
#  Uses sqlite3 directly (no ud dependency to avoid circular imports).
# -----------------------------------------------------------------------

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# -- tuning constants --
_SPILL_THRESHOLD = 4096          # content longer than this spills to a file
_DEFAULT_IMPORTANCE = 5          # legacy History default (meta.i)
_TITLE_MAXLEN = 40              # H1: non-LLM title fallback length (first user msg)

# provider -> env var name for api_key_ref substitution (mirrors SYS_META)
_API_KEY_REF = {
    "groq": "GROQ_API_KEY",
    "groq_api": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


# -- DB path resolution --

def _db_path() -> Path:
    """Resolve the unified DB: USEKIT_PATH/sys/sys_db/usekit.db.

    Prefers the loader_env resolver (single source of truth, follows a
    user-relocated .usekit). Falls back to env vars only if that import
    is unavailable, so the module still works in a bare context.
    """
    try:
        from usekit.classes.core.env.loader_env import get_sys_db_path
        p = get_sys_db_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        pass

    base = os.getenv("ENV_BASE_PATH") or os.getenv("USEKIT_BASE") or os.getenv("BASE_PATH")
    if base:
        p = Path(base) / ".usekit" / "sys" / "sys_db"
        p.mkdir(parents=True, exist_ok=True)
        return p / "usekit.db"

    # Last resort (dev/no-env): relative .usekit
    p = Path(".usekit/sys/sys_db")
    p.mkdir(parents=True, exist_ok=True)
    return p / "usekit.db"


def _spill_dir() -> Path:
    d = _db_path().parent / "spill"
    d.mkdir(parents=True, exist_ok=True)
    return d


# -- Connection --

_conn_cache: Optional[sqlite3.Connection] = None


def _get_conn() -> sqlite3.Connection:
    """Get or create the sqlite connection (cached). Never creates tables."""
    global _conn_cache
    if _conn_cache is not None:
        try:
            _conn_cache.execute("SELECT 1")
            return _conn_cache
        except Exception:
            _conn_cache = None

    db = _db_path()
    _conn_cache = sqlite3.connect(str(db), check_same_thread=False)
    _conn_cache.row_factory = sqlite3.Row
    _conn_cache.execute("PRAGMA journal_mode=WAL")
    return _conn_cache


# -- helpers --

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#  Request-payload keys that must NEVER persist into TSK_SESSION.meta. The
#  chief offender is `images`: a single screenshot is a ~770 KB base64 data: URI,
#  and the old blacklist (api_key only) let it copy straight into meta on every
#  image turn — bloating usekit.db to ~29 MB from ~1k tiny rows. These are all
#  per-request scaffolding with no place in durable session config.
#  (DB = state/index; bodies live in files — TSK_MESSAGE spill / ai_calls.)
_META_DROP_KEYS = {
    "images", "image", "attachments", "files", "parts",
    "contents", "messages", "history", "_state",
}
#  Defensive backstop: any value still serializing larger than this is dropped,
#  so a future large/base64 field can't leak in under a new key name. Real
#  session knobs (temperature, max_tokens, model, base_url, api_key_ref) are tiny.
_META_MAX_VALUE_BYTES = 2048


def _strip_config(config: Optional[dict], provider: str) -> dict:
    """Build durable session meta from a request config.

    Single sanitizer chokepoint for TSK_SESSION.meta:
      1. never persists an api_key body (keeps only api_key_ref),
      2. drops known request-payload keys (images/attachments/_state/...),
      3. defensively drops any oversized value (base64 blobs, etc.).
    Keeps the row small so an image turn can't bloat the session table.
    """
    cfg = dict(config or {})

    # 1) api_key body never persists.
    if "api_key" in cfg:
        cfg.pop("api_key", None)
        ref = _API_KEY_REF.get((provider or "").lower())
        if ref:
            cfg.setdefault("api_key_ref", ref)

    # 2) Drop known transient / payload keys (chiefly base64 images).
    for k in _META_DROP_KEYS:
        cfg.pop(k, None)

    # 3) Size backstop — drop anything still oversized or unserializable.
    out = {}
    for k, v in cfg.items():
        if v is None:
            out[k] = v
            continue
        try:
            if len(json.dumps(v, ensure_ascii=False)) > _META_MAX_VALUE_BYTES:
                continue
        except (TypeError, ValueError):
            continue
        out[k] = v
    return out


def _msg_id(session_id: str, seq: int) -> str:
    """Deterministic msg_id so re-saving a seq is idempotent."""
    return f"{session_id}_{seq:06d}"


def _store_content(session_id: str, seq: int, text: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (content, content_path). Long text spills to a file."""
    text = text or ""
    if len(text) <= _SPILL_THRESHOLD:
        return text, None
    fp = _spill_dir() / f"{_msg_id(session_id, seq)}.txt"
    try:
        fp.write_text(text, encoding="utf-8")
        return None, str(fp)
    except Exception:
        # If the file write fails, keep the text inline rather than lose it.
        return text, None


def _read_content(row: sqlite3.Row) -> str:
    """Reassemble full text from content or content_path."""
    content = row["content"]
    if content is not None:
        return content
    cp = row["content_path"]
    if cp:
        try:
            return Path(cp).read_text(encoding="utf-8")
        except Exception:
            return ""
    return ""


def _row_to_turn(row: sqlite3.Row) -> dict:
    """Map a TSK_MESSAGE row to the History return-key contract (i/kw/s/text/role)."""
    try:
        kw = json.loads(row["keywords"]) if row["keywords"] else []
    except (json.JSONDecodeError, TypeError):
        kw = []
    return {
        "role": row["role"],
        "i": row["importance"] if row["importance"] is not None else _DEFAULT_IMPORTANCE,
        "kw": kw,
        "s": row["summary"] or "",
        "text": _read_content(row),
    }


# -- Session CRUD --

def create_session(session_id: str, provider: str, model: str = "", config: dict = None,
                   slot: str = "") -> dict:
    """Insert/replace a live chat session into TSK_SESSION (kind='live', mode='chat').

    `slot` records the owning editor slot name (single source of truth for the
    Memory Editor's LINKED/ORPHAN split). On conflict we only overwrite slot when
    a non-empty value is provided, so a later slot-less reattach can't wipe it.
    """
    conn = _get_conn()
    meta = _strip_config(config, provider)
    now = _now()
    conn.execute(
        "INSERT INTO TSK_SESSION "
        "  (session_id, mode, status, started_at, last_active_at, meta, "
        "   provider, model, kind, slot, turn_count, created_at, updated_at) "
        "VALUES (?, 'chat', 'active', ?, ?, ?, ?, ?, 'live', ?, 0, ?, ?) "
        "ON CONFLICT(session_id) DO UPDATE SET "
        "  provider=excluded.provider, model=excluded.model, "
        "  meta=excluded.meta, last_active_at=excluded.last_active_at, "
        "  slot=COALESCE(NULLIF(excluded.slot, ''), TSK_SESSION.slot), "
        "  updated_at=excluded.updated_at",
        (session_id, now, now, json.dumps(meta, ensure_ascii=False),
         provider, model, slot or "", now, now),
    )
    conn.commit()
    return {"session_id": session_id, "provider": provider, "model": model}


def record_call(
    session_id: str = "",
    provider: str = "",
    model: str = "",
    *,
    ok: int = 1,
    finish: str = "stop",
    kind: str = "live",
    msg_seq: Optional[int] = None,
    elapsed_ms: Optional[int] = None,
    ctx_mode: Optional[str] = None,
    turns_merged: Optional[int] = None,
    refeed: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    total_tokens: Optional[int] = None,
    error_type: Optional[str] = None,
    error_summary: Optional[str] = None,
    log_ref: Optional[str] = None,
    telemetry_level: Optional[str] = None,
    call_id: Optional[str] = None,
) -> str:
    """Insert one TSK_CALL telemetry row (one row per AI call; failures kept too).

    Minimal-by-design: callers fill what they have; the rest stays NULL.
    ctx_mode (compress|full|auto) + turns_merged answer "did the model see
    summaries or full turns this call". Token counts are NULL until ua.chat()
    surfaces a usage block. An empty session_id is stored as NULL ("one-off").
    Returns the call_id.
    """
    import uuid
    call_id = call_id or f"call_{uuid.uuid4().hex[:12]}"
    conn = _get_conn()
    conn.execute(
        "INSERT INTO TSK_CALL "
        "  (call_id, session_id, msg_seq, provider, model, kind, "
        "   ctx_mode, turns_merged, refeed, "
        "   prompt_tokens, completion_tokens, total_tokens, elapsed_ms, "
        "   finish, ok, error_type, error_summary, log_ref, telemetry_level, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (call_id, session_id or None, msg_seq, provider or None, model or None, kind,
         ctx_mode, turns_merged, refeed,
         prompt_tokens, completion_tokens, total_tokens, elapsed_ms,
         finish, int(ok), error_type, error_summary, log_ref, telemetry_level, _now()),
    )
    conn.commit()
    return call_id


def get_session(session_id: str) -> Optional[dict]:
    """Load a session by ID (raw TSK_SESSION row as dict)."""
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM TSK_SESSION WHERE session_id = ?", (session_id,)
    ).fetchone()
    return dict(row) if row else None


def list_sessions(limit: int = 20) -> List[dict]:
    """Recent live sessions (most recently active first)."""
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM TSK_SESSION WHERE kind = 'live' "
        "ORDER BY COALESCE(last_active_at, started_at) DESC LIMIT ?",
        (limit,),
    ).fetchall()
    return [dict(r) for r in rows]


# -- History CRUD --

def _backfill_title(conn: sqlite3.Connection, session_id: str, first_user_text: str):
    """H1: set TSK_SESSION.title from the first user message (non-LLM fallback).

    Only fills when title is still NULL/'' — once set it is never regenerated
    (second turn onward is a no-op). Pre-existing NULL-title sessions recover
    progressively on their next user turn. LLM-generated titles are a later
    (paid-tier) concern; manual rename can be allowed for all tiers later.

    Applies to temp_ sessions too: the history drawer shows temp sessions in a
    separate zone below main, so a first-message title (any text) is fine as a
    label there. No special-casing — the first user message represents the
    session regardless of kind.
    """
    row = conn.execute(
        "SELECT title FROM TSK_SESSION WHERE session_id = ?", (session_id,)
    ).fetchone()
    if row and (row["title"] is None or row["title"] == ""):
        t = (first_user_text or "").strip().replace("\n", " ")
        if t:
            conn.execute(
                "UPDATE TSK_SESSION SET title = ? WHERE session_id = ?",
                (t[:_TITLE_MAXLEN], session_id),
            )


def _touch_session(conn: sqlite3.Connection, session_id: str, turn_count: Optional[int] = None,
                   first_user_text: Optional[str] = None):
    """Update last_active_at (+ turn_count) on the parent session.

    P1-2: when turn_count is not given, derive it from the actual row count in
    TSK_MESSAGE rather than blindly doing turn_count+1. The +1 form overcounts
    whenever a turn is re-saved on the same seq — which happens routinely after
    P1-1 DB-restore (ON CONFLICT(session_id, seq) DO UPDATE re-saves existing
    seqs) and on any edit/retry of a turn. COUNT(*) is always the truth.

    H1: when first_user_text is provided (caller passes it only for user turns),
    backfill the session title if still empty. Kept here so callers touch one
    function; default None keeps every existing call site unchanged.
    """
    now = _now()
    if turn_count is None:
        conn.execute(
            "UPDATE TSK_SESSION SET "
            "turn_count = (SELECT COUNT(*) FROM TSK_MESSAGE WHERE session_id = ?), "
            "last_active_at = ?, updated_at = ? WHERE session_id = ?",
            (session_id, now, now, session_id),
        )
    else:
        conn.execute(
            "UPDATE TSK_SESSION SET turn_count = ?, "
            "last_active_at = ?, updated_at = ? WHERE session_id = ?",
            (turn_count, now, now, session_id),
        )
    if first_user_text:
        _backfill_title(conn, session_id, first_user_text)


def save_turn(session_id: str, idx: int, role: str, text: str, meta: dict = None,
              is_temporary: int = 0, include_in_summary: int = 1,
              include_in_context: int = 1, context_group: str = "main"):
    """Save a single turn to TSK_MESSAGE (idempotent on (session_id, seq)).

    Lifecycle fields (§4.8/4.9): default 0/1/1/main = a normal durable turn,
    identical to pre-S1 behaviour. Temporary turns pass 1/0/0/'temporary' so the
    restore/summary filters (S2) can exclude them while keeping the row for audit.
    """
    conn = _get_conn()
    meta = meta or {}
    content, content_path = _store_content(session_id, idx, text)
    conn.execute(
        "INSERT INTO TSK_MESSAGE "
        "  (msg_id, session_id, seq, role, content, content_path, summary, "
        "   importance, keywords, is_temporary, include_in_summary, "
        "   include_in_context, context_group, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(session_id, seq) DO UPDATE SET "
        "  role=excluded.role, content=excluded.content, "
        "  content_path=excluded.content_path, summary=excluded.summary, "
        "  importance=excluded.importance, keywords=excluded.keywords, "
        "  is_temporary=excluded.is_temporary, "
        "  include_in_summary=excluded.include_in_summary, "
        "  include_in_context=excluded.include_in_context, "
        "  context_group=excluded.context_group",
        (
            _msg_id(session_id, idx),
            session_id,
            idx,
            role,
            content,
            content_path,
            meta.get("s", ""),
            meta.get("i", _DEFAULT_IMPORTANCE),
            json.dumps(meta.get("kw", []), ensure_ascii=False),
            is_temporary,
            include_in_summary,
            include_in_context,
            context_group,
            _now(),
        ),
    )
    # H1: backfill title from the first user message. Loose role match because
    # the DB uses you|ai|system but the client/LLM layer may emit user|assistant.
    if role in ("user", "you"):
        _touch_session(conn, session_id, first_user_text=text)
    else:
        _touch_session(conn, session_id)
    conn.commit()


def save_turns(session_id: str, turns: List[dict]):
    """Bulk save turns (for session dump). Replaces existing seqs."""
    conn = _get_conn()
    now = _now()
    for t in turns:
        meta = t.get("meta", {}) or {}
        idx = t.get("idx", 0)
        text = t.get("text", "")
        content, content_path = _store_content(session_id, idx, text)
        conn.execute(
            "INSERT INTO TSK_MESSAGE "
            "  (msg_id, session_id, seq, role, content, content_path, summary, "
            "   importance, keywords, is_temporary, include_in_summary, "
            "   include_in_context, context_group, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(session_id, seq) DO UPDATE SET "
            "  role=excluded.role, content=excluded.content, "
            "  content_path=excluded.content_path, summary=excluded.summary, "
            "  importance=excluded.importance, keywords=excluded.keywords, "
            "  is_temporary=excluded.is_temporary, "
            "  include_in_summary=excluded.include_in_summary, "
            "  include_in_context=excluded.include_in_context, "
            "  context_group=excluded.context_group",
            (
                _msg_id(session_id, idx),
                session_id,
                idx,
                t.get("role", "user"),
                content,
                content_path,
                meta.get("s", ""),
                meta.get("i", _DEFAULT_IMPORTANCE),
                json.dumps(meta.get("kw", []), ensure_ascii=False),
                int(meta.get("is_temporary", 0)),
                int(meta.get("include_in_summary", 1)),
                int(meta.get("include_in_context", 1)),
                meta.get("context_group", "main"),
                now,
            ),
        )
    _touch_session(conn, session_id, turn_count=len(turns))
    conn.commit()


def load_turns(session_id: str, limit: int = 100) -> List[dict]:
    """Load turns for restore, ordered by seq. Returns i/kw/s/text/role dicts.

    §4.8/4.9 restore filter: only durable, context-eligible, non-temporary turns
    rehydrate into live memory. Temporary turns (is_temporary=1) and turns flagged
    out of context (include_in_context=0) stay in the DB for audit but never leak
    back into the conversation. Keeps seq order so the rebuilt history is faithful.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM TSK_MESSAGE "
        "WHERE session_id = ? AND include_in_context = 1 AND is_temporary = 0 "
        "ORDER BY seq ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    return [_row_to_turn(r) for r in rows]


def load_turns_raw(session_id: str, limit: int = 200) -> List[dict]:
    """ALL turns for the curation / history card panel — NO restore filter.

    Unlike load_turns (which hides excluded/temporary turns so live restore stays
    faithful to the §4.8/4.9 context contract), the card panel is a *curation*
    surface: it MUST show excluded (include_in_context=0) and temporary
    (is_temporary=1) turns, otherwise the later include/exclude toggle (2단계) has
    nothing to act on. Returns lifecycle flags + turn_status + has_summary so the
    UI can badge/dim each card.

    NEVER call this from the live-restore path. Restore = load_turns (filtered);
    history/curation = load_turns_raw (unfiltered). Keeping them as separate names
    (instead of one function with an include_hidden flag) is deliberate so the
    restore path can never accidentally pull hidden turns back into context.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT seq, role, summary, importance, keywords, content, content_path, "
        "       is_temporary, include_in_context, context_group, turn_status "
        "FROM TSK_MESSAGE WHERE session_id = ? ORDER BY seq ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    out = []
    for r in rows:
        s = r["summary"] or ""
        try:
            kw = json.loads(r["keywords"]) if r["keywords"] else []
        except Exception:
            kw = []
        out.append({
            "seq": r["seq"],
            "role": r["role"],
            "s": s,
            "has_summary": bool(s),
            "i": r["importance"] if r["importance"] is not None else _DEFAULT_IMPORTANCE,
            "kw": kw,
            "text": _read_content(r),
            "is_temporary": r["is_temporary"],
            "include_in_context": r["include_in_context"],
            "context_group": r["context_group"],
            "turn_status": r["turn_status"],
        })
    return out


def load_call_body(session_id: str, msg_seq) -> dict:
    """Resolve a turn (session_id + msg_seq) to its AI-call telemetry + body.

    Backs the Memory Editor card's [Input]/[Output] view: the turn knows its
    seq, TSK_CALL.msg_seq points back to the call row, and log_ref points at the
    JSONL body. Returns {found, has_body, level, input_prompt, output_text, ...}.
    The body stays None unless telemetry.level (debug/trace) actually wrote it.
    """
    out = {"found": False, "has_body": False}
    try:
        seq = int(msg_seq)
    except (TypeError, ValueError):
        return out
    row = _get_conn().execute(
        "SELECT call_id, log_ref, telemetry_level, ctx_mode, turns_merged, "
        "       prompt_tokens, completion_tokens, total_tokens, elapsed_ms, ttft_ms, "
        "       finish, ok, provider, model, refeed, created_at, error_type, error_summary "
        "FROM TSK_CALL WHERE session_id = ? AND msg_seq = ? "
        "ORDER BY id DESC LIMIT 1",
        (session_id, seq),
    ).fetchone()
    if not row:
        return out
    out.update({
        "found": True,
        "call_id": row["call_id"],
        "level": row["telemetry_level"],
        "ctx_mode": row["ctx_mode"],
        "turns_merged": row["turns_merged"],
        "prompt_tokens": row["prompt_tokens"],
        "completion_tokens": row["completion_tokens"],
        "total_tokens": row["total_tokens"],
        "elapsed_ms": row["elapsed_ms"],
        "ttft_ms": row["ttft_ms"],
        "finish": row["finish"],
        "ok": row["ok"],
        "provider": row["provider"],
        "model": row["model"],
        "refeed": row["refeed"],
        "created_at": row["created_at"],
        "error_type": row["error_type"],
        "error_summary": row["error_summary"],
    })
    if row["log_ref"]:
        from usekit.llm.base.init.lli_calllog import read_call_body
        body = read_call_body(row["call_id"], row["log_ref"])
        if body:
            out["has_body"] = True
            out["input_prompt"] = body.get("input_prompt")
            out["output_text"] = body.get("output_text")
            if "final_prompt" in body:
                out["final_prompt"] = body.get("final_prompt")
    return out


def load_turns_for_summary(session_id: str, limit: int = 100) -> List[dict]:
    """Load turns eligible for summarisation (§4.9).

    Separate from load_turns because the summary set uses include_in_summary,
    not include_in_context. Temporary turns are excluded here too. Used by the
    compress/summary path (STEP6c §4.6) — not by live restore.
    """
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM TSK_MESSAGE "
        "WHERE session_id = ? AND include_in_summary = 1 AND is_temporary = 0 "
        "ORDER BY seq ASC LIMIT ?",
        (session_id, limit),
    ).fetchall()
    return [_row_to_turn(r) for r in rows]


def search_turns(keyword: str, limit: int = 20) -> List[dict]:
    """Search across sessions by keyword in content / summary / keywords."""
    conn = _get_conn()
    pattern = f"%{keyword}%"
    rows = conn.execute(
        "SELECT m.*, s.provider, s.model FROM TSK_MESSAGE m "
        "JOIN TSK_SESSION s ON m.session_id = s.session_id "
        "WHERE m.content LIKE ? OR m.summary LIKE ? OR m.keywords LIKE ? "
        "ORDER BY m.created_at DESC LIMIT ?",
        (pattern, pattern, pattern, limit),
    ).fetchall()
    result = []
    for r in rows:
        turn = _row_to_turn(r)
        turn["provider"] = r["provider"]
        turn["model"] = r["model"]
        result.append(turn)
    return result


def clear_session(session_id: str):
    """Delete all messages for a session and reset its turn_count."""
    conn = _get_conn()
    conn.execute("DELETE FROM TSK_MESSAGE WHERE session_id = ?", (session_id,))
    conn.execute(
        "UPDATE TSK_SESSION SET turn_count = 0, updated_at = ? WHERE session_id = ?",
        (_now(), session_id),
    )
    conn.commit()


def delete_session(session_id: str) -> dict:
    """Delete a whole session: its TSK_MESSAGE turns AND its TSK_SESSION row.

    Unlike clear_session (which empties turns but keeps the session row), this
    removes the session entirely. The left-panel session manager is the ONLY
    place allowed to delete a session (§ SESSION_ID_MANAGEMENT: 삭제는 좌측 패널만).
    Slot destruction never calls this — sessions outlive slots (orphan-safe).

    There is no FK ON DELETE CASCADE between TSK_MESSAGE and TSK_SESSION, so both
    tables are cleared explicitly in one transaction. Returns counts for caller.
    """
    conn = _get_conn()
    msg_n = conn.execute(
        "SELECT COUNT(*) FROM TSK_MESSAGE WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    sess_n = conn.execute(
        "SELECT COUNT(*) FROM TSK_SESSION WHERE session_id = ?", (session_id,)
    ).fetchone()[0]
    conn.execute("DELETE FROM TSK_MESSAGE WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM TSK_SESSION WHERE session_id = ?", (session_id,))
    conn.commit()
    return {"session_id": session_id, "existed": bool(sess_n),
            "messages_deleted": msg_n}


# -- Utility --

def db_path() -> str:
    """Return the resolved DB path (for inspection)."""
    return str(_db_path())


def close():
    """Close the cached connection."""
    global _conn_cache
    if _conn_cache:
        _conn_cache.close()
        _conn_cache = None


__all__ = [
    "create_session", "get_session", "list_sessions",
    "save_turn", "save_turns", "load_turns", "load_turns_for_summary", "search_turns", "clear_session",
    "db_path", "close",
]
