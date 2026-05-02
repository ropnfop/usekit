# Path: usekit.classes.navi.base.init.wrap.any.nbi_class_any.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Any-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Any data IO loader
from usekit.classes.navi.base.init.wrap.any.nbi_wrap_any import (
    # PATH
    path_any_base, path_any_sub, path_any_dir, path_any_now, path_any_tmp, path_any_pre, path_any_cache,
    # FIND
    find_any_base, find_any_sub, find_any_dir, find_any_now, find_any_tmp, find_any_pre, find_any_cache,
    # LIST
    list_any_base, list_any_sub, list_any_dir, list_any_now, list_any_tmp, list_any_pre, list_any_cache,
    # GET
    get_any_base, get_any_sub, get_any_dir, get_any_now, get_any_tmp, get_any_pre, get_any_cache,
    # SET
    set_any_base, set_any_sub, set_any_dir, set_any_now, set_any_tmp, set_any_pre, set_any_cache,
)

class AnyNVCore(SimpleNamespace):
    """
    Any-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.any.nbi_class_any import AnyNV

        # Original style
        AnyNV.find.base(name="config")
        AnyNV.path.base()

        # Alias style (shorter)
        AnyNV.find.base(nm="config", stat=True)
        AnyNV.path.base(wk=True, stat=True)
        AnyNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_any_base),
                sub=_wrap_simple_format(path_any_sub),
                dir=_wrap_simple_format(path_any_dir),
                now=_wrap_simple_format(path_any_now),
                tmp=_wrap_simple_format(path_any_tmp),
                pre=_wrap_simple_format(path_any_pre),
                cache=_wrap_simple_format(path_any_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_any_base),
                sub=_wrap_simple_format(find_any_sub),
                dir=_wrap_simple_format(find_any_dir),
                now=_wrap_simple_format(find_any_now),
                tmp=_wrap_simple_format(find_any_tmp),
                pre=_wrap_simple_format(find_any_pre),
                cache=_wrap_simple_format(find_any_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_any_base),
                sub=_wrap_simple_format(list_any_sub),
                dir=_wrap_simple_format(list_any_dir),
                now=_wrap_simple_format(list_any_now),
                tmp=_wrap_simple_format(list_any_tmp),
                pre=_wrap_simple_format(list_any_pre),
                cache=_wrap_simple_format(list_any_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_any_base),
                sub=_wrap_simple_format(get_any_sub),
                dir=_wrap_simple_format(get_any_dir),
                now=_wrap_simple_format(get_any_now),
                tmp=_wrap_simple_format(get_any_tmp),
                pre=_wrap_simple_format(get_any_pre),
                cache=_wrap_simple_format(get_any_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_any_base),
                sub=_wrap_simple_format(set_any_sub),
                dir=_wrap_simple_format(set_any_dir),
                now=_wrap_simple_format(set_any_now),
                tmp=_wrap_simple_format(set_any_tmp),
                pre=_wrap_simple_format(set_any_pre),
                cache=_wrap_simple_format(set_any_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
AnyNV = AnyNVCore()

__all__ = ["AnyNV", "AnyNVCore"]
