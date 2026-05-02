# Path: usekit.classes.navi.base.init.wrap.ddl.nbi_class_ddl.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Ddl-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Ddl data IO loader
from usekit.classes.navi.base.init.wrap.ddl.nbi_wrap_ddl import (
    # PATH
    path_ddl_base, path_ddl_sub, path_ddl_dir, path_ddl_now, path_ddl_tmp, path_ddl_pre, path_ddl_cache,
    # FIND
    find_ddl_base, find_ddl_sub, find_ddl_dir, find_ddl_now, find_ddl_tmp, find_ddl_pre, find_ddl_cache,
    # LIST
    list_ddl_base, list_ddl_sub, list_ddl_dir, list_ddl_now, list_ddl_tmp, list_ddl_pre, list_ddl_cache,
    # GET
    get_ddl_base, get_ddl_sub, get_ddl_dir, get_ddl_now, get_ddl_tmp, get_ddl_pre, get_ddl_cache,
    # SET
    set_ddl_base, set_ddl_sub, set_ddl_dir, set_ddl_now, set_ddl_tmp, set_ddl_pre, set_ddl_cache,
)

class DdlNVCore(SimpleNamespace):
    """
    Ddl-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.ddl.nbi_class_ddl import DdlNV

        # Original style
        DdlNV.find.base(name="config")
        DdlNV.path.base()

        # Alias style (shorter)
        DdlNV.find.base(nm="config", stat=True)
        DdlNV.path.base(wk=True, stat=True)
        DdlNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_ddl_base),
                sub=_wrap_simple_format(path_ddl_sub),
                dir=_wrap_simple_format(path_ddl_dir),
                now=_wrap_simple_format(path_ddl_now),
                tmp=_wrap_simple_format(path_ddl_tmp),
                pre=_wrap_simple_format(path_ddl_pre),
                cache=_wrap_simple_format(path_ddl_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_ddl_base),
                sub=_wrap_simple_format(find_ddl_sub),
                dir=_wrap_simple_format(find_ddl_dir),
                now=_wrap_simple_format(find_ddl_now),
                tmp=_wrap_simple_format(find_ddl_tmp),
                pre=_wrap_simple_format(find_ddl_pre),
                cache=_wrap_simple_format(find_ddl_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_ddl_base),
                sub=_wrap_simple_format(list_ddl_sub),
                dir=_wrap_simple_format(list_ddl_dir),
                now=_wrap_simple_format(list_ddl_now),
                tmp=_wrap_simple_format(list_ddl_tmp),
                pre=_wrap_simple_format(list_ddl_pre),
                cache=_wrap_simple_format(list_ddl_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_ddl_base),
                sub=_wrap_simple_format(get_ddl_sub),
                dir=_wrap_simple_format(get_ddl_dir),
                now=_wrap_simple_format(get_ddl_now),
                tmp=_wrap_simple_format(get_ddl_tmp),
                pre=_wrap_simple_format(get_ddl_pre),
                cache=_wrap_simple_format(get_ddl_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_ddl_base),
                sub=_wrap_simple_format(set_ddl_sub),
                dir=_wrap_simple_format(set_ddl_dir),
                now=_wrap_simple_format(set_ddl_now),
                tmp=_wrap_simple_format(set_ddl_tmp),
                pre=_wrap_simple_format(set_ddl_pre),
                cache=_wrap_simple_format(set_ddl_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
DdlNV = DdlNVCore()

__all__ = ["DdlNV", "DdlNVCore"]
