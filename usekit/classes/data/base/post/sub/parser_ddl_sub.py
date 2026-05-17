# Path: usekit.classes.data.base.post.sub.parser_ddl_sub.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Helper functions for SQL DDL parser
# Features:
#   - Atomic write operations with temp file safety
#   - SQL value escaping and type inference
#   - Column name normalization
#   - Table name extraction from data structures
#   - CREATE TABLE and INSERT statement generation
#   - Schema inference from Python data
# -----------------------------------------------------------------------------------------------

from pathlib import Path
import tempfile
import os
from typing import Any, Union, Optional, Dict, List
import re


# ===============================================================================
# File I/O Utilities
# ===============================================================================

def _atomic_write_text(path: Path, text: str, encoding: str = "utf-8") -> None:
    """
    Safe write: write to temp file then atomically replace target.
    
    This prevents file corruption if write operation fails mid-way.
    
    Args:
        path: Target file path
        text: Content to write
        encoding: Text encoding
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", delete=False, dir=str(path.parent), encoding=encoding
    ) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def _ensure_path(file: Union[str, Path]) -> Path:
    """
    Convert to Path object if needed.
    
    Args:
        file: String or Path object
        
    Returns:
        Path object
    """
    return file if isinstance(file, Path) else Path(file)


# ===============================================================================
# Data Wrapping
# ===============================================================================

def _wrap_if_needed(data: Any, wrap: bool) -> Any:
    """
    Auto-wrap simple values into dict if needed.
    
    This allows users to pass simple lists and have them auto-converted
    to the dict format expected by the parser.
    
    Args:
        data: Input data (any type)
        wrap: Whether to perform auto-wrapping
        
    Returns:
        Wrapped data or original data
    """
    if not wrap:
        return data
    if not isinstance(data, dict):
        return {"tables": [data] if isinstance(data, list) else data}
    return data


# ===============================================================================
# SQL Value Handling
# ===============================================================================

def _escape_sql_value(value: Any) -> str:
    """
    Escape value for safe SQL insertion.
    
    Handles:
    - None → NULL
    - Boolean → TRUE/FALSE
    - Numbers → string representation
    - Strings → quoted with escaped single quotes
    
    Args:
        value: Python value to escape
        
    Returns:
        SQL-safe string representation
    """
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    # Fallback for other types
    escaped = str(value).replace("'", "''")
    return f"'{escaped}'"


def _parse_sql_type(value: Any) -> str:
    """
    Infer SQL type from Python value.
    
    Type mapping:
    - bool → BOOLEAN
    - int → INTEGER
    - float → REAL
    - str (>255 chars) → TEXT
    - str (<=255 chars) → VARCHAR(n)
    - other → TEXT
    
    Args:
        value: Python value to analyze
        
    Returns:
        SQL type string
    """
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, str):
        if len(value) > 255:
            return "TEXT"
        return f"VARCHAR({max(len(value) * 2, 50)})"
    return "TEXT"


# ===============================================================================
# Column and Table Name Handling
# ===============================================================================

def _normalize_column_name(name: str) -> str:
    """
    Normalize column name for SQL compatibility.
    
    Transformations:
    - Remove special characters (keep alphanumeric and underscore)
    - Replace whitespace with underscore
    - Convert to lowercase
    
    Args:
        name: Original column name
        
    Returns:
        Normalized column name
    """
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', '_', name)
    return name.lower()


def _extract_table_name(data: Any) -> Optional[str]:
    """
    Extract table name from data structure if present.
    
    Checks for these keys in order:
    - 'table'
    - 'table_name'
    - 'name'
    - '_table'
    
    Args:
        data: Data structure (typically dict)
        
    Returns:
        Table name if found, None otherwise
    """
    if isinstance(data, dict):
        for key in ['table', 'table_name', 'name', '_table']:
            if key in data:
                return str(data[key])
    return None


# ===============================================================================
# SQL Statement Generation
# ===============================================================================

def _generate_create_table(
    table_name: str,
    columns: Dict[str, str],
    primary_key: Optional[str] = None,
    if_not_exists: bool = True
) -> str:
    """
    Generate CREATE TABLE statement.
    
    Format:
        CREATE TABLE [IF NOT EXISTS] table_name (
            column1 type1 [PRIMARY KEY],
            column2 type2,
            ...
        );
    
    Args:
        table_name: Name of table to create
        columns: Dict of column_name -> sql_type
        primary_key: Optional primary key column name
        if_not_exists: Add IF NOT EXISTS clause
        
    Returns:
        CREATE TABLE SQL statement
    """
    exists_clause = "IF NOT EXISTS " if if_not_exists else ""
    
    col_defs = []
    for col_name, col_type in columns.items():
        col_def = f"    {col_name} {col_type}"
        if col_name == primary_key:
            col_def += " PRIMARY KEY"
        col_defs.append(col_def)
    
    columns_sql = ",\n".join(col_defs)
    
    return f"""CREATE TABLE {exists_clause}{table_name} (
{columns_sql}
);"""


def _generate_insert(
    table_name: str,
    data: Union[Dict, List[Dict]],
    batch: bool = True
) -> str:
    """
    Generate INSERT statement(s).
    
    Two modes:
    - batch=True: Single INSERT with multiple VALUES rows
    - batch=False: Multiple single-row INSERT statements
    
    Args:
        table_name: Target table name
        data: Single dict or list of dicts with data
        batch: Use batch insert (single statement)
        
    Returns:
        INSERT SQL statement(s)
    """
    if not isinstance(data, list):
        data = [data]
    
    if not data:
        return ""
    
    columns = list(data[0].keys())
    columns_sql = ", ".join(columns)
    
    if batch:
        # Batch mode: single INSERT with multiple VALUES
        values_list = []
        for record in data:
            values = [_escape_sql_value(record.get(col)) for col in columns]
            values_sql = ", ".join(values)
            values_list.append(f"({values_sql})")
        
        all_values = ",\n    ".join(values_list)
        return f"""INSERT INTO {table_name} ({columns_sql})
VALUES
    {all_values};"""
    else:
        # Individual mode: separate INSERT for each row
        statements = []
        for record in data:
            values = [_escape_sql_value(record.get(col)) for col in columns]
            values_sql = ", ".join(values)
            statements.append(
                f"INSERT INTO {table_name} ({columns_sql}) VALUES ({values_sql});"
            )
        return "\n".join(statements)


# ===============================================================================
# Schema Inference
# ===============================================================================

def _infer_schema_from_data(data: List[Dict]) -> Dict[str, str]:
    """
    Infer SQL schema from data records.
    
    Process:
    1. Collect all keys from all records
    2. For each key, find first non-None value
    3. Infer SQL type from that value
    4. Normalize column names
    
    Args:
        data: List of record dicts
        
    Returns:
        Dict of normalized_column_name -> sql_type
    """
    if not data:
        return {}
    
    schema = {}
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    
    for key in all_keys:
        sample_value = None
        for record in data:
            if key in record and record[key] is not None:
                sample_value = record[key]
                break
        
        if sample_value is not None:
            schema[_normalize_column_name(key)] = _parse_sql_type(sample_value)
        else:
            schema[_normalize_column_name(key)] = "TEXT"
    
    return schema


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "_atomic_write_text",
    "_ensure_path",
    "_wrap_if_needed",
    "_escape_sql_value",
    "_parse_sql_type",
    "_normalize_column_name",
    "_extract_table_name",
    "_generate_create_table",
    "_generate_insert",
    "_infer_schema_from_data",
]


# -----------------------------------------------------------------------------------------------
#  MEMORY IS EMOTION
# -----------------------------------------------------------------------------------------------