# Path: usekit.classes.data.base.init.wrap.ddl.dbi_wrap_ddl.py
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
_DataHd = DataLd("ddl")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_ddl_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read ddl file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside ddl (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read ddl file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_ddl_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_ddl_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_ddl_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_ddl_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_ddl_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_ddl_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_ddl_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write ddl file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_ddl_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_ddl_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update ddl file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete ddl file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of ddl file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("ddl Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_ddl_base(data, "test_config")
    print("✓ Written: test_config.ddl")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_ddl_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_ddl_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.ddl")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_ddl_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_ddl_base("test_config")
    print("✓ Deleted: test_config.ddl")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    ddl_str = write_ddl_base({"test": "value"})
    print(f"✓ Dumps: {ddl_str}")
    
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
def emit_ddl_mem(data=None, type=None, **kwargs):
    """Emit ddl data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
