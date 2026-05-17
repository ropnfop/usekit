# Path: usekit.classes.data.base.post.parser.parser_ddl.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Production-ready SQL DDL/DML parser and generator (REFACTORED)
# Pattern: Small → Big (data → name → dir → options)
# Changes:
#   - Smart file naming: auto-extract table name when file=None
#   - Auto-backup: backup existing file before overwrite
#   - Dump mode: return SQL string only when no table name extractable
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Union, Optional, Dict, List

# Import helper functions from sub module
try:
    from usekit.classes.data.base.post.sub.parser_ddl_sub import (
        _atomic_write_text,
        _ensure_path,
        _wrap_if_needed,
        _escape_sql_value,
        _parse_sql_type,
        _normalize_column_name,
        _extract_table_name,
        _generate_create_table,
        _generate_insert,
        _infer_schema_from_data,
    )
    from usekit.classes.data.base.post.sub.ddl.auto_name import (
        extract_table_name_from_ddl,
        backup_existing_file,
    )
except ModuleNotFoundError:
    # For standalone testing
    from parser_ddl_sub import (
        _atomic_write_text,
        _ensure_path,
        _wrap_if_needed,
        _escape_sql_value,
        _parse_sql_type,
        _normalize_column_name,
        _extract_table_name,
        _generate_create_table,
        _generate_insert,
        _infer_schema_from_data,
    )
    from auto_name import (
        extract_table_name_from_ddl,
        backup_existing_file,
    )


# ===============================================================================
# Load / Loads (Parse SQL statements)
# ===============================================================================

def load(
    file,
    encoding: str = "utf-8",
    **kwargs
) -> Dict[str, Any]:
    """
    Read SQL from a file.
    
    Returns:
        {
            "statements": [...],  # List of SQL statements
            "raw": "...",         # Raw SQL text
            "count": n            # Statement count
        }
    
    Args:
        file: File path or file-like object
        encoding: Text encoding
        **kwargs: Additional arguments passed to loads()
    """
    if isinstance(file, (str, Path)):
        path = _ensure_path(file)
        with path.open("r", encoding=encoding) as f:
            text = f.read()
    else:
        text = file.read()
    
    return loads(text, **kwargs)


def loads(text: str, **kwargs) -> Dict[str, Any]:
    """
    Parse SQL from string.
    
    Process:
    1. Remove SQL comments (-- and /* */)
    2. Clean whitespace
    3. Split on semicolons
    4. Return structured data
    
    Args:
        text: SQL text to parse
        **kwargs: Reserved for future options
        
    Returns:
        Dict with statements, raw text, and count
    """
    lines = []
    for line in text.splitlines():
        # Remove single-line comments
        if '--' in line:
            line = line[:line.index('--')]
        line = line.strip()
        if line:
            lines.append(line)
    
    cleaned = ' '.join(lines)
    statements = [s.strip() for s in cleaned.split(';') if s.strip()]
    
    return {
        "statements": statements,
        "raw": text,
        "count": len(statements)
    }


# ===============================================================================
# Dump / Dumps (Generate SQL)
# Pattern: data → file → options
# ===============================================================================

def dump(
    data: Any,
    file=None,
    *,
    # Options (sorted by importance)
    mode: str = "auto",           # 'auto' | 'create' | 'insert' | 'full'
    primary_key: Optional[str] = None,
    batch_insert: bool = True,
    if_not_exists: bool = True,
    # DDL-specific options
    auto_backup: bool = True,     # Auto-backup existing file before overwrite
    base_dir: Optional[Path] = None,  # Base directory for file operations
    # File handling
    encoding: str = "utf-8",
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    debug: bool = False,
    **kwargs
) -> Optional[str]:
    """
    Write SQL to file or return as string.
    
    REFACTORED: Smart file naming for DDL
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - file provided → use it (with auto-backup)
    - file=None → try to extract table name from data
      ├─ table name found → create file with table name (auto-backup)
      └─ table name NOT found → dump mode (return SQL string)
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    Pattern: Small → Big
        data      (smallest - the content)
        file      (medium - where to save, optional for dumps)
        options   (largest - how to process)
    
    Usage:
        # [1] Explicit filename (traditional)
        dump(data, "users.sql")
        dump(data, "users.sql", mode="full", primary_key="id")
        
        # [2] Auto table name extraction (NEW)
        dump("CREATE TABLE users (id INT);")  # → users.sql
        dump({"table": "products", "records": [...]})  # → products.sql
        
        # [3] Dump mode (no file, no extractable table name)
        sql_str = dump([{"id": 1}])  # No table name → return SQL string
        
        # [4] Disable auto-backup
        dump(data, "users.sql", auto_backup=False)
        
        # [5] Custom base directory
        dump(data, base_dir=Path("/custom/path"))  # → /custom/path/users.sql
    
    Modes:
        'auto'   : Detect from data structure
        'create' : Generate CREATE TABLE only
        'insert' : Generate INSERT statements only
        'full'   : Generate both CREATE TABLE and INSERT
    
    Data Formats:
        # List of records (auto-infer schema)
        [{"id": 1, "name": "Alice"}, ...]
        
        # Dict with table name
        {"table": "users", "records": [...]}
        
        # Dict with explicit schema
        {
            "table": "users",
            "schema": {"id": "INTEGER", "name": "VARCHAR(50)"},
            "records": [...]
        }
        
        # Raw SQL string
        "CREATE TABLE users (id INT, name TEXT);"
    
    Args:
        data: Data to convert to SQL (smallest unit)
        file: File path or None for smart naming/dump mode
        mode: SQL generation mode
        primary_key: Primary key column name
        batch_insert: Use multi-row INSERT
        if_not_exists: Add IF NOT EXISTS to CREATE TABLE
        auto_backup: Backup existing file before overwrite (DDL-specific)
        base_dir: Base directory for file operations (default: current dir)
        encoding: File encoding
        wrap: Auto-convert to dict if needed
        overwrite: Allow overwriting existing file
        safe: Use atomic write
        append: Append to existing file
        debug: Print debug information
        
    Returns:
        SQL string if dump mode (no file created), otherwise None
    """
    data = _wrap_if_needed(data, wrap)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [STEP 1] Generate SQL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sql = dumps(
        data,
        mode=mode,
        primary_key=primary_key,
        if_not_exists=if_not_exists,
        batch_insert=batch_insert,
        **kwargs
    )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [STEP 2] Smart file naming
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    resolved_file = file
    
    # Check if file is a directory path (from dbl_write.py with name=None)
    # IMPORTANT: The path might not exist yet, so we can't use .is_dir()
    # Instead, check if it has no extension and ends with a directory name
    if file is not None and isinstance(file, (str, Path)):
        file_path = _ensure_path(file)
        
        # If path exists and is a directory, treat as base_dir
        if file_path.exists() and file_path.is_dir():
            if debug:
                print(f"[DDL] Received existing directory: {file_path}")
            base_dir = file_path
            resolved_file = None
        # If path doesn't exist but has no extension, assume it's a directory
        elif not file_path.exists() and not file_path.suffix:
            if debug:
                print(f"[DDL] Received directory path (not exists yet): {file_path}")
            base_dir = file_path
            resolved_file = None
    
    # Extract table name from SQL data BEFORE trying to resolve file
    # This ensures we get table name for both explicit file=None and directory cases
    extracted_table_name = None
    if resolved_file is None:
        extracted_table_name = extract_table_name_from_ddl(data)
        if debug and extracted_table_name:
            print(f"[DDL] Auto-extracted table name: {extracted_table_name}")
    
    if resolved_file is None:
        # Use the already extracted table name
        if extracted_table_name:
            # Table name found → create file
            resolved_file = f"{extracted_table_name}.sql"
        else:
            # No table name → dump mode
            if debug:
                print("[DDL] No table name found → dump mode (return SQL string)")
            return sql
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [STEP 3] Build full path
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if isinstance(resolved_file, (str, Path)):
        path_obj = _ensure_path(resolved_file)
        
        # Apply base_dir if provided
        if base_dir:
            base_dir_path = _ensure_path(base_dir)
            path_obj = base_dir_path / path_obj.name
    else:
        # File-like object
        path_obj = None
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [STEP 4] Auto-backup existing file
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if path_obj and auto_backup and path_obj.exists() and not append:
        backup_path = backup_existing_file(path_obj, debug=debug)
        if backup_path and debug:
            print(f"[DDL] Backed up existing file: {path_obj.name} → {backup_path.name}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [STEP 5] Write file
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # Append mode
    if append:
        if path_obj:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("a", encoding=encoding) as f:
                f.write("\n\n")
                f.write(sql)
        else:
            resolved_file.write("\n\n")
            resolved_file.write(sql)
        
        if debug:
            print(f"[DDL] Appended to: {path_obj if path_obj else 'file object'}")
        return None
    
    # Normal write mode
    if path_obj:
        if path_obj.exists() and not overwrite:
            raise FileExistsError(
                f"[sql.dump] Target exists and overwrite=False: {path_obj}"
            )
        
        if safe:
            _atomic_write_text(path_obj, sql, encoding=encoding)
        else:
            path_obj.parent.mkdir(parents=True, exist_ok=True)
            with path_obj.open("w", encoding=encoding) as f:
                f.write(sql)
        
        if debug:
            print(f"[DDL] Written to: {path_obj}")
        return None
    
    # File-like object
    resolved_file.write(sql)
    if debug:
        print("[DDL] Written to file object")
    return None


def dumps(
    data: Any,
    *,
    mode: str = "auto",
    primary_key: Optional[str] = None,
    if_not_exists: bool = True,
    batch_insert: bool = True,
    wrap: bool = False,
    **kwargs
) -> str:
    """
    Serialize to SQL string.
    
    Pattern: Just data → string (no file involved)
    
    Data Formats:
        # Raw SQL string (pass-through)
        "CREATE TABLE users (id INT, name TEXT);"
        
        # List of records (auto-infer schema and table name)
        [{"id": 1, "name": "Alice"}, ...]
        → Table name: "data_table"
        
        # Dict with table name
        {"table": "users", "records": [...]}
        
        # Dict with explicit schema
        {
            "table": "users",
            "schema": {"id": "INTEGER", "name": "VARCHAR(50)"},
            "records": [{"id": 1, "name": "Alice"}]
        }
    
    Args:
        data: Data to convert to SQL
        mode: SQL generation mode
        primary_key: Primary key column name
        if_not_exists: Add IF NOT EXISTS
        batch_insert: Use multi-row INSERT
        wrap: Auto-convert to dict
        
    Returns:
        SQL string
    """
    # Handle raw SQL string pass-through
    if isinstance(data, str):
        return data
    
    data = _wrap_if_needed(data, wrap)
    
    statements = []
    schema = None
    records = None
    table_name = "data_table"  # Default
    
    # Extract table name and data
    if isinstance(data, list):
        records = data
        mode = mode if mode != "auto" else "full"
    elif isinstance(data, dict):
        # Extract table name
        extracted_name = _extract_table_name(data)
        if extracted_name:
            table_name = extracted_name
        
        # Extract schema and records
        if "schema" in data:
            schema = data["schema"]
        if "records" in data:
            records = data["records"]
        
        # Auto-detect mode
        if mode == "auto":
            if schema and records:
                mode = "full"
            elif schema:
                mode = "create"
            elif records:
                mode = "full"
            else:
                mode = "create"
    else:
        raise ValueError(f"[sql.dumps] Unsupported data type: {type(data)}")
    
    # Infer schema if not provided
    if records and not schema:
        schema = _infer_schema_from_data(records)
    
    # Generate CREATE TABLE
    if mode in ("create", "full") and schema:
        create_sql = _generate_create_table(
            table_name, schema, primary_key, if_not_exists
        )
        statements.append(create_sql)
    
    # Generate INSERT statements
    if mode in ("insert", "full") and records:
        insert_sql = _generate_insert(table_name, records, batch_insert)
        statements.append(insert_sql)
    
    return "\n\n".join(statements)


# ===============================================================================
# Helper Functions (following Small → Big pattern)
# ===============================================================================

def create_table(
    schema: Dict[str, str],
    table: str = "data_table",
    *,
    primary_key: Optional[str] = None,
    if_not_exists: bool = True
) -> str:
    """
    Generate CREATE TABLE statement.
    
    Pattern: schema (small) → table name (big) → options
    
    Example:
        sql = create_table(
            {"id": "INTEGER", "name": "VARCHAR(100)"},
            "users",
            primary_key="id"
        )
    
    Args:
        schema: Dict of column_name -> sql_type
        table: Table name
        primary_key: Primary key column name
        if_not_exists: Add IF NOT EXISTS clause
        
    Returns:
        CREATE TABLE SQL statement
    """
    return _generate_create_table(table, schema, primary_key, if_not_exists)


def insert_records(
    records: List[Dict],
    table: str = "data_table",
    *,
    batch: bool = True
) -> str:
    """
    Generate INSERT statement(s).
    
    Pattern: records (small) → table name (big) → options
    
    Example:
        sql = insert_records(
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "users"
        )
    
    Args:
        records: List of record dicts
        table: Table name
        batch: Use batch insert
        
    Returns:
        INSERT SQL statement(s)
    """
    return _generate_insert(table, records, batch)


# ===============================================================================
# Test helper
# ===============================================================================

def _test(base_dir=None):
    """Test SQL parser functionality with smart file naming."""
    print("=" * 60)
    print("SQL DDL/DML Parser Test - REFACTORED")
    print("Smart File Naming + Auto-backup")
    print("=" * 60)
    
    # Sample data
    users = [
        {"id": 1, "name": "Alice", "email": "alice@example.com", "active": True},
        {"id": 2, "name": "Bob", "email": "bob@example.com", "active": True},
        {"id": 3, "name": "Charlie", "email": "charlie@example.com", "active": False}
    ]
    
    # Test 1: Dumps mode (no file)
    print("\n[TEST 1] Dumps mode (data only):")
    sql_str = dump(users, mode="full", primary_key="id")
    print(sql_str[:200] + "...")
    
    # Test 2: Smart file naming - extract from dict
    print("\n[TEST 2] Smart file naming (table in dict):")
    data_with_table = {
        "table": "users",
        "records": users
    }
    dump(data_with_table, mode="full", primary_key="id", base_dir=base_dir, debug=True)
    print("[OK] Created users.sql")
    
    # Test 3: Smart file naming - extract from SQL string
    print("\n[TEST 3] Smart file naming (SQL string):")
    sql = "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL);"
    dump(sql, base_dir=base_dir, debug=True)
    print("[OK] Created products.sql")
    
    # Test 4: Auto-backup on second write
    print("\n[TEST 4] Auto-backup (second write to users.sql):")
    updated_users = users + [{"id": 4, "name": "David", "email": "david@example.com", "active": True}]
    data_with_table["records"] = updated_users
    dump(data_with_table, mode="full", primary_key="id", base_dir=base_dir, debug=True)
    print("[OK] Backed up previous users.sql to users_01.sql")
    
    # Test 5: Explicit filename (traditional)
    print("\n[TEST 5] Explicit filename (traditional mode):")
    dump(users[:2], "manual_users.sql", mode="full", base_dir=base_dir, debug=True)
    print("[OK] Created manual_users.sql")
    
    # Test 6: No table name → dump mode
    print("\n[TEST 6] No table name (dump mode):")
    result = dump(users[:1], debug=True)
    print(f"[OK] Returned SQL string: {result[:100]}...")
    
    print("\n" + "=" * 60)
    print("Pattern verified: Smart file naming + Auto-backup")
    print("  file provided → use it")
    print("  file=None + table name → auto-create file")
    print("  file=None + no table → dump mode (return SQL)")
    print("=" * 60)


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
