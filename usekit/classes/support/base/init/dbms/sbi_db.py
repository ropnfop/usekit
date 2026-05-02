# Path: usekit.classes.support.base.init.dbms.sbi_db.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince, in harmony with ROP and FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from functools import lru_cache

# Type aliases
Params = Union[Tuple, List, Dict]
Row = Tuple[Any, ...]
Rows = List[Row]


@lru_cache(maxsize=1)
def _get_default_db_path() -> Path:
    """Get default database path from sys_const.yaml."""
    try:
        from usekit.classes.common.utils.helper_path import inner_abs_db_path
        return Path(inner_abs_db_path("db"))
    except Exception:
        # Fallback to current directory
        return Path("./usekit.db")


class DBHandler:
    """
    Practical SQLite utilities for usekit.
    
    Features:
        - Connection management with context managers
        - Query execution with parameter binding
        - Transaction support (commit/rollback)
        - Row factory options (tuple/dict/custom)
        - Safe execution with error handling
    
    Examples:
        # Quick query
        >>> ud = DBHandler()
        >>> rows = ud.query("SELECT * FROM users WHERE age > ?", (18,))
        
        # Context manager (auto-commit)
        >>> with ud.connect() as conn:
        ...     ud.execute("INSERT INTO users VALUES (?, ?)", ("Alice", 30))
        ...     results = ud.query("SELECT * FROM users")
        
        # Transaction control
        >>> with ud.transaction() as conn:
        ...     ud.execute("UPDATE users SET age = age + 1")
        ...     # Auto-commit on success, rollback on error
        
        # Dictionary rows
        >>> ud.set_row_factory("dict")
        >>> rows = ud.query("SELECT * FROM users")
        >>> print(rows[0]["name"])
    """
    
    def __init__(self, db_path: Optional[Union[str, Path]] = None):
        """
        Initialize DBHandler.
        
        Parameters:
            db_path: Database file path (None = use sys_const default)
        """
        self.db_path = Path(db_path) if db_path else _get_default_db_path()
        self._conn: Optional[sqlite3.Connection] = None
        self._cursor: Optional[sqlite3.Cursor] = None
        self._row_factory = None
        self._in_context = False
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    def open(self, db_path: Optional[Union[str, Path]] = None) -> sqlite3.Connection:
        """
        Open database connection.
        
        Parameters:
            db_path: Override default database path
        
        Returns:
            Connection object
        """
        if db_path:
            self.db_path = Path(db_path)
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(str(self.db_path))
        
        # Apply row factory if set
        if self._row_factory:
            self._conn.row_factory = self._row_factory
        
        self._cursor = self._conn.cursor()
        return self._conn
    
    def close(self):
        """Close database connection and cursor."""
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def is_open(self) -> bool:
        """Check if connection is open."""
        return self._conn is not None and self._cursor is not None
    
    @contextmanager
    def connect(self, db_path: Optional[Union[str, Path]] = None) -> Iterator[sqlite3.Connection]:
        """
        Context manager for database connection (auto-commit on exit).
        
        Examples:
            >>> with ud.connect() as conn:
            ...     ud.execute("INSERT INTO users VALUES (?, ?)", ("Bob", 25))
        """
        self._in_context = True
        try:
            conn = self.open(db_path)
            yield conn
            conn.commit()
        except Exception:
            if self._conn:
                self._conn.rollback()
            raise
        finally:
            self.close()
            self._in_context = False
    
    @contextmanager
    def transaction(self, db_path: Optional[Union[str, Path]] = None) -> Iterator[sqlite3.Connection]:
        """
        Context manager for explicit transaction (auto-commit/rollback).
        
        Examples:
            >>> with ud.transaction():
            ...     ud.execute("UPDATE users SET active = 1")
            ...     ud.execute("DELETE FROM logs WHERE old = 1")
        """
        self._in_context = True
        try:
            conn = self.open(db_path)
            yield conn
            conn.commit()
        except Exception:
            if self._conn:
                self._conn.rollback()
            raise
        finally:
            self.close()
            self._in_context = False
    
    # ========================================================================
    # Query Execution
    # ========================================================================
    
    def execute(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        commit: bool = False
    ) -> sqlite3.Cursor:
        """
        Execute SQL statement.
        
        Parameters:
            sql: SQL statement
            params: Parameters for placeholders (tuple/list/dict)
            commit: Auto-commit after execution
        
        Returns:
            Cursor object
        
        Examples:
            >>> ud.execute("CREATE TABLE users (name TEXT, age INT)")
            >>> ud.execute("INSERT INTO users VALUES (?, ?)", ("Alice", 30))
            >>> ud.execute("UPDATE users SET age = :age WHERE name = :name",
            ...            {"name": "Alice", "age": 31})
        """
        if not self.is_open():
            raise RuntimeError("Database not connected. Use open() or connect() context.")
        
        if params is None:
            self._cursor.execute(sql)
        else:
            self._cursor.execute(sql, params)
        
        if commit and self._conn:
            self._conn.commit()
        
        return self._cursor
    
    def execute_many(
        self,
        sql: str,
        params_list: List[Params],
        *,
        commit: bool = False
    ) -> sqlite3.Cursor:
        """
        Execute SQL with multiple parameter sets.
        
        Examples:
            >>> users = [("Alice", 30), ("Bob", 25), ("Charlie", 35)]
            >>> ud.execute_many("INSERT INTO users VALUES (?, ?)", users)
        """
        if not self.is_open():
            raise RuntimeError("Database not connected. Use open() or connect() context.")
        
        self._cursor.executemany(sql, params_list)
        
        if commit and self._conn:
            self._conn.commit()
        
        return self._cursor
    
    def query(
        self,
        sql: str,
        params: Optional[Params] = None,
        *,
        one: bool = False
    ) -> Union[Row, Rows, Dict, List[Dict], None]:
        """
        Execute SELECT query and fetch results.
        
        Parameters:
            sql: SELECT statement
            params: Parameters for placeholders
            one: Return single row (fetchone) vs all rows (fetchall)
        
        Returns:
            Rows as tuples or dicts (depends on row_factory)
        
        Examples:
            >>> rows = ud.query("SELECT * FROM users WHERE age > ?", (18,))
            >>> user = ud.query("SELECT * FROM users WHERE id = ?", (1,), one=True)
        """
        self.execute(sql, params)
        return self._cursor.fetchone() if one else self._cursor.fetchall()
    
    def script(self, sql_script: str):
        """
        Execute SQL script (multiple statements).
        
        Examples:
            >>> ud.script('''
            ...     CREATE TABLE users (id INT, name TEXT);
            ...     CREATE TABLE logs (msg TEXT, ts INT);
            ... ''')
        """
        if not self.is_open():
            raise RuntimeError("Database not connected. Use open() or connect() context.")
        
        self._cursor.executescript(sql_script)
    
    # ========================================================================
    # Fetch Methods
    # ========================================================================
    
    def fetchone(self) -> Optional[Union[Row, Dict]]:
        """Fetch one row from last query."""
        if not self._cursor:
            return None
        return self._cursor.fetchone()
    
    def fetchall(self) -> Union[Rows, List[Dict]]:
        """Fetch all rows from last query."""
        if not self._cursor:
            return []
        return self._cursor.fetchall()
    
    def fetchmany(self, size: int = 1) -> Union[Rows, List[Dict]]:
        """Fetch specified number of rows."""
        if not self._cursor:
            return []
        return self._cursor.fetchmany(size)
    
    # ========================================================================
    # Transaction Control
    # ========================================================================
    
    def commit(self):
        """Commit current transaction."""
        if self._conn:
            self._conn.commit()
    
    def rollback(self):
        """Rollback current transaction."""
        if self._conn:
            self._conn.rollback()
    
    # ========================================================================
    # Row Factory
    # ========================================================================
    
    def set_row_factory(self, mode: Optional[str] = None):
        """
        Set row factory for query results.
        
        Parameters:
            mode: "dict" for dictionary rows, None for tuples
        
        Examples:
            >>> ud.set_row_factory("dict")
            >>> rows = ud.query("SELECT * FROM users")
            >>> print(rows[0]["name"])
        """
        if mode == "dict":
            self._row_factory = sqlite3.Row
        else:
            self._row_factory = None
        
        # Apply to existing connection
        if self._conn:
            self._conn.row_factory = self._row_factory
    
    # ========================================================================
    # Utility Methods
    # ========================================================================
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        result = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
            one=True
        )
        return result is not None
    
    def tables(self) -> List[str]:
        """List all tables in database."""
        rows = self.query(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        return [row[0] for row in rows]
    
    def columns(self, table_name: str) -> List[str]:
        """Get column names for a table."""
        result = self.query(f"PRAGMA table_info({table_name})")
        return [row[1] for row in result]
    
    def count(self, table_name: str) -> int:
        """Count rows in a table."""
        result = self.query(f"SELECT COUNT(*) FROM {table_name}", one=True)
        return result[0] if result else 0
    
    def vacuum(self):
        """Optimize database (reclaim space)."""
        if self.is_open():
            self._conn.execute("VACUUM")
    
    # ========================================================================
    # Quick CRUD helpers
    # ========================================================================
    
    def insert(self, table: str, data: Dict[str, Any], *, commit: bool = True) -> int:
        """
        Insert row into table.
        
        Examples:
            >>> ud.insert("users", {"name": "Alice", "age": 30})
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?"] * len(data))
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        self.execute(sql, tuple(data.values()), commit=commit)
        return self._cursor.lastrowid if self._cursor else 0
    
    def update(
        self,
        table: str,
        data: Dict[str, Any],
        where: str,
        params: Optional[Params] = None,
        *,
        commit: bool = True
    ) -> int:
        """
        Update rows in table.
        
        Examples:
            >>> ud.update("users", {"age": 31}, "name = ?", ("Alice",))
        """
        set_clause = ", ".join(f"{k} = ?" for k in data.keys())
        sql = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        all_params = tuple(data.values()) + (params or ())
        self.execute(sql, all_params, commit=commit)
        return self._cursor.rowcount if self._cursor else 0
    
    def delete(
        self,
        table: str,
        where: str,
        params: Optional[Params] = None,
        *,
        commit: bool = True
    ) -> int:
        """
        Delete rows from table.
        
        Examples:
            >>> ud.delete("users", "age < ?", (18,))
        """
        sql = f"DELETE FROM {table} WHERE {where}"
        self.execute(sql, params, commit=commit)
        return self._cursor.rowcount if self._cursor else 0
    
    def select(
        self,
        table: str,
        columns: str = "*",
        where: Optional[str] = None,
        params: Optional[Params] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> Union[Rows, List[Dict]]:
        """
        Select rows from table.
        
        Examples:
            >>> ud.select("users", where="age > ?", params=(18,), order_by="name")
        """
        sql = f"SELECT {columns} FROM {table}"
        
        if where:
            sql += f" WHERE {where}"
        if order_by:
            sql += f" ORDER BY {order_by}"
        if limit:
            sql += f" LIMIT {limit}"
        
        return self.query(sql, params)


# ========================================================================
# Singleton instance
# ========================================================================

# ud: uses sys_const.yaml DB.default_path (or ./usekit.db)
ud = DBHandler()

__all__ = ["DBHandler", "ud"]
