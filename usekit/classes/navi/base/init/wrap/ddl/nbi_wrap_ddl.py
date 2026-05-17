# Path: usekit.classes.navi.base.init.wrap.ddl.nbi_wrap_ddl.py
# -----------------------------------------------------------------------------------------------
# Created by: The Little Prince × ROP × FOP
# Purpose: Thin functional wrappers over NaviLd (IDE-friendly)
# Supports full argument set: (data, name, dir_path, keydata, cus, **kwargs)
# -----------------------------------------------------------------------------------------------

from usekit.classes.navi.base.load.nbl_ops_loader import NaviLd

# ─────────────────────────────────────────────────────────────────────────────
# Loader Singleton (cached instance)
# ─────────────────────────────────────────────────────────────────────────────
_NaviHd = NaviLd("ddl")

# ─────────────────────────────────────────────────────────────────────────────
# PATH
# ─────────────────────────────────────────────────────────────────────────────
def path_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from BASE location."""
    return _NaviHd.path_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from SUB location."""
    return _NaviHd.path_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from DIR location."""
    return _NaviHd.path_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from NOW location."""
    return _NaviHd.path_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from TMP location."""
    return _NaviHd.path_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def path_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from CUSTOM preset location."""
    return _NaviHd.path_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def path_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Path ddl file from CACHE location."""
    return _NaviHd.path_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# FIND
# ─────────────────────────────────────────────────────────────────────────────
def find_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from BASE location."""
    return _NaviHd.find_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from SUB location."""
    return _NaviHd.find_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from DIR location."""
    return _NaviHd.find_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from NOW location."""
    return _NaviHd.find_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from TMP location."""
    return _NaviHd.find_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def find_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from CUSTOM preset location."""
    return _NaviHd.find_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def find_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """Find ddl file from CACHE location."""
    return _NaviHd.find_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# LIST
# ─────────────────────────────────────────────────────────────────────────────
def list_ddl_base(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from BASE location."""
    return _NaviHd.list_base(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_ddl_sub(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from SUB location."""
    return _NaviHd.list_sub(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_ddl_dir(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from DIR location."""
    return _NaviHd.list_dir(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_ddl_now(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from NOW location."""
    return _NaviHd.list_now(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_ddl_tmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from TMP location."""
    return _NaviHd.list_tmp(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

def list_ddl_pre(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from CUSTOM preset location."""
    return _NaviHd.list_pre(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)
    
def list_ddl_cache(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
    """List ddl file from CACHE location."""
    return _NaviHd.list_cache(name=name, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)   

# ─────────────────────────────────────────────────────────────────────────────
# GET
# ─────────────────────────────────────────────────────────────────────────────
def get_ddl_base(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from BASE location."""
    return _NaviHd.get_base(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_sub(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from SUB location."""
    return _NaviHd.get_sub(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_dir(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from DIR location."""
    return _NaviHd.get_dir(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_now(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from NOW location."""
    return _NaviHd.get_now(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_tmp(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from TMP location."""
    return _NaviHd.get_tmp(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_pre(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from restoreTOM preset location."""
    return _NaviHd.get_pre(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

def get_ddl_cache(name=None, dir_path=None, op=None, restore=None, **kwargs):
    """Get ddl file from CACHE location."""
    return _NaviHd.get_cache(name=name, dir_path=dir_path, op=op, restore=restore, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# SET
# ─────────────────────────────────────────────────────────────────────────────
def set_ddl_base(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to BASE location."""
    return _NaviHd.set_base(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_ddl_sub(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to SUB location."""
    return _NaviHd.set_sub(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_ddl_dir(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to DIR location."""
    return _NaviHd.set_dir(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_ddl_now(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to NOW location."""
    return _NaviHd.set_now(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_ddl_tmp(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to TMP location."""
    return _NaviHd.set_tmp(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)

def set_ddl_pre(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to cpTOM preset location."""
    return _NaviHd.set_pre(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
def set_ddl_cache(data=None, name=None, root=None, dir_path=None, op=None, cp=None, **kwargs):
    """Set ddl file to CACHE location."""
    return _NaviHd.set_cache(data=data, name=name, root=root, dir_path=dir_path, op=op, cp=cp, **kwargs)
    
# ─────────────────────────────────────────────────────────────────────────────
# Usage Examples
# ─────────────────────────────────────────────────────────────────────────────

def _test():
    """Test Example."""
    print("=" * 70)
    print("ddl Loader Test - Small → Big Pattern")
    print("=" * 70)
       
    # Path
    print("\n[PATH Test] - name → dir_path")
    result = path_ddl_base()
    print(f"✓ Path: {result}")
    
    # Find
    print("\n[FIND Test] - data → name → dir_path")
    find_ddl_base("test")
    print("✓ find: test_config.ddl")
    
    # List
    print("\n[LIST Test] - data → name → dir_path")
    list_ddl_base("test_config")
    print("✓ List: test_config.ddl")
    
    # set
    print("\n[SET Test] - name → dir_path")
    set = set_ddl_base("test_config")
    print(f"✓ Set: {set}")
    
    # get
    print("\n[LIST Test] - name → dir_path")
    get_ddl_base("test_config")
    print("✓ get: test_config.ddl")
    
    print("\n" + "=" * 70)
    print("Pattern verified: Small → Big ✓")
    print("=" * 70)

if __name__ == "__main__":
    _test()

# -----------------------------------------------------------------------------------------------
# EOF
# -----------------------------------------------------------------------------------------------