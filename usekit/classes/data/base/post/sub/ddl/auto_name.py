# Path: usekit.classes.data.base.post.sub.ddl.auto_name.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: DDL-specific auto-naming utilities (REFACTORED)
# Features:
#   - Extract table name from SQL DDL
#   - Backup existing file with auto-increment sequence
#   - Pattern: table_name → table_name_01 → table_name_02 ...
# Changes:
#   - Simplified: backup_existing_file() now takes Path directly
#   - Removed: prepare_ddl_write(), resolve_ddl_filename() (logic moved to parser)
# -----------------------------------------------------------------------------------------------

from pathlib import Path
from typing import Any, Optional
import re
import shutil


# ===============================================================================
# Table Name Extraction
# ===============================================================================

def extract_table_name_from_ddl(data: Any) -> Optional[str]:
    """
    Extract table name from DDL data.
    
    Sources (in priority order):
    1. Dict with 'table' key
    2. Raw SQL string (parse CREATE TABLE statement)
    3. List of records (return None - use default)
    
    Args:
        data: DDL data (str, dict, or list)
        
    Returns:
        Table name if found, None otherwise
        
    Examples:
        >>> extract_table_name_from_ddl("CREATE TABLE users (id INT);")
        'users'
        
        >>> extract_table_name_from_ddl({"table": "products", "records": [...]})
        'products'
        
        >>> extract_table_name_from_ddl([{"id": 1}])
        None
    """
    
    # Case 1: Dict with explicit table name
    if isinstance(data, dict):
        for key in ['table', 'table_name', 'name', '_table']:
            if key in data and data[key]:
                return str(data[key])
    
    # Case 2: Raw SQL string - parse CREATE TABLE
    if isinstance(data, str):
        return _parse_table_name_from_sql(data)
    
    # Case 3: List or other types - no auto-detection
    return None


def _parse_table_name_from_sql(sql: str) -> Optional[str]:
    """
    Parse table name from CREATE TABLE statement.
    
    Handles:
    - CREATE TABLE table_name
    - CREATE TABLE IF NOT EXISTS table_name
    - CREATE TABLE schema.table_name
    - Quoted identifiers: "table_name" or `table_name`
    
    Args:
        sql: SQL DDL string
        
    Returns:
        Table name if found, None otherwise
    """
    
    # Remove comments
    sql_clean = re.sub(r'--[^\n]*', '', sql)
    sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
    
    # Pattern: CREATE TABLE [IF NOT EXISTS] [schema.]table_name
    # Supports: unquoted, "quoted", `quoted`
    pattern = r'''
        CREATE\s+TABLE\s+
        (?:IF\s+NOT\s+EXISTS\s+)?
        (?:[\w]+\.)?                     # Optional schema
        (?:
            "([^"]+)"|                   # Double-quoted
            `([^`]+)`|                   # Backtick-quoted
            (\w+)                        # Unquoted
        )
    '''
    
    match = re.search(pattern, sql_clean, re.IGNORECASE | re.VERBOSE)
    
    if match:
        # Return first non-None group (one of the three capture groups)
        table_name = match.group(1) or match.group(2) or match.group(3)
        return table_name
    
    return None


# ===============================================================================
# Backup Management (Simplified)
# ===============================================================================

def backup_existing_file(
    source_path: Path,
    debug: bool = False
) -> Optional[Path]:
    """
    Backup existing file with auto-increment sequence.
    
    Strategy:
    - Main file is always {table}.sql (latest version)
    - Old versions backed up as {table}_01.sql, _02.sql, etc.
    
    Logic:
    1. If source_path doesn't exist → no backup needed
    2. If exists → find next sequence number and backup
    3. Return backup path
    
    Args:
        source_path: Path to file that needs backup
        debug: Print debug info
        
    Returns:
        Path of backup file if created, None if no backup needed
        
    Examples:
        >>> # No existing file
        >>> backup_existing_file(Path("/data/users.sql"))
        None
        
        >>> # users.sql exists, no backups yet
        >>> backup_existing_file(Path("/data/users.sql"))
        Path("/data/users_01.sql")  # users.sql copied to users_01.sql
        
        >>> # users.sql and users_01.sql exist
        >>> backup_existing_file(Path("/data/users.sql"))
        Path("/data/users_02.sql")  # users.sql copied to users_02.sql
    """
    
    # No backup needed if file doesn't exist
    if not source_path.exists():
        if debug:
            print(f"[DDL] No backup needed: {source_path.name} doesn't exist")
        return None
    
    # Extract base name and extension
    stem = source_path.stem
    suffix = source_path.suffix
    parent = source_path.parent
    
    # Find next available backup sequence
    sequence = 1
    max_attempts = 999
    
    while sequence < max_attempts:
        backup_name = f"{stem}_{sequence:02d}{suffix}"
        backup_path = parent / backup_name
        
        if not backup_path.exists():
            # Backup the current file
            shutil.copy2(source_path, backup_path)
            
            if debug:
                print(f"[DDL] Backed up: {source_path.name} → {backup_name}")
            
            return backup_path
        
        sequence += 1
    
    # Fallback: timestamp-based backup
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{stem}_{timestamp}{suffix}"
    backup_path = parent / backup_name
    
    shutil.copy2(source_path, backup_path)
    
    if debug:
        print(f"[DDL] Backed up (timestamp): {source_path.name} → {backup_name}")
    
    return backup_path


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "extract_table_name_from_ddl",
    "backup_existing_file",
]


# ===============================================================================
# Test
# ===============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DDL Auto-naming Test - Simplified Version")
    print("=" * 70)
    
    # Test 1: Extract from SQL string
    print("\n[Test 1] Extract table name from SQL:")
    sql_cases = [
        "CREATE TABLE users (id INT);",
        "CREATE TABLE IF NOT EXISTS products (id INT);",
        'CREATE TABLE "order_items" (id INT);',
        "CREATE TABLE db.employees (id INT);",
    ]
    
    for sql in sql_cases:
        name = extract_table_name_from_ddl(sql)
        print(f"  {sql[:40]:40s} → {name}")
    
    # Test 2: Extract from dict
    print("\n[Test 2] Extract from dict:")
    dict_data = {"table": "customers", "records": []}
    name = extract_table_name_from_ddl(dict_data)
    print(f"  {dict_data} → {name}")
    
    # Test 3: Backup strategy simulation
    print("\n[Test 3] Backup strategy (simplified):")
    from tempfile import TemporaryDirectory
    
    with TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        source_file = tmp_path / "users.sql"
        
        # First write - no backup needed
        print("\n  Write 1:")
        source_file.write_text("CREATE TABLE users (id INT);")
        backup1 = backup_existing_file(source_file, debug=True)
        print(f"    Backup created: {backup1}")
        
        # Second write - backup to users_01.sql
        print("\n  Write 2:")
        source_file.write_text("CREATE TABLE users (id INT, name TEXT);")
        backup2 = backup_existing_file(source_file, debug=True)
        print(f"    Backup created: {backup2.name if backup2 else None}")
        
        # Third write - backup to users_02.sql
        print("\n  Write 3:")
        source_file.write_text("CREATE TABLE users (id INT, name TEXT, email TEXT);")
        backup3 = backup_existing_file(source_file, debug=True)
        print(f"    Backup created: {backup3.name if backup3 else None}")
        
        # Show final file structure
        print("\n  Final files in directory:")
        for f in sorted(tmp_path.glob("*.sql")):
            content = f.read_text()[:50]
            print(f"    {f.name:15s} - {content}...")
    
    print("\n" + "=" * 70)
    print("Backup Strategy: Latest always in {table}.sql")
    print("                 History in {table}_01.sql, _02.sql, ...")
    print("=" * 70)


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------
