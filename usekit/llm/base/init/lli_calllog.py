# =============================================================================
#  lli_calllog : LLM call-body logger (the "body" half of TSK_CALL telemetry).
# =============================================================================
#  TSK_CALL row = summary/index (queryable). The full input prompt + output
#  body live in a JSONL file; TSK_CALL.log_ref points at that file. This is the
#  "DB = summary, file = body" split from the TSK_CALL schema header.
#
#  Policy source = SYS_META (seeded, audit-approved):
#    telemetry.level              summary (DB only) | debug (bodies) | trace (+final_prompt)
#    telemetry.store_final_prompt 1 = include final_prompt (trace only); default 0 (OFF)
#
#  Reuses existing parts only: parser_json.dump(append_mode="jsonl") for the
#  write, lli_db helpers for paths/conn, history._db_fail for surfacing.
#  Best-effort: any failure is surfaced via _db_fail (P1-3) and returns None,
#  so the chat stream is never killed.
# =============================================================================
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from usekit.llm.base.init.lli_db import _db_path, _get_conn
from usekit.llm.history import _db_fail

_DEFAULT_LEVEL = "summary"


def _calllog_dir() -> Path:
    """ai_calls/ next to the unified DB (mirrors lli_db._spill_dir layout)."""
    d = _db_path().parent / "ai_calls"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _read_meta(key: str, default: str) -> str:
    """Read one SYS_META value (key/value table); fall back on any error."""
    try:
        row = _get_conn().execute(
            "SELECT value FROM SYS_META WHERE key = ?", (key,)
        ).fetchone()
        if row and row[0] is not None:
            return str(row[0])
    except Exception:
        pass
    return default


def get_telemetry_level() -> str:
    """Current telemetry.level from SYS_META (summary|debug|trace)."""
    return _read_meta("telemetry.level", _DEFAULT_LEVEL)


def append_call_log(
    call_id: str,
    *,
    level: Optional[str] = None,
    input_prompt: Optional[str] = None,
    output_text: Optional[str] = None,
    final_prompt: Optional[str] = None,
) -> Optional[str]:
    """Append one call-body record to <base>/ai_calls/<YYYY-MM-DD>.jsonl.

    level summary -> bodies are NOT written; returns None (log_ref stays NULL).
    level debug   -> input_prompt + output_text bodies written.
    level trace   -> also final_prompt, but only if telemetry.store_final_prompt=1.

    Returns the JSONL file path (= the log_ref; the matching row is found by
    call_id inside it), or None when nothing was written / on failure.
    """
    lvl = (level or get_telemetry_level()).strip().lower()
    if lvl == "summary":
        return None  # DB-only: keep no bodies on disk

    try:
        # Reuse the existing JSONL appender (parser_json.dump jsonl mode).
        from usekit.classes.data.base.post.parser.parser_json import dump as _json_dump

        rec = {
            "call_id": call_id,
            "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "level": lvl,
            "input_prompt": input_prompt,
            "output_text": output_text,
        }
        # final_prompt is the most sensitive/largest field: trace + explicit opt-in only.
        if lvl == "trace" and _read_meta("telemetry.store_final_prompt", "0") == "1":
            rec["final_prompt"] = final_prompt

        fp = _calllog_dir() / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        _json_dump(rec, str(fp), append=True, append_mode="jsonl")
        return str(fp)
    except Exception as _e:
        _db_fail("append_call_log", _e)
        return None


def read_call_body(call_id: str, log_ref: Optional[str]) -> Optional[dict]:
    """Read the body record for call_id from its JSONL log_ref file (read side).

    Returns the dict (input_prompt/output_text/level/...) or None when the file
    is missing or has no matching row (e.g. summary level wrote nothing).
    """
    if not log_ref:
        return None
    try:
        if not Path(log_ref).exists():
            return None
        from usekit.classes.data.base.post.parser.parser_json import load as _json_load

        rows = _json_load(log_ref, jsonl=True)
        if isinstance(rows, dict):  # single-row safety
            rows = [rows]
        for r in (rows or []):
            if isinstance(r, dict) and r.get("call_id") == call_id:
                return r
        return None
    except Exception as _e:
        _db_fail("read_call_body", _e)
        return None
