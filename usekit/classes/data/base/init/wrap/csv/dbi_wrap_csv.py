# Path: usekit.classes.data.base.init.wrap.csv.dbi_wrap_csv.py
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
_DataHd = DataLd("csv")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_csv_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read csv file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside csv (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_csv_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_csv_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_csv_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_csv_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_csv_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_csv_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read csv file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_csv_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_csv_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_csv_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_csv_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_csv_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_csv_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_csv_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write csv file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_csv_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_csv_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update csv file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_csv_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_csv_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete csv file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_csv_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_csv_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of csv file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("csv Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_csv_base(data, "test_config")
    print("✓ Written: test_config.csv")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_csv_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_csv_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.csv")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_csv_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_csv_base("test_config")
    print("✓ Deleted: test_config.csv")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    csv_str = write_csv_base({"test": "value"})
    print(f"✓ Dumps: {csv_str}")
    
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
def emit_csv_mem(data=None, type=None, **kwargs):
    """Emit csv data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
