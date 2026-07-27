-- ============================================================
-- TSK_IDX : Indexes for Task-management support domain
-- ============================================================
-- Pairs with 01_TSK.sql. Loaded after it (alphabetical: 01 -> 02).
-- Indexes chosen to serve the queries the editor actually runs:
--   Manager list/status, per-seq progress (Check), re-injection,
--   session resume, context lookup.

-- TASK : Manager list (status board) + session/context joins
CREATE INDEX IF NOT EXISTS idx_tsk_task_status  ON TSK_TASK(status, is_active);
CREATE INDEX IF NOT EXISTS idx_tsk_task_session ON TSK_TASK(session_id);
CREATE INDEX IF NOT EXISTS idx_tsk_task_context ON TSK_TASK(context_id);

-- STEP : Manager 'Check' = per-task seq progress; verify sweeps
CREATE INDEX IF NOT EXISTS idx_tsk_step_task   ON TSK_STEP(task_id, seq);
CREATE INDEX IF NOT EXISTS idx_tsk_step_status ON TSK_STEP(status);
CREATE INDEX IF NOT EXISTS idx_tsk_step_verify ON TSK_STEP(verify_pass);

-- SESSION : resume (most-recent-active) + mode filter
CREATE INDEX IF NOT EXISTS idx_tsk_session_active ON TSK_SESSION(status, last_active_at);
CREATE INDEX IF NOT EXISTS idx_tsk_session_mode   ON TSK_SESSION(mode);

-- MESSAGE : ordered fetch within a session + token-budget scan
CREATE INDEX IF NOT EXISTS idx_tsk_message_session ON TSK_MESSAGE(session_id, seq);
CREATE INDEX IF NOT EXISTS idx_tsk_message_role    ON TSK_MESSAGE(session_id, role);

-- MESSAGE STEP6c : restore/summary filters (§4.9/§4.10) + context_turn_count
--   restore  = include_in_context=1 AND is_temporary=0 AND turn_status='ok'
--   summary  = include_in_summary=1 AND is_temporary=0 AND turn_status='ok'
CREATE INDEX IF NOT EXISTS idx_tsk_message_restore ON TSK_MESSAGE(session_id, include_in_context, is_temporary, turn_status, seq);
CREATE INDEX IF NOT EXISTS idx_tsk_message_summary ON TSK_MESSAGE(session_id, include_in_summary, is_temporary, turn_status, seq);
CREATE INDEX IF NOT EXISTS idx_tsk_message_retry   ON TSK_MESSAGE(session_id, parent_user_seq);

-- CONTEXT : active pack lookup
CREATE INDEX IF NOT EXISTS idx_tsk_context_active ON TSK_CONTEXT(is_active);
