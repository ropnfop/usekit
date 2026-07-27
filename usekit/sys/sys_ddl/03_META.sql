-- ============================================================
-- META : usekit.db meta layers (3-tier, prefix-separated)
--   SYS_META  system/app-global KV  (schema_version, colors, api_key_ref)
--   TBL_META  schema dictionary     (table × column × enum: label/desc/color)
--   TSK_META  task-domain KV         (per-task or global task settings)
-- One DB (usekit.db), tiers distinguished by table prefix only.
-- Loaded after 01/02 (alphabetical). Audit-approved (안②, 2026-06-03).
-- ============================================================

-- SYS_META : flat global key/value.
CREATE TABLE IF NOT EXISTS SYS_META (
    key         TEXT PRIMARY KEY,
    value       TEXT,
    description TEXT,
    updated_at  TEXT DEFAULT (datetime('now','localtime'))
);

-- TBL_META : schema dictionary. UI/runtime read this instead of hardcoding.
--   enum_value IS NULL  → column-level description
--   enum_value NOT NULL → that enum value's label/description/color
CREATE TABLE IF NOT EXISTS TBL_META (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name   TEXT NOT NULL,
    column_name  TEXT NOT NULL,
    enum_value   TEXT,
    label        TEXT,
    description  TEXT,
    color        TEXT,
    ord          INTEGER DEFAULT 0,
    UNIQUE(table_name, column_name, enum_value)
);
CREATE INDEX IF NOT EXISTS idx_tbl_meta_col ON TBL_META(table_name, column_name, ord);
-- Partial-unique for column-level rows (enum_value IS NULL): SQLite treats NULL
-- as distinct in UNIQUE, so without this the column-desc row could duplicate
-- and ON CONFLICT(table_name,column_name) WHERE enum_value IS NULL would fail.
CREATE UNIQUE INDEX IF NOT EXISTS uq_tbl_meta_col_desc
    ON TBL_META(table_name, column_name) WHERE enum_value IS NULL;

-- TSK_META : task-domain settings. task_id NULL = global task default.
CREATE TABLE IF NOT EXISTS TSK_META (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id     TEXT,
    key         TEXT NOT NULL,
    value       TEXT,
    description TEXT,
    UNIQUE(task_id, key)
);
CREATE INDEX IF NOT EXISTS idx_tsk_meta_task ON TSK_META(task_id, key);
