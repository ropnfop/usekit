# Path: usekit.classes.data.base.init.wrap.any.dbi_wrap_any.py
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
_DataHd = DataLd("any")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_any_base(name: Optional[str] = None, mod: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read any file from BASE location.

    Args:
        name: File name (without extension)
        mod: fmt sub name (default "all")
        dir_path: Custom directory path
        keydata: Optional key path inside any (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from SUB location."""
    return _DataHd.read_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from DIR location."""
    return _DataHd.read_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from NOW location."""
    return _DataHd.read_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from TMP location."""
    return _DataHd.read_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read any file from CACHE location."""
    return _DataHd.read_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_any_base(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to BASE location."""
    return _DataHd.write_base(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_any_sub(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_any_dir(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_any_now(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to NOW location."""
    return _DataHd.write_now(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_any_tmp(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_any_pre(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_any_cache(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write any file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_any_base(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in BASE location."""
    return _DataHd.update_base(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_sub(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_dir(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_now(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in NOW location."""
    return _DataHd.update_now(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_tmp(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_pre(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_any_cache(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update any file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_any_base(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from BASE location."""
    return _DataHd.delete_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from SUB location."""
    return _DataHd.delete_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from DIR location."""
    return _DataHd.delete_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from NOW location."""
    return _DataHd.delete_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from TMP location."""
    return _DataHd.delete_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete any file from CACHE location."""
    return _DataHd.delete_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_any_base(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in BASE location."""
    return _DataHd.has_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in SUB location."""
    return _DataHd.has_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in DIR location."""
    return _DataHd.has_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in NOW location."""
    return _DataHd.has_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in TMP location."""
    return _DataHd.has_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of any file in CACHE location."""
    return _DataHd.has_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("any Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_any_base(data, "test_config")
    print("✓ Written: test_config.any")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_any_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_any_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.any")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_any_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_any_base("test_config")
    print("✓ Deleted: test_config.any")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    any_str = write_any_base({"test": "value"})
    print(f"✓ Dumps: {any_str}")
    
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
def emit_any_mem(data=None, type=None, **kwargs):
    """Emit any data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
