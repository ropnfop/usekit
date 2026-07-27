# Path: usekit.classes.common.utils.helper_km_transform.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × Claude
# — memory is emotion —
#
# KM Level 2: Transform Pipeline
#   JSON → JTK (flatten) → KQL (query) → KTJ (reconstruct) → JSON
#
# Wraps TreeCache (flatten engine) + keypath (CRUD engine).
# The only truly new logic is KQL query parsing.
# -----------------------------------------------------------------------------------------------

from __future__ import annotations

import re
from copy import deepcopy
from typing import Any, Dict, List, Optional, Literal

from usekit.classes.common.utils.helper_treecache import TreeCache
from usekit.classes.common.utils.helper_keypath import set_key_path


# ===============================================================================
# JTK — Flatten (JSON → Leaf Table)
# ===============================================================================

def km_flatten(
    data: dict,
    *,
    depth: Literal["shallow", "deep"] = "shallow",
) -> List[Dict[str, Any]]:
    """
    Flatten nested dict to KM leaf table.

    Each row: {"path": str, "key": str, "value": Any}

    Args:
        data: Nested dict to flatten
        depth: "shallow" stops at leaf values (preserves nested objects),
               "deep" recursively flattens all nested objects.

    Returns:
        List of leaf records [{path, key, value}, ...]
    """
    if not isinstance(data, dict):
        raise TypeError(f"km_flatten expects dict, got {type(data).__name__}")

    if depth == "deep":
        return _flatten_deep(data)

    return _flatten_shallow(data)


def _flatten_shallow(data: dict, _prefix: str = "") -> List[Dict[str, Any]]:
    """Shallow: stop at scalar/list-of-scalar/nested-dict leaf values."""
    result = []
    for key, value in data.items():
        if isinstance(value, dict):
            sub_prefix = f"{_prefix}/{key}" if _prefix else key
            result.extend(_flatten_shallow(value, sub_prefix))
        elif isinstance(value, list):
            # Array of dicts → recurse with index
            if value and isinstance(value[0], dict):
                for i, item in enumerate(value):
                    sub_prefix = f"{_prefix}/{key}[{i}]" if _prefix else f"{key}[{i}]"
                    result.extend(_flatten_shallow(item, sub_prefix))
            else:
                # Array of scalars → single leaf
                result.append({"path": _prefix, "key": key, "value": value})
        else:
            result.append({"path": _prefix, "key": key, "value": value})
    return result


def _flatten_deep(data: dict) -> List[Dict[str, Any]]:
    """Deep: use TreeCache to fully flatten, then convert to leaf table."""
    tc = TreeCache(data)
    flat = tc.to_flat()  # {'a.b.c': val, ...}

    result = []
    for full_path, value in flat.items():
        # TreeCache uses '.' separator → convert to '/'
        full_path_slash = full_path.replace(".", "/")
        parts = full_path_slash.rsplit("/", 1)
        if len(parts) == 2:
            result.append({"path": parts[0], "key": parts[1], "value": value})
        else:
            result.append({"path": "", "key": parts[0], "value": value})

    return result


# ===============================================================================
# KTJ — Reconstruct (Leaf Table → JSON)
# ===============================================================================

def km_reconstruct(leaf_table: List[Dict[str, Any]]) -> dict:
    """
    Reconstruct nested dict from KM leaf table.

    Uses set_key_path for each row to rebuild the tree.

    Args:
        leaf_table: List of leaf records [{path, key, value}, ...]

    Returns:
        Nested dict restored from leaf table.
    """
    result = {}
    for row in leaf_table:
        path = row.get("path", "")
        key = row["key"]
        value = row["value"]

        full_path = f"{path}/{key}" if path else key
        set_key_path(result, full_path, value)

    return result


# ===============================================================================
# KQL — Query (Leaf Table → Leaf Table)
# ===============================================================================

# WHERE operators
_OP_MAP = {
    "=": lambda a, b: str(a) == str(b),
    "!=": lambda a, b: str(a) != str(b),
    ">": lambda a, b: float(a) > float(b),
    "<": lambda a, b: float(a) < float(b),
    ">=": lambda a, b: float(a) >= float(b),
    "<=": lambda a, b: float(a) <= float(b),
}


def _match_like(value: str, pattern: str) -> bool:
    """SQL-style LIKE: % = any, _ = single char."""
    regex = "^"
    for ch in pattern:
        if ch == "%":
            regex += ".*"
        elif ch == "_":
            regex += "."
        else:
            regex += re.escape(ch)
    regex += "$"
    return bool(re.match(regex, str(value)))


def _match_where(row: Dict[str, Any], conditions: List[dict]) -> bool:
    """Check if a row matches all WHERE conditions (AND logic)."""
    for cond in conditions:
        field = cond["field"]
        op = cond["op"]
        target = cond["value"]
        actual = row.get(field, "")

        if op == "LIKE":
            if not _match_like(actual, target):
                return False
        elif op == "NOT LIKE":
            if _match_like(actual, target):
                return False
        elif op in _OP_MAP:
            try:
                if not _OP_MAP[op](actual, target):
                    return False
            except (ValueError, TypeError):
                return False
        else:
            return False

    return True


def _parse_value(raw: str) -> Any:
    """Parse a raw string value into Python type."""
    raw = raw.strip()

    # Quoted string
    if (raw.startswith("'") and raw.endswith("'")) or \
       (raw.startswith('"') and raw.endswith('"')):
        return raw[1:-1]

    # Boolean
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.lower() == "none" or raw.lower() == "null":
        return None

    # Number
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _parse_where(where_str: str) -> List[dict]:
    """
    Parse WHERE clause into condition list.

    Supports: =, !=, >, <, >=, <=, LIKE, NOT LIKE
    Multiple conditions joined by AND.
    """
    conditions = []
    # Split by AND (case-insensitive)
    parts = re.split(r"\s+AND\s+", where_str, flags=re.IGNORECASE)

    for part in parts:
        part = part.strip()

        # NOT LIKE
        m = re.match(r"(\w+)\s+NOT\s+LIKE\s+['\"](.+?)['\"]", part, re.IGNORECASE)
        if m:
            conditions.append({"field": m.group(1), "op": "NOT LIKE", "value": m.group(2)})
            continue

        # LIKE
        m = re.match(r"(\w+)\s+LIKE\s+['\"](.+?)['\"]", part, re.IGNORECASE)
        if m:
            conditions.append({"field": m.group(1), "op": "LIKE", "value": m.group(2)})
            continue

        # Comparison: field op value
        m = re.match(r"(\w+)\s*(!=|>=|<=|>|<|=)\s*(.+)", part)
        if m:
            conditions.append({
                "field": m.group(1),
                "op": m.group(2),
                "value": _parse_value(m.group(3)),
            })
            continue

        raise ValueError(f"Cannot parse WHERE condition: '{part}'")

    return conditions


def _parse_kql(query: str) -> dict:
    """
    Parse KQL query string into operation dict.

    Supported:
        SELECT * WHERE path LIKE 'ai/%'
        UPDATE SET value = 'gpt-4' WHERE key = 'model'
        DELETE WHERE path LIKE 'srs/%'
        INSERT path='ai/config' key='max_tokens' value=1000
    """
    query = query.strip()
    upper = query.upper()

    # SELECT
    if upper.startswith("SELECT"):
        m = re.match(r"SELECT\s+\*\s+WHERE\s+(.+)", query, re.IGNORECASE)
        if m:
            return {"op": "SELECT", "where": _parse_where(m.group(1))}
        # SELECT * (all)
        if re.match(r"SELECT\s+\*\s*$", query, re.IGNORECASE):
            return {"op": "SELECT", "where": []}
        raise ValueError(f"Invalid SELECT: '{query}'")

    # UPDATE
    if upper.startswith("UPDATE"):
        m = re.match(
            r"UPDATE\s+SET\s+(.+?)\s+WHERE\s+(.+)",
            query, re.IGNORECASE,
        )
        if m:
            set_clause = m.group(1)
            where_clause = m.group(2)

            # Parse SET: field = value [, field = value]
            set_pairs = {}
            for pair in re.split(r",\s*", set_clause):
                pm = re.match(r"(\w+)\s*=\s*(.+)", pair.strip())
                if pm:
                    set_pairs[pm.group(1)] = _parse_value(pm.group(2))

            return {
                "op": "UPDATE",
                "set": set_pairs,
                "where": _parse_where(where_clause),
            }
        raise ValueError(f"Invalid UPDATE: '{query}'")

    # DELETE
    if upper.startswith("DELETE"):
        m = re.match(r"DELETE\s+WHERE\s+(.+)", query, re.IGNORECASE)
        if m:
            return {"op": "DELETE", "where": _parse_where(m.group(1))}
        raise ValueError(f"Invalid DELETE: '{query}'")

    # INSERT
    if upper.startswith("INSERT"):
        m = re.match(r"INSERT\s+(.+)", query, re.IGNORECASE)
        if m:
            body = m.group(1)
            values = {}
            for pair in re.finditer(r"(\w+)\s*=\s*(['\"].*?['\"]|\S+)", body):
                values[pair.group(1)] = _parse_value(pair.group(2))

            if "key" not in values:
                raise ValueError(f"INSERT requires 'key': '{query}'")

            return {
                "op": "INSERT",
                "values": {
                    "path": values.get("path", ""),
                    "key": values["key"],
                    "value": values.get("value"),
                },
            }
        raise ValueError(f"Invalid INSERT: '{query}'")

    raise ValueError(f"Unknown KQL operation: '{query}'")


def km_query(
    leaf_table: List[Dict[str, Any]],
    query: str,
) -> List[Dict[str, Any]]:
    """
    Execute KQL query on leaf table.

    Args:
        leaf_table: Input leaf table
        query: KQL query string

    Returns:
        Modified/filtered leaf table
    """
    parsed = _parse_kql(query)
    op = parsed["op"]

    if op == "SELECT":
        if not parsed["where"]:
            return list(leaf_table)
        return [row for row in leaf_table if _match_where(row, parsed["where"])]

    if op == "UPDATE":
        result = []
        for row in leaf_table:
            if _match_where(row, parsed["where"]):
                row = dict(row)  # copy
                for field, value in parsed["set"].items():
                    row[field] = value
            result.append(row)
        return result

    if op == "DELETE":
        return [row for row in leaf_table if not _match_where(row, parsed["where"])]

    if op == "INSERT":
        return list(leaf_table) + [parsed["values"]]

    raise ValueError(f"Unsupported operation: {op}")


# ===============================================================================
# Pipeline — Chain operations
# ===============================================================================

def km_pipe(
    data: dict,
    queries: List[str],
    *,
    depth: Literal["shallow", "deep"] = "shallow",
) -> dict:
    """
    Flatten → chain KQL queries → reconstruct.

    Args:
        data: Input nested dict
        queries: List of KQL query strings to apply in order
        depth: Flatten depth ("shallow" or "deep")

    Returns:
        Reconstructed nested dict after all queries applied.
    """
    leaf = km_flatten(data, depth=depth)
    for q in queries:
        leaf = km_query(leaf, q)
    return km_reconstruct(leaf)


# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "km_flatten",
    "km_reconstruct",
    "km_query",
    "km_pipe",
]
