# Path: usekit.classes.support.base.init.dbms.sbi_db.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import sqlite3
from collections import namedtuple
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union


def _row_factory(cursor, row):
    fields = [d[0] for d in cursor.description]
    Row = namedtuple("Row", fields)
    return Row(*row)


class DBHandler:
    """
    SQLite3 database utility.

    conn → exec / fetch / one → close
    tx() 로 트랜잭션 관리.

    Examples:
        ud.conn("data/table/db/base.db")
        ud.exec("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, name TEXT)")
        ud.exec("INSERT INTO t VALUES (?, ?)", 1, "Alice", commit=True)
        rows = ud.fetch("SELECT * FROM t")
        row  = ud.one("SELECT * FROM t WHERE id = ?", 1)
        print(row.name)
        ud.close()

        with ud.tx("data/table/db/base.db"):
            ud.exec("INSERT INTO t VALUES (?, ?)", 2, "Bob")
    """

    def __init__(self):
        self._conn: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None

    # ── connection ─────────────────────────────────────────────────────────

    def conn(self, path: Union[str, Path]) -> "DBHandler":
        """Open database connection. Returns self for chaining."""
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(p))
        self._conn.row_factory = _row_factory
        self._cursor = self._conn.cursor()
        return self

    def close(self):
        """Close database connection."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._conn:
            self._conn.close()
            self._conn = None

    def is_open(self) -> bool:
        """Return True if connection is open."""
        return self._conn is not None

    @contextmanager
    def tx(self, path: Optional[Union[str, Path]] = None) -> Iterator["DBHandler"]:
        """
        Transaction context — auto commit on success, rollback on error.

        with ud.tx("data/table/db/base.db"):   # opens + closes
            ud.exec(...)

        with ud.tx():                           # uses existing conn
            ud.exec(...)
        """
        opened_here = False
        if path:
            self.conn(path)
            opened_here = True
        try:
            yield self
            if self._conn:
                self._conn.commit()
        except Exception:
            if self._conn:
                self._conn.rollback()
            raise
        finally:
            if opened_here:
                self.close()

    # ── execution ──────────────────────────────────────────────────────────

    def _resolve_params(self, args):
        """Normalize *args into sqlite3-compatible params."""
        if not args:
            return None
        if len(args) == 1 and isinstance(args[0], (tuple, list, dict)):
            return args[0]
        return args

    def exec(self, sql: str, *args, commit: bool = False) -> sqlite3.Cursor:
        """
        Execute DML/DDL statement.

        ud.exec("INSERT INTO t VALUES (?, ?)", 1, "Alice")
        ud.exec("INSERT INTO t VALUES (?, ?)", (1, "Alice"))
        ud.exec("UPDATE t SET name=:n WHERE id=:id", {"n": "Bob", "id": 1})
        ud.exec("DELETE FROM t WHERE id = ?", 1, commit=True)
        """
        if not self.is_open():
            raise RuntimeError("Not connected. Call ud.conn(path) first.")
        params = self._resolve_params(args)
        if params is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, params)
        if commit and self._conn:
            self._conn.commit()
        return self._cursor

    def fetch(self, sql: str, *args) -> list:
        """
        Execute SELECT and return all rows.
        Row supports attribute access: row.col

        rows = ud.fetch("SELECT * FROM t WHERE age > ?", 20)
        for row in rows:
            print(row.id, row.name)
        """
        self.exec(sql, *args)
        return self._cursor.fetchall()

    def one(self, sql: str, *args):
        """
        Execute SELECT and return first row or None.

        row = ud.one("SELECT * FROM t WHERE id = ?", 1)
        if row:
            print(row.name)
        """
        self.exec(sql, *args)
        return self._cursor.fetchone()

    def many(self, sql: str, params_list: list, *, commit: bool = False) -> sqlite3.Cursor:
        """
        Execute DML with multiple parameter sets (batch).

        ud.many("INSERT INTO t VALUES (?, ?)", [(1, "A"), (2, "B")], commit=True)
        """
        if not self.is_open():
            raise RuntimeError("Not connected. Call ud.conn(path) first.")
        self._cursor.executemany(sql, params_list)
        if commit and self._conn:
            self._conn.commit()
        return self._cursor

    def script(self, sql_script: str):
        """Execute SQL script (multiple statements separated by semicolons)."""
        if not self.is_open():
            raise RuntimeError("Not connected. Call ud.conn(path) first.")
        self._conn.executescript(sql_script)

    # ── transaction control ────────────────────────────────────────────────

    def commit(self):
        """Commit current transaction."""
        if self._conn:
            self._conn.commit()

    def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            self._conn.rollback()

    # ── CRUD helpers ───────────────────────────────────────────────────────

    def insert(self, table: str, data: Dict[str, Any], *, commit: bool = True) -> int:
        """
        Insert a row. Returns lastrowid.

        ud.insert("users", {"name": "Alice", "age": 30})
        """
        cols = ", ".join(data.keys())
        ph = ", ".join(["?"] * len(data))
        self.exec(f"INSERT INTO {table} ({cols}) VALUES ({ph})", tuple(data.values()), commit=commit)
        return self._cursor.lastrowid or 0

    def update(self, table: str, data: Dict[str, Any], where: str,
               params: Optional[Union[tuple, list]] = None, *, commit: bool = True) -> int:
        """
        Update rows. Returns rowcount.

        ud.update("users", {"age": 31}, "name = ?", ("Alice",))
        """
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        all_params = tuple(data.values()) + tuple(params or ())
        self.exec(sql, all_params, commit=commit)
        return self._cursor.rowcount or 0

    def delete(self, table: str, where: str,
               params: Optional[Union[tuple, list]] = None, *, commit: bool = True) -> int:
        """
        Delete rows. Returns rowcount.

        ud.delete("users", "age < ?", (18,))
        """
        self.exec(f"DELETE FROM {table} WHERE {where}", params or (), commit=commit)
        return self._cursor.rowcount or 0

    def select(self, table: str, cols: str = "*", where: Optional[str] = None,
               params: Optional[Union[tuple, list]] = None, *,
               order: Optional[str] = None, limit: Optional[int] = None) -> list:
        """
        Select rows from table.

        ud.select("users", where="age > ?", params=(18,), order="name", limit=10)
        """
        sql = f"SELECT {cols} FROM {table}"
        if where:
            sql += f" WHERE {where}"
        if order:
            sql += f" ORDER BY {order}"
        if limit:
            sql += f" LIMIT {limit}"
        return self.fetch(sql, *(params or ()))

    # ── utilities ──────────────────────────────────────────────────────────

    def tables(self) -> List[str]:
        """List all table names in the database."""
        rows = self.fetch("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [r.name for r in rows]

    def cols(self, table: str) -> List[str]:
        """List column names for a table."""
        rows = self.fetch(f"PRAGMA table_info({table})")
        return [r.name for r in rows]

    def has(self, table: str) -> bool:
        """Return True if table exists."""
        r = self.one("SELECT name FROM sqlite_master WHERE type='table' AND name=?", table)
        return r is not None

    def count(self, table: str) -> int:
        """Return row count for a table."""
        r = self.one(f"SELECT COUNT(*) AS n FROM {table}")
        return r.n if r else 0

    def vacuum(self):
        """Run VACUUM to reclaim disk space."""
        if self._conn:
            self._conn.execute("VACUUM")


# ── Singleton instance ─────────────────────────────────────────────────────

ud = DBHandler()

__all__ = ["DBHandler", "ud"]
