# Path: usekit.classes.navi.base.init.wrap.pyp.nbi_wrap_pyp.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over NaviLd (IDE-friendly)
# Supports full argument set: (data, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.load.nbl_ops_loader import NaviLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_NaviHd = NaviLd("pyp")

# ─────────────────────────────────────────────────────────────────────────────
# PATH
# ─────────────────────────────────────────────────────────────────────────────
def path_pyp_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from BASE location."""
    return _NaviHd.path_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_pyp_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from SUB location."""
    return _NaviHd.path_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_pyp_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from DIR location."""
    return _NaviHd.path_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_pyp_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from NOW location."""
    return _NaviHd.path_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_pyp_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from TMP location."""
    return _NaviHd.path_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_pyp_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from CUSTOM preset location."""
    return _NaviHd.path_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_pyp_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path pyp file from CACHE location."""
    return _NaviHd.path_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# FIND
# ─────────────────────────────────────────────────────────────────────────────
def find_pyp_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from BASE location."""
    return _NaviHd.find_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_pyp_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from SUB location."""
    return _NaviHd.find_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_pyp_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from DIR location."""
    return _NaviHd.find_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_pyp_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from NOW location."""
    return _NaviHd.find_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_pyp_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from TMP location."""
    return _NaviHd.find_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_pyp_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from CUSTOM preset location."""
    return _NaviHd.find_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_pyp_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find pyp file from CACHE location."""
    return _NaviHd.find_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────────────────────
def list_pyp_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from BASE location."""
    return _NaviHd.list_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_pyp_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from SUB location."""
    return _NaviHd.list_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_pyp_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from DIR location."""
    return _NaviHd.list_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_pyp_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from NOW location."""
    return _NaviHd.list_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_pyp_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from TMP location."""
    return _NaviHd.list_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_pyp_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from CUSTOM preset location."""
    return _NaviHd.list_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_pyp_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List pyp file from CACHE location."""
    return _NaviHd.list_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# GET
# ─────────────────────────────────────────────────────────────────────────────
def get_pyp_base(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from BASE location."""
    return _NaviHd.get_base(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_sub(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from SUB location."""
    return _NaviHd.get_sub(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_dir(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from DIR location."""
    return _NaviHd.get_dir(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_now(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from NOW location."""
    return _NaviHd.get_now(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_tmp(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from TMP location."""
    return _NaviHd.get_tmp(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_pre(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from restoreTOM preset location."""
    return _NaviHd.get_pre(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_pyp_cache(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get pyp file from CACHE location."""
    return _NaviHd.get_cache(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# SET
# ─────────────────────────────────────────────────────────────────────────────
def set_pyp_base(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to BASE location."""
    return _NaviHd.set_base(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_pyp_sub(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to SUB location."""
    return _NaviHd.set_sub(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_pyp_dir(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to DIR location."""
    return _NaviHd.set_dir(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_pyp_now(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to NOW location."""
    return _NaviHd.set_now(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_pyp_tmp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to TMP location."""
    return _NaviHd.set_tmp(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_pyp_pre(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to cpTOM preset location."""
    return _NaviHd.set_pre(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
def set_pyp_cache(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set pyp file to CACHE location."""
    return _NaviHd.set_cache(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("pyp Loader Test - Small → Big Pattern")
    print("=" * 70)
       
    # Path
    print("\n[PATH Test] - name → dir_path")
    result = path_pyp_base()
    print(f"✓ Path: {result}")
    
    # Find
    print("\n[FIND Test] - data → name → dir_path")
    find_pyp_base("test")
    print("✓ find: test_config.pyp")
    
    # List
    print("\n[LIST Test] - data → name → dir_path")
    list_pyp_base("test_config")
    print("✓ List: test_config.pyp")
    
    # set
    print("\n[SET Test] - name → dir_path")
    set = set_pyp_base("test_config")
    print(f"✓ Set: {set}")
    
    # get
    print("\n[LIST Test] - name → dir_path")
    get_pyp_base("test_config")
    print("✓ get: test_config.pyp")
    
    print("\n" + "=" * 70)
    print("Pattern verified: Small → Big ✓")
    print("=" * 70)

if __name__ == "__main__":
    _test()

# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------