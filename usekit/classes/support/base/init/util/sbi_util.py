# Path: usekit.classes.support.base.init.util.sbi_util.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# — memory is emotion —
#
# Util Support Handler — uu
#
# usekit utilities. First feature: the task work-unit generator.
#
# A "task" is a folder under docs/task/<task_id>/ holding seq-numbered
# documents (01_*.md ...), a manifest.json (self-describing), and a _DONE
# marker when frozen. The folder is the body (SSOT, grep-reachable); the
# support DB (.usekit/sys/sys_db/usekit.db) holds the status/relation index.
# DB can be lost and rebuilt from manifest.json — folder wins.
#
# Usage:
#   from usekit import uu
#
#   t  = uu.task.new("Refactor float_ai header", command="patch")
#   uu.task.step(t, "Apply seg router", input="# STEP ...\n## CHECK\n...")
#   uu.task.list()                      # rows from task.db
#   uu.task.show(t)                     # one task + its steps
#   uu.task.done(t)                     # freeze: write _DONE + status=done
#
# Design notes:
#   - Paths come from loader_env (get_sys_db_path). No hardcoding.
#   - usekit.db is opened with an explicit path, so it never
#     collides with the project's base.db.
#   - Idempotent where it can be; folder + DB stay in sync via manifest.json.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# enum/status vocabulary SSOT (no hardcoded state strings — DESIGN §2.4)
from usekit.classes.support.base.init.util import sbi_task_const as tc


# Relative anchors (resolved against project base at call time)
_TASK_ROOT_REL = "docs/task"                      # MD_PATH.root("docs") / task


def _base() -> Path:
    from usekit.classes.core.env.loader_env import get_base_path
    return get_base_path()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _short_id() -> str:
    return uuid.uuid4().hex[:6]


# -----------------------------------------------------------------------------------------------
# DB access (usekit.db) — thin, explicit, no external deps
# -----------------------------------------------------------------------------------------------

def _db_path() -> Path:
    # Single source of truth for the unified support DB path.
    from usekit.classes.core.env.loader_env import get_sys_db_path
    return get_sys_db_path()


def _connect() -> sqlite3.Connection:
    p = _db_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(p))
    con.row_factory = sqlite3.Row
    return con


class _TaskUtil:
    """Task work-unit generator: folder + seq docs + manifest, indexed in task.db."""

    # ---- create ----

    def new(
        self,
        title: str,
        command: str = "",
        session_id: str = "",
        context_id: str = "",
        task_id: Optional[str] = None,
    ) -> str:
        """
        Create a task folder (docs/task/<task_id>/) + manifest.json,
        and register a TSK_TASK row. Returns task_id.
        """
        task_id = task_id or f"task_{_short_id()}"
        folder = _base() / _TASK_ROOT_REL / task_id
        folder.mkdir(parents=True, exist_ok=True)

        manifest = {
            "task_id": task_id,
            "title": title,
            "status": tc.STATUS_PENDING,
            "command": command,
            "session_id": session_id,
            "context_id": context_id,
            "steps": [],
            "created_at": _now(),
            "updated_at": _now(),
        }
        self._write_manifest(folder, manifest)

        con = _connect()
        try:
            con.execute(
                "INSERT OR REPLACE INTO TSK_TASK "
                "(task_id,title,status,command,session_id,context_id,folder_path,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (task_id, title, tc.STATUS_PENDING, command, session_id, context_id,
                 str(folder), _now(), _now()),
            )
            con.commit()
        finally:
            con.close()
        return task_id

    def step(
        self,
        task_id: str,
        title: str,
        input: str = "",
        check_block: str = "",
    ) -> str:
        """
        Add a seq step: write NN_<slug>.md into the folder, register TSK_STEP row,
        and append to manifest. Returns step_id.
        One step = one self-contained instruction (TASK_INSTRUCTION_TEMPLATE).
        """
        folder = self._folder(task_id)
        seq = self._next_seq(task_id)
        slug = self._slug(title)
        fname = f"{seq:02d}_{slug}.md"
        fpath = folder / fname

        body = input if input else f"# {title}\n"
        fpath.write_text(body, encoding="utf-8")

        step_id = f"step_{_short_id()}"
        con = _connect()
        try:
            con.execute(
                "INSERT INTO TSK_STEP "
                "(step_id,task_id,seq,title,status,input_path,check_block,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (step_id, task_id, seq, title, tc.STATUS_PENDING,
                 str(fpath), check_block, _now(), _now()),
            )
            con.commit()
        finally:
            con.close()

        # mirror into manifest (folder self-describes even without DB)
        m = self._read_manifest(folder)
        m.setdefault("steps", []).append(
            {"step_id": step_id, "seq": seq, "title": title,
             "file": fname, "status": tc.STATUS_PENDING}
        )
        m["updated_at"] = _now()
        self._write_manifest(folder, m)
        return step_id

    # ---- query ----

    def list(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List tasks from task.db (optionally filter by status)."""
        con = _connect()
        try:
            if status:
                rows = con.execute(
                    "SELECT task_id,title,status,created_at FROM TSK_TASK "
                    "WHERE status=? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT task_id,title,status,created_at FROM TSK_TASK "
                    "ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()

    def show(self, task_id: str) -> Dict[str, Any]:
        """Return one task + its steps (from task.db)."""
        con = _connect()
        try:
            t = con.execute(
                "SELECT * FROM TSK_TASK WHERE task_id=?", (task_id,)
            ).fetchone()
            steps = con.execute(
                "SELECT seq,title,status,input_path FROM TSK_STEP "
                "WHERE task_id=? ORDER BY seq", (task_id,)
            ).fetchall()
            return {
                "task": dict(t) if t else None,
                "steps": [dict(s) for s in steps],
            }
        finally:
            con.close()

    # ---- state ----

    def set_status(self, task_id: str, status: str) -> bool:
        """Update task status in DB + manifest.

        Management / queue-routed use only: during execution the queue engine
        (uu.queue) owns status transitions (DESIGN §1 — single writer). An
        unknown status is surfaced (P1-3) rather than silently written.
        """
        if not tc.is_status(status):
            import sys
            print(f"[uu.task] WARN unknown status '{status}' "
                  f"not in sbi_task_const.STATUS {tc.STATUS}", file=sys.stderr)
        con = _connect()
        try:
            con.execute(
                "UPDATE TSK_TASK SET status=?, updated_at=? WHERE task_id=?",
                (status, _now(), task_id),
            )
            con.commit()
        finally:
            con.close()
        folder = self._folder(task_id)
        m = self._read_manifest(folder)
        m["status"] = status
        m["updated_at"] = _now()
        self._write_manifest(folder, m)
        return True

    def done(self, task_id: str) -> bool:
        """Freeze a task: status=done + write _DONE marker (asset)."""
        self.set_status(task_id, tc.STATUS_DONE)
        (self._folder(task_id) / "_DONE").write_text(_now(), encoding="utf-8")
        return True

    # ---- internals ----

    def _folder(self, task_id: str) -> Path:
        f = _base() / _TASK_ROOT_REL / task_id
        if not f.exists():
            raise FileNotFoundError(f"task folder not found: {f}")
        return f

    def _manifest_path(self, folder: Path) -> Path:
        return folder / "manifest.json"

    def _write_manifest(self, folder: Path, data: Dict[str, Any]) -> None:
        self._manifest_path(folder).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _read_manifest(self, folder: Path) -> Dict[str, Any]:
        p = self._manifest_path(folder)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return {"task_id": folder.name, "steps": []}

    def _next_seq(self, task_id: str) -> int:
        con = _connect()
        try:
            row = con.execute(
                "SELECT MAX(seq) AS m FROM TSK_STEP WHERE task_id=?", (task_id,)
            ).fetchone()
            return (row["m"] or 0) + 1
        finally:
            con.close()

    @staticmethod
    def _slug(title: str) -> str:
        keep = [c.lower() if c.isalnum() else "_" for c in title.strip()]
        s = "".join(keep).strip("_")
        while "__" in s:
            s = s.replace("__", "_")
        return (s or "step")[:40]


class UtilHandler:
    """uu — usekit utilities. Exposes the task store (uu.task) and, later,
    the queue engine (uu.queue, wired in step 2 / sbi_queue.py)."""

    def __init__(self):
        self.task = _TaskUtil()
        # Queue engine placeholder. uu.queue (the _QueueEngine in sbi_queue.py)
        # is wired in step 2 and will own all status transitions during run.
        # Left as None so the attribute resolves but any premature dispatch
        # fails loudly (AttributeError) instead of silently no-op'ing.
        self.queue = None

    def __repr__(self):
        wired = "queue" if self.queue is not None else "queue(pending)"
        return f"<UtilHandler uu [task | {wired}]>"


# module-level singleton (lazy-wrapped in use_support)
uu = UtilHandler()


# -----------------------------------------------------------------------------------------------
# [EOF]
# -----------------------------------------------------------------------------------------------
