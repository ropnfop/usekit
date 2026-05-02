# Exec: usekit.classes.exec.base.init.wrap.ddl.ebi_wrap_ddl.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over ExecLd (IDE-friendly)
# Supports full argument set: (pattern, *args, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from usekit.classes.exec.base.load.ebl_ops_loader import ExecLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_ExecHd = ExecLd("ddl")

# ─────────────────────────────────────────────────────────────────────────────
# EXEC
# ─────────────────────────────────────────────────────────────────────────────
def exec_ddl_base(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from BASE location."""
    return _ExecHd.exec_base(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def exec_ddl_sub(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from SUB location."""
    return _ExecHd.exec_sub(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_ddl_dir(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from DIR location."""
    return _ExecHd.exec_dir(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_ddl_now(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from NOW location."""
    return _ExecHd.exec_now(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_ddl_tmp(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from TMP location."""
    return _ExecHd.exec_tmp(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def exec_ddl_pre(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from PRESET location."""
    return _ExecHd.exec_pre(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_ddl_cache(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec ddl file from CACHE location."""
    return _ExecHd.exec_cache(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT (no *args needed - import doesn't call functions)
# ─────────────────────────────────────────────────────────────────────────────
def import_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from BASE location."""
    return _ExecHd.import_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def import_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from SUB location."""
    return _ExecHd.import_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from DIR location."""
    return _ExecHd.import_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from NOW location."""
    return _ExecHd.import_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from TMP location."""
    return _ExecHd.import_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def import_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from PRESET location."""
    return _ExecHd.import_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import ddl file from CACHE location."""
    return _ExecHd.import_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# BOOT (no *args needed - boot doesn't call functions, just loads modules)
# ─────────────────────────────────────────────────────────────────────────────
def boot_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from BASE location."""
    return _ExecHd.boot_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def boot_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from SUB location."""
    return _ExecHd.boot_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from DIR location."""
    return _ExecHd.boot_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from NOW location."""
    return _ExecHd.boot_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from TMP location."""
    return _ExecHd.boot_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def boot_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from PRESET location."""
    return _ExecHd.boot_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot ddl file from CACHE location."""
    return _ExecHd.boot_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# CLOSE (no *args needed - close doesn't call functions)
# ─────────────────────────────────────────────────────────────────────────────
def close_ddl_base(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from BASE location."""
    return _ExecHd.close_base(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_sub(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from SUB location."""
    return _ExecHd.close_sub(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_dir(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from DIR location."""
    return _ExecHd.close_dir(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_now(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from NOW location."""
    return _ExecHd.close_now(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_tmp(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from TMP location."""
    return _ExecHd.close_tmp(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_pre(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from PRESET location."""
    return _ExecHd.close_pre(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_ddl_cache(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close ddl file from CACHE location."""
    return _ExecHd.close_cache(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)
    
# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------
