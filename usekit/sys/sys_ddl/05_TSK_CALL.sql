-- ============================================================
-- TSK_CALL : AI call telemetry (tuning instrument). usekit.db.
-- DB = summary row per call; JSONL = detail per call (log_ref points to it).
-- Audit-approved x3 (2026-06-03): full in/out set, ok=0 rows kept,
-- final_prompt OFF by default (trace only). Loaded after 04.
-- ============================================================
CREATE TABLE IF NOT EXISTS TSK_CALL (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    call_id           TEXT UNIQUE,
    session_id        TEXT,                -- FK TSK_SESSION (NULL = one-off)
    msg_seq           INTEGER,
    provider          TEXT,
    model             TEXT,
    kind              TEXT,                -- live|job
    -- input telemetry
    ctx_mode          TEXT,                -- compress|full|auto
    turns_merged      INTEGER,
    refeed            TEXT,                -- resume|append|meta_only|none
    prompt_tokens     INTEGER,
    -- output telemetry
    completion_tokens INTEGER,
    total_tokens      INTEGER,
    elapsed_ms        INTEGER,
    ttft_ms           INTEGER,             -- stream only; NULL for block/fail
    finish            TEXT,                -- stop|length|error|cancel
    ok                INTEGER,             -- 1|0 (failures MUST be recorded)
    -- failure (stacktrace goes to JSONL, NOT here)
    error_type        TEXT,
    error_summary     TEXT,
    -- linkage / mode
    log_ref           TEXT,                -- ai_calls JSONL location
    telemetry_level   TEXT,                -- summary|debug|trace (at emit time)
    route             TEXT,                -- caller stage tag (white|fop|...) — pj01/app set
    turn_ref          TEXT,                -- caller turn id — groups calls of one logical turn
    created_at        TEXT DEFAULT (datetime('now','localtime'))
);
CREATE INDEX IF NOT EXISTS idx_tsk_call_session ON TSK_CALL(session_id, msg_seq);
CREATE INDEX IF NOT EXISTS idx_tsk_call_model   ON TSK_CALL(provider, model, created_at);
CREATE INDEX IF NOT EXISTS idx_tsk_call_ctx     ON TSK_CALL(ctx_mode, refeed, ok, created_at);
CREATE INDEX IF NOT EXISTS idx_tsk_call_ok      ON TSK_CALL(ok, finish, created_at);
CREATE INDEX IF NOT EXISTS idx_tsk_call_turn    ON TSK_CALL(turn_ref, route);
