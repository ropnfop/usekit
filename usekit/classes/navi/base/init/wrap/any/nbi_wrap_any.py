# Path: usekit.classes.navi.base.init.wrap.any.nbi_wrap_any.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over NaviLd (IDE-friendly)
# Supports full argument set: (data, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.load.nbl_ops_loader import NaviLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_NaviHd = NaviLd("any")

# ─────────────────────────────────────────────────────────────────────────────
# PATH
# ─────────────────────────────────────────────────────────────────────────────
def path_any_base(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from BASE location."""
    return _NaviHd.path_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from SUB location."""
    return _NaviHd.path_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from DIR location."""
    return _NaviHd.path_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from NOW location."""
    return _NaviHd.path_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from TMP location."""
    return _NaviHd.path_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from CUSTOM preset location."""
    return _NaviHd.path_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path any file from CACHE location."""
    return _NaviHd.path_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# FIND
# ─────────────────────────────────────────────────────────────────────────────
def find_any_base(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from BASE location."""
    return _NaviHd.find_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from SUB location."""
    return _NaviHd.find_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from DIR location."""
    return _NaviHd.find_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from NOW location."""
    return _NaviHd.find_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from TMP location."""
    return _NaviHd.find_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from CUSTOM preset location."""
    return _NaviHd.find_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find any file from CACHE location."""
    return _NaviHd.find_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────────────────────
def list_any_base(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from BASE location."""
    return _NaviHd.list_base(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_any_sub(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from SUB location."""
    return _NaviHd.list_sub(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_any_dir(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from DIR location."""
    return _NaviHd.list_dir(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_any_now(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from NOW location."""
    return _NaviHd.list_now(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_any_tmp(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from TMP location."""
    return _NaviHd.list_tmp(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_any_pre(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from CUSTOM preset location."""
    return _NaviHd.list_pre(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_any_cache(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List any file from CACHE location."""
    return _NaviHd.list_cache(name=name, mod=mod, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# GET
# ─────────────────────────────────────────────────────────────────────────────
def get_any_base(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from BASE location."""
    return _NaviHd.get_base(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_sub(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from SUB location."""
    return _NaviHd.get_sub(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_dir(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from DIR location."""
    return _NaviHd.get_dir(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_now(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from NOW location."""
    return _NaviHd.get_now(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_tmp(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from TMP location."""
    return _NaviHd.get_tmp(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_pre(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from CUSTOM preset location."""
    return _NaviHd.get_pre(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_any_cache(name=None, mod=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get any file from CACHE location."""
    return _NaviHd.get_cache(name=name, mod=mod, dir_path=dir_path, op=op, restore=restore, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# SET
# ─────────────────────────────────────────────────────────────────────────────
def set_any_base(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to BASE location."""
    return _NaviHd.set_base(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_any_sub(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to SUB location."""
    return _NaviHd.set_sub(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_any_dir(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to DIR location."""
    return _NaviHd.set_dir(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_any_now(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to NOW location."""
    return _NaviHd.set_now(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_any_tmp(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to TMP location."""
    return _NaviHd.set_tmp(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_any_pre(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to CUSTOM preset location."""
    return _NaviHd.set_pre(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
def set_any_cache(data=None, name=None, mod=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set any file to CACHE location."""
    return _NaviHd.set_cache(data=data, name=name, mod=mod, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("any Loader Test - Small → Big Pattern")
    print("=" * 70)
       
    # Path
    print("\n[PATH Test] - name → dir_path")
    result = path_any_base()
    print(f"✓ Path: {result}")
    
    # Find
    print("\n[FIND Test] - data → name → dir_path")
    find_any_base("test")
    print("✓ find: test_config.any")
    
    # List
    print("\n[LIST Test] - data → name → dir_path")
    list_any_base("test_config")
    print("✓ List: test_config.any")
    
    # set
    print("\n[SET Test] - name → dir_path")
    set = set_any_base("test_config")
    print(f"✓ Set: {set}")
    
    # get
    print("\n[LIST Test] - name → dir_path")
    get_any_base("test_config")
    print("✓ get: test_config.any")
    
    print("\n" + "=" * 70)
    print("Pattern verified: Small → Big ✓")
    print("=" * 70)

if __name__ == "__main__":
    _test()

# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------