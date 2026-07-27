-- ============================================================
-- TSK : Task-management support domain (usekit editor)
-- ============================================================
-- Target DB : .usekit/sys/sys_db/usekit.db   (unified, get_sys_db_path)
-- Loaded by : for f in sorted(u.fdd("*", wk=True)): ud.script(u.rdd(f))
--
-- This is the support DB for the usekit editor's task manager.
-- It is NOT project application data (that lives in base.db).
-- One support DB per usekit workspace; tracks tasks the editor
-- issues to executors (Claude Code / Codex) to build real projects.
--
-- Source design : guide DATA_ARCHITECTURE.md §3 (5-table stable form)
--                 + TASK_INSTRUCTION_TEMPLATE.md (step.input format)
-- Philosophy    : DB = state/relation/index, files = body (SSOT).
--                 Folder (docs/) survives even if this DB is lost.
-- ============================================================


-- TSK_TASK : one row = one task folder (docs/ task unit).
--   The folder is the body (SSOT); this row is the index/status tag.

CREATE TABLE IF NOT EXISTS TSK_TASK (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT NOT NULL UNIQUE,        -- folder name (e.g. 'task_ae01d8')
    title       TEXT,
    status      TEXT DEFAULT 'pending',      -- pending|running|done|cancelled|error
    command     TEXT,                        -- launch command / intent

    -- relations
    session_id  TEXT,                        -- which session issued it (TSK_SESSION)
    context_id  TEXT,                        -- which context pack was fed (TSK_CONTEXT)

    -- body (file paths — grep-reachable, not duplicated into DB)
    folder_path TEXT,                        -- task folder (docs/...)
    log_path    TEXT,                        -- long exec log file
    result_path TEXT,                        -- result body file
    parts       TEXT,                        -- attached outputs (JSON list)

    -- short result kept in DB directly (small + query target)
    summary     TEXT,

    is_active   INTEGER DEFAULT 1,
    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT
);


-- TSK_STEP : the job-list items of a task (seq).
--   One row = one self-contained instruction (TASK_INSTRUCTION_TEMPLATE).
--   Manager 'Check' queries this for per-seq progress.
--   step.input  = the instruction MD body (or its path).
--   step.status = decided by the CHECK block via 'uk verify'.

CREATE TABLE IF NOT EXISTS TSK_STEP (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    step_id     TEXT NOT NULL UNIQUE,
    task_id     TEXT NOT NULL,               -- FK -> TSK_TASK.task_id
    seq         INTEGER NOT NULL,            -- matches folder prefix (01_, 02_)
    title       TEXT,
    status      TEXT DEFAULT 'pending',      -- 8-state enum (sbi_task_const.STATUS):
                                             --   pending|running|waiting_feedback|retry|
                                             --   blocked|done|failed|archived
                                             --   (legacy 'error' folded into 'failed')

    -- instruction (self-contained MD). Small -> inline; large -> path.
    input       TEXT,                        -- instruction body (short)
    input_path  TEXT,                        -- instruction file (long)
    output_path TEXT,                        -- produced artifact (seq file)
    log_path    TEXT,
    check_block TEXT,                         -- CHECK block text (uk verify input)
    verify_pass INTEGER,                      -- 1 pass / 0 fail / NULL not run

    summary     TEXT,

    -- ---- queue engine fields (added 2026-06-08; auto-migrated by _migrate_add_missing_columns) ----
    -- TSK_STEP doubles as the queue body. These columns drive worker dispatch,
    -- state transition and the emit chain. enum/shape SSOT = sbi_task_const.py
    -- (these comments derive from it; keep them in sync).
    --
    -- !! Do NOT add indexes on these columns in 02_TSK_IDX yet. setup runs
    --    executescript(indexes) BEFORE _migrate(column add), so an index on a
    --    not-yet-added column raises "no such column". Add (status, run_after)
    --    and (parent_call_id) only AFTER the columns settle (queue-engine step).
    parent_step_id TEXT,                     -- emit chain: which step scheduled this one
    parent_call_id TEXT,                     -- logical ref -> TSK_CALL.call_id (call -> step trace)
    worker_type    TEXT,                     -- llm | cli | read | write | none
    action_type    TEXT,                     -- none | next_turn | read | write | run_command
    depth          INTEGER DEFAULT 0,        -- recursion depth within the emit chain
    max_depth      INTEGER DEFAULT 5,        -- hard ceiling (enforced by uu.queue.pop)
    payload_json   TEXT,                     -- worker input  {version,source,input,options}
    result_json    TEXT,                     -- worker output {version,ok,output,summary}
    error_json     TEXT,                     -- failure detail {version,type,message,trace,retryable}
    run_after      TEXT,                     -- delayed-run schedule (datetime; NULL = immediate)

    created_at  TEXT DEFAULT (datetime('now','localtime')),
    updated_at  TEXT,
    UNIQUE(task_id, seq)
);


-- TSK_SESSION : conversation/work session + rolling summary.
--   summary_md is what gets re-injected (not the raw transcript) -> token economy.

CREATE TABLE IF NOT EXISTS TSK_SESSION (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT NOT NULL UNIQUE,
    title              TEXT,
    mode               TEXT DEFAULT 'chat',  -- chat|task|edit (3-axis)
    status             TEXT DEFAULT 'active',-- active|closed
    started_at         TEXT DEFAULT (datetime('now','localtime')),
    last_active_at     TEXT,
    summary_md         TEXT,                 -- session summary (re-injected)
    current_context_id TEXT,                 -- active context pack
    meta               TEXT,                 -- JSON misc (api_key_ref, NOT api_key)

    -- llm absorption (live chat sessions)
    provider           TEXT,                 -- groq|qwen|claude_code|...
    model              TEXT,
    kind               TEXT DEFAULT 'live',  -- live (chat累積) | job (CLI)
    cli_session_id     TEXT,                 -- CLI resume key (kind='job' only)
    slot               TEXT,                 -- owning editor slot name (NULL = orphan, no slot)
    turn_count         INTEGER DEFAULT 0,

    created_at         TEXT DEFAULT (datetime('now','localtime')),
    updated_at         TEXT
);


-- TSK_MESSAGE : full messages live here; summaries are layered for re-injection.
--   content short -> inline ; long -> content_path. summary = one-line re-inject.

CREATE TABLE IF NOT EXISTS TSK_MESSAGE (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    msg_id      TEXT NOT NULL UNIQUE,
    session_id  TEXT NOT NULL,               -- FK -> TSK_SESSION.session_id
    seq         INTEGER NOT NULL,            -- order within session
    role        TEXT NOT NULL,               -- you|ai|system
    content     TEXT,                        -- full text (short) or null
    content_path TEXT,                       -- full text file (long)
    summary     TEXT,                        -- one-line summary (re-inject) = meta.s
    token_est   INTEGER,                     -- token budget tracking

    -- llm absorption (History meta)
    importance  INTEGER DEFAULT 0,           -- meta.i (sort/filter, auto re-feed)
    keywords    TEXT,                        -- meta.kw (JSON array)
    meta        TEXT,                        -- misc JSON buffer

    -- STEP6c §4.9 Temporary Turn Policy
    --   normal = 0/1/1/'main' ; temporary = 1/0/0/'temporary'
    is_temporary       INTEGER DEFAULT 0,    -- 1 = transient turn (temp_sid)
    include_in_summary INTEGER DEFAULT 1,    -- summary candidate
    include_in_context INTEGER DEFAULT 1,    -- restore candidate (shared w/ §4.10)
    context_group      TEXT DEFAULT 'main',  -- 'main' | 'temporary'

    -- STEP6c §4.10 Session Error Policy
    --   a failed model call MUST NOT become a valid assistant turn
    turn_status     TEXT DEFAULT 'ok',       -- ok|failed|partial|cancelled|blocked|db_pending
    error_code      TEXT,                    -- e.g. 'llm_timeout'
    error_message   TEXT,                    -- human-readable failure note
    parent_user_seq INTEGER,                 -- retry anchor (the user turn this answers)
    run_id          TEXT,                    -- groups turns from one call/run

    created_at  TEXT DEFAULT (datetime('now','localtime')),
    UNIQUE(session_id, seq)
);


-- TSK_CONTEXT : a pack of files fed to a task + its summary.
--   source_files is JSON (read/written whole -> no join table needed).

CREATE TABLE IF NOT EXISTS TSK_CONTEXT (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    context_id     TEXT NOT NULL UNIQUE,
    name           TEXT,
    purpose        TEXT,
    source_files   TEXT,                     -- file path list (JSON)
    summary        TEXT,
    token_estimate INTEGER,
    is_active      INTEGER DEFAULT 1,
    created_at     TEXT DEFAULT (datetime('now','localtime')),
    updated_at     TEXT
);
