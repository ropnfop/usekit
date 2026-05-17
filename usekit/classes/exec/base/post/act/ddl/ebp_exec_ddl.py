# Path: usekit.classes.exec.base.post.act.ddl.ebp_exec_ddl.py
# -----------------------------------------------------------------------------------------------
#  DDL Executor POST Layer - with Auto-Save
#  Created by: THE Little Prince × ROP × FOP
#
#  Interface:
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  exec_ddl(ddl_or_path, db=None, auto_save=True, safe=True, debug=False)
#  
#  Key Feature: Auto-save raw DDL to schema files
#  - Raw DDL → save to @/ddl/base/{table}.sql + execute
#  - File path → load + execute (no save)
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Based on: ebp_exec_sql.py
#  Key difference: Auto-save feature for schema management
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional, List, Union

from usekit.classes.common.errors.helper_debug import log_and_raise


@log_and_raise
def exec_ddl(
    ddl_or_path: Union[str, Path],
    *,
    db: Optional[Any] = None,
    auto_save: bool = True,
    safe: bool = True,
    debug: bool = False
) -> List[Any]:
    """
    Execute DDL with auto-save for raw DDL.
    
    Interface Design:
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    exec_ddl(ddl_or_path, db=None, auto_save=True, safe=True, debug=False)
    
    Auto-Save Logic:
        - Raw DDL + auto_save=True → Save to schema file first
        - File path → Load and execute (no save)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Args:
        ddl_or_path: DDL text or file pattern/path
            - Raw DDL: "CREATE TABLE users (id INT, name TEXT)"
            - File pattern: "users"
            - File path: "schema/users.sql"
            
        db: Database connection (optional if DB_PATH configured)
            - Path string: "data/my.db"
            - Path object: Path("data/my.db")
            - Connection: sqlite3.Connection object
            - None: Use default from sys_const.yaml
            
        auto_save: Auto-save raw DDL to schema file
            - True: Save raw DDL before execution
            - False: Execute only (no save)
            
        safe: Safe execution mode (reserved for future)
        
        debug: Enable debug output
            
    Returns:
        List of results:
        - DDL: [Row(affected=0)]  # Schema change, no rows
        - Empty: []
        
    Examples:
        # Method 1: Raw DDL with auto-save (default)
        >>> exec_ddl("CREATE TABLE users (id INT, name TEXT);", db=conn)
        # → Saves to users.sql + creates table
        [Row(affected=0)]
        
        # Method 2: File pattern (no save)
        >>> exec_ddl("users", db=conn)
        # → Loads users.sql + creates table
        [Row(affected=0)]
        
        # Method 3: Raw DDL without save
        >>> exec_ddl(
        ...     "CREATE TABLE temp (id INT);",
        ...     db=conn,
        ...     auto_save=False
        ... )
        # → Creates table only (no file)
        
        # Method 4: Complex DDL with auto-save
        >>> ddl = '''
        ... CREATE TABLE orders (
        ...     id INTEGER PRIMARY KEY,
        ...     user_id INTEGER,
        ...     total REAL,
        ...     FOREIGN KEY (user_id) REFERENCES users(id)
        ... );
        ... '''
        >>> exec_ddl(ddl, db=conn)
        # → Saves to orders.sql + creates table
    """
    
    if debug:
        print(f"[DDL-POST] ddl_or_path: {ddl_or_path}")
        print(f"[DDL-POST] db: {db}")
        print(f"[DDL-POST] auto_save: {auto_save}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DDL Loading
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Determine if inline DDL or file
    ddl_text = str(ddl_or_path)
    is_inline = _is_inline_ddl(ddl_text)
    
    if is_inline:
        # Inline DDL
        final_ddl = ddl_text
        if debug:
            print(f"[DDL-POST] Inline DDL detected")
            print(f"[DDL-POST] DDL preview: {final_ddl[:80]}...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [AUTO-SAVE] Save raw DDL to schema file
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if auto_save:
            if debug:
                print(f"[DDL-POST] Auto-saving DDL to schema file...")
            
            try:
                # Use USEKIT's write DDL function (u.wdb)
                # This handles table name extraction and backup automatically
                from usekit.classes.data.base.load.ops.dbl_write import write_operation
                
                result_path = write_operation(
                    fmt="ddl",
                    data=final_ddl,
                    name=None,  # Auto-extract table name
                    loc="base",
                    debug=debug
                )
                
                if debug and result_path:
                    print(f"[DDL-POST] Schema saved to: {result_path}")
            except Exception as e:
                if debug:
                    print(f"[DDL-POST] Warning: Failed to save schema: {e}")
                # Continue execution even if save fails
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    else:
        # File - load DDL
        if debug:
            print(f"[DDL-POST] File pattern detected: {ddl_text}")
        
        from usekit.classes.data.base.post.parser.parser_sql import load
        
        try:
            final_ddl = load(ddl_text)
            if debug:
                print(f"[DDL-POST] Loaded DDL from file: {ddl_text}")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"DDL file not found: '{ddl_text}'\n"
                f"Tried to load as file path. "
                f"For pattern-based search, use LOAD layer (ebl_exec_ddl)."
            )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Database Connection
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    if db is None:
        # Try to get default DB from sys_const.yaml
        try:
            from usekit.classes.common.utils.helper_const import get_const, get_base_path
            db_root = get_const("DB_PATH.root")
            db_file = get_const("DB_PATH.db")
            db = get_base_path() / db_root / db_file
            
            if debug:
                print(f"[DDL-POST] Using default DB: {db}")
        except (KeyError, FileNotFoundError):
            raise ValueError(
                "Database connection required: pass 'db' parameter or "
                "configure DB_PATH in sys_const.yaml"
            )
    
    if debug:
        print(f"[DDL-POST] Final DB: {db}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DDL Execution
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    from usekit.classes.data.base.post.parser.parser_sql import execute
    
    if debug:
        print(f"[DDL-POST] Executing DDL...")
    
    # Execute DDL (CREATE/ALTER/DROP/TRUNCATE)
    # DDL statements don't return rows, just affected count (usually 0)
    affected = execute(
        sql=final_ddl,
        db=db,
        commit=True
    )
    
    if debug:
        print(f"[DDL-POST] DDL executed: {affected} affected")
    
    return [Row(affected=affected)]


def _is_inline_ddl(text: str) -> bool:
    """
    Detect if text is inline DDL or file pattern.
    
    Inline DDL starts with DDL keywords.
    Everything else is treated as file pattern/path.
    """
    ddl_keywords = (
        'CREATE', 'ALTER', 'DROP', 'TRUNCATE'
    )
    
    text_upper = text.strip().upper()
    return any(text_upper.startswith(kw) for kw in ddl_keywords)


# Row class for DDL results
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Row:
    """
    DDL result with attribute/dict access.
    
    Examples:
        >>> row = Row(affected=0)
        >>> row.affected
        0
        >>> row['affected']
        0
    """
    
    def __init__(self, **kwargs):
        self._data = kwargs
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"Row has no attribute '{name}'")
    
    def __getitem__(self, key):
        return self._data[key]
    
    def __iter__(self):
        return iter(self._data.values())
    
    def __len__(self):
        return len(self._data)
    
    def __repr__(self):
        items = ', '.join(f"{k}={v!r}" for k, v in self._data.items())
        return f"Row({items})"
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()
    
    def to_dict(self):
        return self._data.copy()


# ===============================================================================
# Exports
# ===============================================================================

__all__ = [
    "exec_ddl",
    "Row",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
