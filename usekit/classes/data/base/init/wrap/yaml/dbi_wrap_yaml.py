# Path: usekit.classes.data.base.init.wrap.yaml.dbi_wrap_yaml.py
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
_DataHd = DataLd("yaml")

# ─────────────────────────────────────────────────────────────────────────────
# READ
# ─────────────────────────────────────────────────────────────────────────────
def read_yaml_base(name: Optional[str] = None, dir_path: Optional[str] = None,
                   keydata: Optional[Any] = None, cus: Optional[str] = None, **kwargs) -> Any:
    """Read yaml file from BASE location.

    Args:
        name: File name (without extension)
        dir_path: Custom directory path
        keydata: Optional key path inside yaml (e.g. "meta.version" or ["meta","version"])
        cus: Custom preset path key (e.g. "job01", "backup", "user01")
        **kwargs: Additional parameters
    """
    return _DataHd.read_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_yaml_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from SUB location."""
    return _DataHd.read_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_yaml_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from DIR location."""
    return _DataHd.read_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_yaml_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from NOW location."""
    return _DataHd.read_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_yaml_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from TMP location."""
    return _DataHd.read_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def read_yaml_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from CUSTOM preset location."""
    return _DataHd.read_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def read_yaml_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Read yaml file from CACHE location."""
    return _DataHd.read_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# WRITE
# ─────────────────────────────────────────────────────────────────────────────
def write_yaml_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to BASE location."""
    return _DataHd.write_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_yaml_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to SUB location."""
    return _DataHd.write_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_yaml_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to DIR location."""
    return _DataHd.write_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_yaml_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to NOW location."""
    return _DataHd.write_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_yaml_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to TMP location."""
    return _DataHd.write_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def write_yaml_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to CUSTOM preset location."""
    return _DataHd.write_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def write_yaml_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Write yaml file to CACHE location."""
    return _DataHd.write_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────
def update_yaml_base(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in BASE location."""
    return _DataHd.update_base(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_sub(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in SUB location."""
    return _DataHd.update_sub(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_dir(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in DIR location."""
    return _DataHd.update_dir(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_now(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in NOW location."""
    return _DataHd.update_now(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_tmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in TMP location."""
    return _DataHd.update_tmp(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_pre(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in CUSTOM preset location."""
    return _DataHd.update_pre(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def update_yaml_cache(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Update yaml file in CACHE location."""
    return _DataHd.update_cache(data=data, name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────────────────────
def delete_yaml_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from BASE location."""
    return _DataHd.delete_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from SUB location."""
    return _DataHd.delete_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from DIR location."""
    return _DataHd.delete_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from NOW location."""
    return _DataHd.delete_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from TMP location."""
    return _DataHd.delete_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from CUSTOM preset location."""
    return _DataHd.delete_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def delete_yaml_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Delete yaml file from CACHE location."""
    return _DataHd.delete_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# HAS
# ─────────────────────────────────────────────────────────────────────────────
def has_yaml_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in BASE location."""
    return _DataHd.has_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in SUB location."""
    return _DataHd.has_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in DIR location."""
    return _DataHd.has_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in NOW location."""
    return _DataHd.has_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in TMP location."""
    return _DataHd.has_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in CUSTOM preset location."""
    return _DataHd.has_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def has_yaml_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Check existence of yaml file in CACHE location."""
    return _DataHd.has_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# MEM — process-level in-memory store (no file I/O)
# ─────────────────────────────────────────────────────────────────────────────

def read_yaml_mem(name=None, **kwargs):
    """Read from in-memory store."""
    return _DataHd.read_mem(name=name, **kwargs)

def write_yaml_mem(data=None, name=None, **kwargs):
    """Write to in-memory store."""
    return _DataHd.write_mem(data=data, name=name, **kwargs)

def update_yaml_mem(data=None, name=None, **kwargs):
    """Update (merge) in in-memory store."""
    return _DataHd.update_mem(data=data, name=name, **kwargs)

def delete_yaml_mem(name=None, **kwargs):
    """Delete from in-memory store."""
    return _DataHd.delete_mem(name=name, **kwargs)

def has_yaml_mem(name=None, **kwargs):
    """Check existence in in-memory store."""
    return _DataHd.has_mem(name=name, **kwargs)

def list_yaml_mem(**kwargs):
    """List all keys in in-memory store."""
    return _DataHd.list_mem()

# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("yaml Loader Test - Small → Big Pattern")
    print("=" * 70)
    
    # Write
    print("\n[WRITE Test] - data → name → dir_path")
    data = {"server": {"host": "localhost", "port": 8080}}
    write_yaml_base(data, "test_config")
    print("✓ Written: test_config.yaml")
    
    # Read
    print("\n[READ Test] - name → dir_path")
    result = read_yaml_base("test_config")
    print(f"✓ Read: {result}")
    
    # Update
    print("\n[UPDATE Test] - data → name → dir_path")
    update_yaml_base({"server": {"timeout": 30}}, "test_config")
    print("✓ Updated: test_config.yaml")
    
    # Exists
    print("\n[EXISTS Test] - name → dir_path")
    has = has_yaml_base("test_config")
    print(f"✓ Exists: {exists}")
    
    # Delete
    print("\n[DELETE Test] - name → dir_path")
    delete_yaml_base("test_config")
    print("✓ Deleted: test_config.yaml")
    
    # Dumps mode
    print("\n[DUMPS Test] - data only (no name)")
    yaml_str = write_yaml_base({"test": "value"})
    print(f"✓ Dumps: {yaml_str}")
    
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
def emit_yaml_mem(data=None, type=None, **kwargs):
    """Emit yaml data (memory-only serialization, no file I/O).

    Args:
        data: Data to serialize/deserialize.
        type: Output type - 's'(str), 'd'(dict), 'l'(list), 'b'(bytes).
    """
    return _DataHd.emit(data=data, type=type or "s", **kwargs)
