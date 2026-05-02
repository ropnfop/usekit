# Path: usekit.classes.data.base.post.parser.parser_sql.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready SQL parser with multi-dialect variable binding support
# Features:
#   - Multi-dialect support: USEKIT($), SQLite(?), Oracle(:), MSSQL(@), psycopg(%)
#   - Smart parameter parsing: declarative strings, kwargs, dicts
#   - Type inference: auto-detect and convert types
#   - Safe execution: parameterized queries, SQL injection prevention
#   - File operations: load/dump SQL files
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
import sqlite3
from typing import Any, Union, Optional, List, Dict, Tuple

# Import all helper functions from sub module
from usekit.classes.common.fileops.helper_dotdict import DotDict
from usekit.classes.data.base.post.sub.parser_sql_sub import (
    SQL_STYLES,
    _detect_sql_style,
    _parse_param_string,
    _infer_type,
    _convert_to_usekit,
    _convert_from_usekit,
    _replace_variables,
    _merge_params,
    _handle_quoted_variables,
)

# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """Safe write: write to a temp file then atomically replace target."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """Convert to Path object if needed."""
    return file if isinstance(file, Path) else Path(file)


def _get_connection(db_path: Union[str, Path, sqlite3.Connection]) -> Tuple[sqlite3.Connection, bool]:
    """
    Get database connection.
    Returns (connection, should_close)
    """
    if isinstance(db_path, sqlite3.Connection):
        return db_path, False
    
    path = _ensure_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row  # Enable column access by name
    return conn, True


def _normalize_bind_args(args, params):
    """
    Normalize *args and params for SQL bind parameter passing.

    Handles two problems:
    1. Single tuple/list/dict in *args → redirect to params
    2. params itself double-wrapped: ((val1, val2),) → (val1, val2)

    Returns:
        (args, params) — normalized
    """
    # ── Step 1: args redirect (when params is not yet set)
    if params is None and len(args) == 1:
        first = args[0]
        if isinstance(first, dict):
            return (), first
        if isinstance(first, (tuple, list)):
            return (), first

    # ── Step 2: unwrap double-wrapped params
    #   params=( ("Alice","Seoul"), )  →  ("Alice","Seoul")
    #   params=( {"k":"v"},         )  →  {"k":"v"}
    #   params=( [1, 2, 3],         )  →  [1, 2, 3]
    if params is not None and isinstance(params, (tuple, list)):
        if len(params) == 1:
            inner = params[0]
            if isinstance(inner, (tuple, list, dict)):
                return args, inner

    return args, params


# ───────────────────────────────────────────────────────────────
# Execute / Query
# ───────────────────────────────────────────────────────────────

def execute(
    sql: str,
    db: Union[str, Path, sqlite3.Connection],
    *args,
    params: Optional[Union[Tuple, List, Dict]] = None,
    commit: bool = True,
    **kwargs
) -> int:
    """
    Execute DML statement with smart variable binding.
    
    Supports multiple parameter formats:
    - USEKIT style: execute("WHERE id=$id", db, id=123)
    - Param string: execute("WHERE id=$id", db, "$id: 123")
    - Traditional: execute("WHERE id=?", db, params=(123,))
    - Mixed: execute("WHERE id=$id", db, "$id: 123", id=456)  # id=456 wins
    
    Variable styles (auto-detected):
    - USEKIT: $variable
    - SQLite: ? (positional)
    - Oracle: :variable
    - MSSQL: @variable
    - psycopg: %(variable)s
    
    Args:
        sql: SQL statement (with variables)
        db: Database path or connection object
        *args: Positional param strings ("$name: value | $age: 20")
        params: Traditional params (tuple/list/dict)
        commit: Auto-commit after execution
        **kwargs: Variable values (name=value)
        
    Returns:
        Number of affected rows
        
    Examples:
        # USEKIT style
        execute("UPDATE users SET age=$age WHERE id=$id", db, age=25, id=1)
        
        # Param string
        execute("UPDATE users SET age=$age WHERE id=$id", db, "$age: 25 | $id: 1")
        
        # Traditional
        execute("UPDATE users SET age=? WHERE id=?", db, params=(25, 1))
        
        # Mixed
        execute("UPDATE users SET age=$age WHERE id=$id", db, "$age: 20", id=1)
    """
    # ── Normalize: single tuple/list/dict in *args → redirect to params
    args, params = _normalize_bind_args(args, params)

    conn, should_close = _get_connection(db)
    
    try:
        cursor = conn.cursor()
        
        # Handle quoted variables: '$var' → $var
        sql = _handle_quoted_variables(sql)
        
        # Detect SQL style
        style = _detect_sql_style(sql)
        
        # Convert to USEKIT standard if needed
        if style != 'usekit':
            sql = _convert_to_usekit(sql, style)
        
        # Merge parameters (args + kwargs)
        if args or kwargs:
            merged_params = _merge_params(*args, **kwargs)
            
            # Convert to SQLite format for execution
            sql_exec, params_exec = _convert_from_usekit(sql, merged_params, 'sqlite')
            
            cursor.execute(sql_exec, params_exec)
        elif params is not None:
            # Traditional params provided
            cursor.execute(sql, params)
        else:
            # No parameters
            cursor.execute(sql)
        
        affected = cursor.rowcount
        
        if commit:
            conn.commit()
        
        return affected
    
    finally:
        if should_close:
            conn.close()


def query(
    sql: str,
    db: Union[str, Path, sqlite3.Connection],
    *args,
    params: Optional[Union[Tuple, List, Dict]] = None,
    as_dict: bool = True,
    **kwargs
) -> List[Union[Dict, Tuple]]:
    """
    Execute SELECT query with smart variable binding.
    
    Supports same parameter formats as execute().
    
    Args:
        sql: SELECT statement (with variables)
        db: Database path or connection object
        *args: Positional param strings
        params: Traditional params (tuple/list/dict)
        as_dict: Return rows as dicts (True) or tuples (False)
        **kwargs: Variable values
        
    Returns:
        List of rows (dicts or tuples)
        
    Examples:
        # USEKIT style
        rows = query("SELECT * FROM users WHERE age > $min_age", db, min_age=20)
        
        # Param string
        rows = query("SELECT * FROM users WHERE age > $min_age", db, "$min_age: 20")
        
        # Traditional
        rows = query("SELECT * FROM users WHERE age > ?", db, params=(20,))
    """
    # ── Normalize: single tuple/list/dict in *args → redirect to params
    args, params = _normalize_bind_args(args, params)

    conn, should_close = _get_connection(db)
    
    try:
        cursor = conn.cursor()
        
        # Handle quoted variables
        sql = _handle_quoted_variables(sql)
        
        # Detect and convert SQL style
        style = _detect_sql_style(sql)
        if style != 'usekit':
            sql = _convert_to_usekit(sql, style)
        
        # Merge parameters
        if args or kwargs:
            merged_params = _merge_params(*args, **kwargs)
            sql_exec, params_exec = _convert_from_usekit(sql, merged_params, 'sqlite')
            cursor.execute(sql_exec, params_exec)
        elif params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        rows = cursor.fetchall()
        
        if as_dict:
            # return [dict(row) for row in rows]
            return [DotDict(dict(r)) for r in rows]    
        else:
            return [tuple(row) for row in rows]
    
    finally:
        if should_close:
            conn.close()


def execute_many(
    sql: str,
    db: Union[str, Path, sqlite3.Connection],
    params_list: List[Union[Tuple, Dict]],
    commit: bool = True,
    **kwargs
) -> int:
    """
    Execute DML statement multiple times with different parameters.
    
    Args:
        sql: SQL statement
        db: Database path or connection object
        params_list: List of parameter tuples/dicts
        commit: Auto-commit after execution
        **kwargs: Reserved for future use
        
    Returns:
        Total number of affected rows
    """
    conn, should_close = _get_connection(db)
    
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, params_list)
        
        affected = cursor.rowcount
        
        if commit:
            conn.commit()
        
        return affected
    
    finally:
        if should_close:
            conn.close()


def query_one(
    sql: str,
    db: Union[str, Path, sqlite3.Connection],
    *args,
    params: Optional[Union[Tuple, List, Dict]] = None,
    as_dict: bool = True,
    **kwargs
) -> Optional[Union[Dict, Tuple]]:
    """
    Execute SELECT query and return first row with smart variable binding.
    
    Args:
        sql: SELECT statement (with variables)
        db: Database path or connection object
        *args: Positional param strings
        params: Traditional params (tuple/list/dict)
        as_dict: Return row as dict (True) or tuple (False)
        **kwargs: Variable values
        
    Returns:
        First row or None
        
    Examples:
        # USEKIT style
        user = query_one("SELECT * FROM users WHERE id=$id", db, id=1)
        
        # Param string
        user = query_one("SELECT * FROM users WHERE id=$id", db, "$id: 1")
    """
    # ── Normalize: single tuple/list/dict in *args → redirect to params
    args, params = _normalize_bind_args(args, params)

    conn, should_close = _get_connection(db)
    
    try:
        cursor = conn.cursor()
        
        # Handle quoted variables
        sql = _handle_quoted_variables(sql)
        
        # Detect and convert SQL style
        style = _detect_sql_style(sql)
        if style != 'usekit':
            sql = _convert_to_usekit(sql, style)
        
        # Merge parameters
        if args or kwargs:
            merged_params = _merge_params(*args, **kwargs)
            sql_exec, params_exec = _convert_from_usekit(sql, merged_params, 'sqlite')
            cursor.execute(sql_exec, params_exec)
        elif params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        
        row = cursor.fetchone()
        
        if row is None:
            return None
        
        if as_dict:
            # return dict(row)
            return DotDict(dict(row))
        else:
            return tuple(row)
    
    finally:
        if should_close:
            conn.close()


# ───────────────────────────────────────────────────────────────
# Load / Dump (SQL file operations)
# ───────────────────────────────────────────────────────────────

def load(
    file,
    encoding: str = "utf-8",
    strip: bool = True,
    **kwargs
) -> str:
    """
    Read SQL from file.
    
    Args:
        file: File path (str/Path) or file-like object
        encoding: File encoding (ignored for file-like objects)
        strip: Strip whitespace
        **kwargs: Reserved for future use
        
    Returns:
        SQL string
    """
    # Handle file-like object (already opened)
    if hasattr(file, 'read'):
        sql = file.read()
    else:
        # Handle file path
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            sql = f.read()
    
    if strip:
        sql = sql.strip()
    
    return sql


def dump(
    sql: str,
    file,
    *,
    encoding: str = "utf-8",
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    append_newline: bool = True,
    **kwargs
) -> None:
    """
    Write SQL to file.
    
    Args:
        sql: SQL statement(s)
        file: File path or file-like object
        encoding: File encoding (ignored for file-like objects)
        overwrite: Allow overwriting
        safe: Use atomic write
        append: Append to existing file
        append_newline: Add newline when appending
        **kwargs: Reserved for future use
    """
    if not isinstance(sql, str):
        sql = str(sql)
    
    # Handle file-like object (e.g., StringIO)
    if hasattr(file, 'write'):
        file.write(sql)
        return
    
    # Handle file path
    path = _ensure_path(file)
    
    # ── Append mode
    if append:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding=encoding) as f:
            if append_newline and path.stat().st_size > 0:
                if not sql.startswith('\n'):
                    f.write('\n')
            f.write(sql)
        return
    
    # ── Normal write mode
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"[sql.dump] Target exists and overwrite=False: {path}"
        )
    
    if safe:
        _atomic_write_text(path, sql, encoding=encoding)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding=encoding) as f:
            f.write(sql)


def dumps(
    sql: str,
    **kwargs
) -> str:
    """
    Serialize SQL to string (identity function for SQL).
    
    Args:
        sql: SQL statement(s)
        **kwargs: Reserved for future use
        
    Returns:
        SQL string
    """
    return str(sql) if not isinstance(sql, str) else sql


# ───────────────────────────────────────────────────────────────
# Transaction helpers
# ───────────────────────────────────────────────────────────────

class Transaction:
    """Context manager for database transactions."""
    
    def __init__(self, db: Union[str, Path, sqlite3.Connection]):
        self.db = db
        self.conn = None
        self.should_close = False
    
    def __enter__(self) -> sqlite3.Connection:
        self.conn, self.should_close = _get_connection(self.db)
        return self.conn
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        
        if self.should_close:
            self.conn.close()


def transaction(db: Union[str, Path, sqlite3.Connection]) -> Transaction:
    """
    Create a transaction context manager.
    
    Usage:
        with transaction("db.sqlite") as conn:
            execute("INSERT ...", conn)
            execute("UPDATE ...", conn)
    """
    return Transaction(db)


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(db_path="test.db"):
    """Test DML parser functionality."""
    
    # Clean start
    path = Path(db_path)
    if path.exists():
        path.unlink()
    
    # Create test table (using DDL)
    execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER,
            city TEXT
        )
    """, db_path)
    print("[DML] created table")
    
    # INSERT single row
    affected = execute(
        "INSERT INTO users (name, age, city) VALUES (?, ?, ?)",
        db_path,
        ("Alice", 30, "Seoul")
    )
    print(f"[DML] inserted {affected} row(s)")
    
    # INSERT multiple rows
    users_data = [
        ("Bob", 25, "Busan"),
        ("Charlie", 35, "Jeju"),
        ("Diana", 28, "Incheon")
    ]
    affected = execute_many(
        "INSERT INTO users (name, age, city) VALUES (?, ?, ?)",
        db_path,
        users_data
    )
    print(f"[DML] inserted {affected} row(s)")
    
    # SELECT all
    rows = query("SELECT * FROM users", db_path)
    print("[DML] all users:", rows)
    
    # SELECT with WHERE
    rows = query(
        "SELECT * FROM users WHERE age > ?",
        db_path,
        (27,)
    )
    print("[DML] users age > 27:", rows)
    
    # SELECT one
    user = query_one(
        "SELECT * FROM users WHERE name = ?",
        db_path,
        ("Alice",)
    )
    print("[DML] found user:", user)
    
    # UPDATE
    affected = execute(
        "UPDATE users SET age = ? WHERE name = ?",
        db_path,
        (31, "Alice")
    )
    print(f"[DML] updated {affected} row(s)")
    
    # Verify update
    user = query_one("SELECT * FROM users WHERE name = 'Alice'", db_path)
    print("[DML] after update:", user)
    
    # Transaction test
    print("[DML] testing transaction...")
    try:
        with transaction(db_path) as conn:
            execute("UPDATE users SET age = age + 1", conn, commit=False)
            execute("INSERT INTO users (name, age, city) VALUES (?, ?, ?)", 
                   conn, ("Eve", 22, "Daegu"), commit=False)
            # Auto-commits on successful exit
        print("[DML] transaction committed")
    except Exception as e:
        print(f"[DML] transaction rolled back: {e}")
    
    # Final count
    result = query_one("SELECT COUNT(*) as count FROM users", db_path)
    print(f"[DML] total users: {result['count']}")
    
    # DELETE
    affected = execute("DELETE FROM users WHERE age < ?", db_path, (26,))
    print(f"[DML] deleted {affected} row(s)")
    
    # Save SQL to file
    sql_content = """
-- User queries
SELECT * FROM users WHERE city = 'Seoul';
SELECT AVG(age) as avg_age FROM users;
"""
    dump(sql_content, "queries.sql")
    print("[DML] saved SQL to file")
    
    # Load and execute
    loaded_sql = load("queries.sql")
    print("[DML] loaded SQL:", loaded_sql[:50] + "...")

# ───────────────────────────────────────────────────────────────
# Export
# ───────────────────────────────────────────────────────────────

__all__ = [
    # Main functions
    "execute",
    "query",
    "execute_many",
    "query_one",
    "load",
    "dump",
    "dumps",
    "transaction",
    "Transaction",
    # Constants from sub module
    "SQL_STYLES",
]

# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------