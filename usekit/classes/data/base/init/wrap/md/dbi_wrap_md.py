# Path: usekit.classes.data.base.init.wrap.md.dbi_wrap_md.py
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
_DataHd = DataLd("md")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_md_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read md file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside md (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_md_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_md_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_md_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_md_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_md_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_md_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read md file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_md_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_md_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_md_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_md_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_md_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_md_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_md_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write md file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_md_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_md_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update md file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_md_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_md_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete md file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_md_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_md_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of md file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# MEM — process-level in-memory store (no file I/O)
# ─────────────────────────────────────────────────────────────────────────────

def read_md_mem(name=None, **kwargs):
    """Read from in-memory store."""
    return _DataHd.read_mem(name=name, **kwargs)

def write_md_mem(data=None, name=None, **kwargs):
    """Write to in-memory store."""
    return _DataHd.write_mem(data=data, name=name, **kwargs)

def update_md_mem(data=None, name=None, **kwargs):
    """Update (merge) in in-memory store."""
    return _DataHd.update_mem(data=data, name=name, **kwargs)

def delete_md_mem(name=None, **kwargs):
    """Delete from in-memory store."""
    return _DataHd.delete_mem(name=name, **kwargs)

def has_md_mem(name=None, **kwargs):
    """Check existence in in-memory store."""
    return _DataHd.has_mem(name=name, **kwargs)

def list_md_mem(**kwargs):
    """List all keys in in-memory store."""
    return _DataHd.list_mem()

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("md Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_md_base(data, "test_config")
    print("✓ Written: test_config.md")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_md_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_md_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.md")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_md_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_md_base("test_config")
    print("✓ Deleted: test_config.md")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    md_str = write_md_base({"test": "value"})
    print(f"✓ Dumps: {md_str}")
    
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
def emit_md_mem(data=None, type=None, **kwargs):
    """Emit md data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
