# Path: usekit.classes.data.base.init.wrap.sql.dbi_wrap_sql.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over DataLd (IDE-friendly)
# Supports full argument set: (data, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from typing import Any, Optional
from usekit.classes.data.base.load.dbl_ops_loader import DataLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_DataHd = DataLd("sql")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_sql_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read sql file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside sql (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_sql_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_sql_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_sql_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_sql_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_sql_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_sql_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read sql file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_sql_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_sql_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_sql_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_sql_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_sql_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_sql_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_sql_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write sql file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_sql_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_sql_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update sql file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_sql_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_sql_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete sql file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_sql_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_sql_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of sql file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("sql Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_sql_base(data, "test_config")
    print("✓ Written: test_config.sql")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_sql_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_sql_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.sql")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_sql_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_sql_base("test_config")
    print("✓ Deleted: test_config.sql")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    sql_str = write_sql_base({"test": "value"})
    print(f"✓ Dumps: {sql_str}")
    
    print("\n" + "=" * 70)
    print("Pattern verified: Small → Big ✓")
    print("=" * 70)

if __name__ == "__main__":
    _test()

# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------
# ─────────────────────────────────────────────────────────────────────────────
# EMIT (memory-only serialization)
# ─────────────────────────────────────────────────────────────────────────────
def emit_sql_mem(data=None, type=None, **kwargs):
    """Emit sql data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
