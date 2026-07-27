# Path: usekit.tools.task.task_manager.py
# -----------------------------------------------------------------------------------------------
#  Task Manager — CLI runner adapter (state-less)
#  Created by: THE Little Prince × ROP × FOP
#
#  ROLE (DECISION 2026-06-08): this module is a RUNNER, not a state owner.
#  State (status / relations) lives in usekit.db / TSK_STEP, owned by the queue
#  engine (uu.queue). task_manager only knows how to *execute*:
#       run_command(cmd, log_path) -> pid     launch (nohup), return pid
#       tail_log(log_path)         -> text     read a log tail
#       check_pid(pid)             -> bool     is the process alive
#  None of these touch a DB. The queue passes a step's command/log_path in and
#  records the result back into TSK_STEP itself.
#
#  The legacy tasks-DB API below (add_task/start_task/.../init_db) is DEPRECATED:
#  it kept a second source of truth in task_manager.db and is the state
#  duplication this refactor removes. It is retained (not deleted) until the
#  on-device `tasks` table is confirmed empty (0 rows), then it can be dropped.
#  New code paths MUST use the runner adapter, never the legacy DB functions.
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import sqlite3
import time
import os
import subprocess
import shlex

from usekit.classes.core.env.loader_env import get_base_path

# ─────────────────────────────────────────────────────────────────────────────
# Paths (auto-resolved from USEKIT base)
# ─────────────────────────────────────────────────────────────────────────────
_BASE = Path(get_base_path())
DB_PATH = _BASE / "data" / "table" / "db" / "task_manager.db"
LOG_DIR = _BASE / "logs"
RESULT_DIR = _BASE / "results"

DB_PATH.parent.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _conn():
    return sqlite3.connect(str(DB_PATH))


# ─────────────────────────────────────────────────────────────────────────────
# Runner adapter (state-less) — the supported surface for the queue engine.
#   These own NO DB row. The queue engine (uu.queue) supplies the command and
#   log_path from a TSK_STEP, runs it here, and writes status/result back into
#   TSK_STEP itself. No second source of truth.
# ─────────────────────────────────────────────────────────────────────────────
def run_command(command, log_path=None, cwd=None):
    """Launch a shell command via nohup; return its PID (int). State-less.

    command  : the shell command to run.
    log_path : if given, stdout+stderr are redirected there (queue derives it
               from the step's log_path).
    cwd      : optional working directory.
    """
    inner = command if not cwd else f"cd {shlex.quote(str(cwd))} && {command}"
    redirect = f"> {shlex.quote(str(log_path))} 2>&1" if log_path else ""
    full_cmd = f"nohup sh -c {shlex.quote(inner)} {redirect} & echo $!"
    pid = int(subprocess.check_output(full_cmd, shell=True).decode().strip())
    return pid


def tail_log(log_path, lines=50):
    """Return the last N lines of a log file, or None if absent. State-less."""
    if not log_path or not Path(log_path).exists():
        return None
    result = subprocess.run(
        ["tail", f"-{lines}", str(log_path)], capture_output=True, text=True
    )
    return result.stdout


def check_pid(pid):
    """True if the process is alive. State-less (no DB write, unlike check_tasks)."""
    if not pid:
        return False
    return os.system(f"kill -0 {int(pid)} 2>/dev/null") == 0


# ─────────────────────────────────────────────────────────────────────────────
# [DEPRECATED] Legacy tasks-DB API (state owner) — task_manager.db
#   Kept for backward compat until the on-device `tasks` table is confirmed
#   empty, then removable. New code MUST NOT call these; use the runner adapter
#   above + uu.task / uu.queue for state.
# ─────────────────────────────────────────────────────────────────────────────
def init_db():
    """Create tasks table if not exists."""
    with _conn() as db:
        db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_key TEXT UNIQUE,
            title TEXT,
            status TEXT DEFAULT 'pending',
            command TEXT,
            pid INTEGER,
            log_path TEXT,
            result_path TEXT,
            created_at TEXT,
            started_at TEXT,
            finished_at TEXT,
            updated_at TEXT
        )
        """)
        db.commit()


# ─────────────────────────────────────────────────────────────────────────────
# Core API
# ─────────────────────────────────────────────────────────────────────────────
def add_task(task_key, title, command):
    """Register a task in DB (pending state)."""
    init_db()
    log_path = str(LOG_DIR / f"{task_key}.log")
    result_path = str(RESULT_DIR / f"{task_key}.md")

    with _conn() as db:
        db.execute("""
        INSERT OR REPLACE INTO tasks
        (task_key, title, status, command, log_path, result_path, created_at, updated_at)
        VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)
        """, (task_key, title, command, log_path, result_path, _now(), _now()))
        db.commit()

    print(f"[TASK] added: {task_key}")
    print(f"  log: {log_path}")
    print(f"  result: {result_path}")
    return task_key


def start_task(task_key):
    """Launch task via nohup, save PID."""
    with _conn() as db:
        row = db.execute(
            "SELECT command, log_path FROM tasks WHERE task_key=?",
            (task_key,)
        ).fetchone()

        if not row:
            raise SystemExit(f"Task not found: {task_key}")

        command, log_path = row

        full_cmd = f"nohup sh -c {shlex.quote(command)} > {shlex.quote(log_path)} 2>&1 & echo $!"
        pid = int(subprocess.check_output(full_cmd, shell=True).decode().strip())

        db.execute("""
        UPDATE tasks
        SET status='running', pid=?, started_at=?, updated_at=?
        WHERE task_key=?
        """, (pid, _now(), _now(), task_key))
        db.commit()

    print(f"[TASK] started: {task_key} (pid={pid})")
    print(f"  log: {log_path}")
    return pid


def run_task(task_key, title, command):
    """Shortcut: add + start in one call."""
    add_task(task_key, title, command)
    return start_task(task_key)


def list_tasks():
    """Print all tasks with status."""
    init_db()
    with _conn() as db:
        rows = db.execute("""
        SELECT task_key, status, pid, title, log_path
        FROM tasks ORDER BY id DESC
        """).fetchall()

    if not rows:
        print("[TASK] no tasks")
        return []

    for task_key, status, pid, title, log_path in rows:
        print(f"  {task_key} | {status} | pid={pid} | {title}")
    return rows


def check_tasks():
    """Auto-mark running tasks as done if PID is dead."""
    with _conn() as db:
        rows = db.execute("""
        SELECT task_key, pid FROM tasks
        WHERE status='running' AND pid IS NOT NULL
        """).fetchall()

        count = 0
        for task_key, pid in rows:
            alive = os.system(f"kill -0 {pid} 2>/dev/null") == 0
            if not alive:
                db.execute("""
                UPDATE tasks
                SET status='done', finished_at=?, updated_at=?
                WHERE task_key=?
                """, (_now(), _now(), task_key))
                count += 1

        db.commit()

    if count:
        print(f"[TASK] {count} task(s) marked done")
    return count


def tail_task(task_key, lines=50):
    """Print last N lines of task log."""
    with _conn() as db:
        row = db.execute(
            "SELECT log_path FROM tasks WHERE task_key=?",
            (task_key,)
        ).fetchone()

    if not row:
        print(f"[TASK] not found: {task_key}")
        return None

    log_path = row[0]
    if not Path(log_path).exists():
        print(f"[TASK] log not yet created: {log_path}")
        return None

    result = subprocess.run(
        ["tail", f"-{lines}", log_path],
        capture_output=True, text=True
    )
    print(result.stdout)
    return result.stdout


def get_status(task_key):
    """Get single task status."""
    with _conn() as db:
        row = db.execute(
            "SELECT status, pid FROM tasks WHERE task_key=?",
            (task_key,)
        ).fetchone()

    if not row:
        return None
    return {"status": row[0], "pid": row[1]}


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    init_db()

    if len(sys.argv) < 2:
        print("Usage: python task_manager.py [list|check|tail <key>]")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "list":
        list_tasks()
    elif cmd == "check":
        check_tasks()
        list_tasks()
    elif cmd == "tail" and len(sys.argv) > 2:
        tail_task(sys.argv[2])
    else:
        print(f"Unknown command: {cmd}")
