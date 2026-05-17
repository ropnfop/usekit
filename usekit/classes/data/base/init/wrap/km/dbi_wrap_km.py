# Path: usekit.classes.data.base.init.wrap.km.dbi_wrap_km.py
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
_DataHd = DataLd("km")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_km_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read km file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside km (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_km_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_km_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_km_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_km_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_km_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_km_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read km file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_km_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_km_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_km_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_km_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_km_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_km_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_km_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write km file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_km_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_km_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update km file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_km_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_km_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete km file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_km_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_km_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of km file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("km Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_km_base(data, "test_config")
    print("✓ Written: test_config.km")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_km_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_km_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.km")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_km_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_km_base("test_config")
    print("✓ Deleted: test_config.km")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    km_str = write_km_base({"test": "value"})
    print(f"✓ Dumps: {km_str}")
    
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
def emit_km_mem(data=None, type=None, **kwargs):
    """Emit km data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
