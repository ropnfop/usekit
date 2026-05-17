# Path: usekit.classes.navi.base.init.wrap.km.nbi_class_km.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Km-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Km data IO loader
from usekit.classes.navi.base.init.wrap.km.nbi_wrap_km import (
    # PATH
    path_km_base, path_km_sub, path_km_dir, path_km_now, path_km_tmp, path_km_pre, path_km_cache,
    # FIND
    find_km_base, find_km_sub, find_km_dir, find_km_now, find_km_tmp, find_km_pre, find_km_cache,
    # LIST
    list_km_base, list_km_sub, list_km_dir, list_km_now, list_km_tmp, list_km_pre, list_km_cache,
    # GET
    get_km_base, get_km_sub, get_km_dir, get_km_now, get_km_tmp, get_km_pre, get_km_cache,
    # SET
    set_km_base, set_km_sub, set_km_dir, set_km_now, set_km_tmp, set_km_pre, set_km_cache,
)

class KmNVCore(SimpleNamespace):
    """
    Km-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.km.nbi_class_km import KmNV

        # Original style
        KmNV.find.base(name="config")
        KmNV.path.base()

        # Alias style (shorter)
        KmNV.find.base(nm="config", stat=True)
        KmNV.path.base(wk=True, stat=True)
        KmNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_km_base),
                sub=_wrap_simple_format(path_km_sub),
                dir=_wrap_simple_format(path_km_dir),
                now=_wrap_simple_format(path_km_now),
                tmp=_wrap_simple_format(path_km_tmp),
                pre=_wrap_simple_format(path_km_pre),
                cache=_wrap_simple_format(path_km_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_km_base),
                sub=_wrap_simple_format(find_km_sub),
                dir=_wrap_simple_format(find_km_dir),
                now=_wrap_simple_format(find_km_now),
                tmp=_wrap_simple_format(find_km_tmp),
                pre=_wrap_simple_format(find_km_pre),
                cache=_wrap_simple_format(find_km_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_km_base),
                sub=_wrap_simple_format(list_km_sub),
                dir=_wrap_simple_format(list_km_dir),
                now=_wrap_simple_format(list_km_now),
                tmp=_wrap_simple_format(list_km_tmp),
                pre=_wrap_simple_format(list_km_pre),
                cache=_wrap_simple_format(list_km_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_km_base),
                sub=_wrap_simple_format(get_km_sub),
                dir=_wrap_simple_format(get_km_dir),
                now=_wrap_simple_format(get_km_now),
                tmp=_wrap_simple_format(get_km_tmp),
                pre=_wrap_simple_format(get_km_pre),
                cache=_wrap_simple_format(get_km_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_km_base),
                sub=_wrap_simple_format(set_km_sub),
                dir=_wrap_simple_format(set_km_dir),
                now=_wrap_simple_format(set_km_now),
                tmp=_wrap_simple_format(set_km_tmp),
                pre=_wrap_simple_format(set_km_pre),
                cache=_wrap_simple_format(set_km_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
KmNV = KmNVCore()

__all__ = ["KmNV", "KmNVCore"]
