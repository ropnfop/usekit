# Exec: usekit.classes.exec.base.init.wrap.pyp.ebi_wrap_pyp.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over ExecLd (IDE-friendly)
# Supports full argument set: (pattern, *args, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from usekit.classes.exec.base.load.ebl_ops_loader import ExecLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_ExecHd = ExecLd("pyp")

# ─────────────────────────────────────────────────────────────────────────────
# EXEC
# ─────────────────────────────────────────────────────────────────────────────
def exec_pyp_base(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from BASE location."""
    return _ExecHd.exec_base(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def exec_pyp_sub(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from SUB location."""
    return _ExecHd.exec_sub(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_pyp_dir(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from DIR location."""
    return _ExecHd.exec_dir(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_pyp_now(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from NOW location."""
    return _ExecHd.exec_now(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_pyp_tmp(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from TMP location."""
    return _ExecHd.exec_tmp(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def exec_pyp_pre(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from PRESET location."""
    return _ExecHd.exec_pre(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def exec_pyp_cache(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
    """Exec pyp file from CACHE location."""
    return _ExecHd.exec_cache(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# IMPORT (no *args needed - import doesn't call functions)
# ─────────────────────────────────────────────────────────────────────────────
def import_pyp_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from BASE location."""
    return _ExecHd.import_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def import_pyp_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from SUB location."""
    return _ExecHd.import_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_pyp_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from DIR location."""
    return _ExecHd.import_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_pyp_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from NOW location."""
    return _ExecHd.import_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_pyp_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from TMP location."""
    return _ExecHd.import_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def import_pyp_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from PRESET location."""
    return _ExecHd.import_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def import_pyp_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Import pyp file from CACHE location."""
    return _ExecHd.import_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# BOOT (no *args needed - boot doesn't call functions, just loads modules)
# ─────────────────────────────────────────────────────────────────────────────
def boot_pyp_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from BASE location."""
    return _ExecHd.boot_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def boot_pyp_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from SUB location."""
    return _ExecHd.boot_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_pyp_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from DIR location."""
    return _ExecHd.boot_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_pyp_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from NOW location."""
    return _ExecHd.boot_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_pyp_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from TMP location."""
    return _ExecHd.boot_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def boot_pyp_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from PRESET location."""
    return _ExecHd.boot_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def boot_pyp_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Boot pyp file from CACHE location."""
    return _ExecHd.boot_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# CLOSE (no *args needed - close doesn't call functions)
# ─────────────────────────────────────────────────────────────────────────────
def close_pyp_base(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from BASE location."""
    return _ExecHd.close_base(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_sub(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from SUB location."""
    return _ExecHd.close_sub(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_dir(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from DIR location."""
    return _ExecHd.close_dir(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_now(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from NOW location."""
    return _ExecHd.close_now(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_tmp(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from TMP location."""
    return _ExecHd.close_tmp(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_pre(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from PRESET location."""
    return _ExecHd.close_pre(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def close_pyp_cache(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Close pyp file from CACHE location."""
    return _ExecHd.close_cache(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)
    
# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------
