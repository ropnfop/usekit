# Path: usekit.classes.navi.base.init.wrap.pyp.nbi_class_pyp.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Pyp-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Pyp data IO loader
from usekit.classes.navi.base.init.wrap.pyp.nbi_wrap_pyp import (
    # PATH
    path_pyp_base, path_pyp_sub, path_pyp_dir, path_pyp_now, path_pyp_tmp, path_pyp_pre, path_pyp_cache,
    # FIND
    find_pyp_base, find_pyp_sub, find_pyp_dir, find_pyp_now, find_pyp_tmp, find_pyp_pre, find_pyp_cache,
    # LIST
    list_pyp_base, list_pyp_sub, list_pyp_dir, list_pyp_now, list_pyp_tmp, list_pyp_pre, list_pyp_cache,
    # GET
    get_pyp_base, get_pyp_sub, get_pyp_dir, get_pyp_now, get_pyp_tmp, get_pyp_pre, get_pyp_cache,
    # SET
    set_pyp_base, set_pyp_sub, set_pyp_dir, set_pyp_now, set_pyp_tmp, set_pyp_pre, set_pyp_cache,
)

class PypNVCore(SimpleNamespace):
    """
    Pyp-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.pyp.nbi_class_pyp import PypNV

        # Original style
        PypNV.find.base(name="config")
        PypNV.path.base()

        # Alias style (shorter)
        PypNV.find.base(nm="config", stat=True)
        PypNV.path.base(wk=True, stat=True)
        PypNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_pyp_base),
                sub=_wrap_simple_format(path_pyp_sub),
                dir=_wrap_simple_format(path_pyp_dir),
                now=_wrap_simple_format(path_pyp_now),
                tmp=_wrap_simple_format(path_pyp_tmp),
                pre=_wrap_simple_format(path_pyp_pre),
                cache=_wrap_simple_format(path_pyp_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_pyp_base),
                sub=_wrap_simple_format(find_pyp_sub),
                dir=_wrap_simple_format(find_pyp_dir),
                now=_wrap_simple_format(find_pyp_now),
                tmp=_wrap_simple_format(find_pyp_tmp),
                pre=_wrap_simple_format(find_pyp_pre),
                cache=_wrap_simple_format(find_pyp_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_pyp_base),
                sub=_wrap_simple_format(list_pyp_sub),
                dir=_wrap_simple_format(list_pyp_dir),
                now=_wrap_simple_format(list_pyp_now),
                tmp=_wrap_simple_format(list_pyp_tmp),
                pre=_wrap_simple_format(list_pyp_pre),
                cache=_wrap_simple_format(list_pyp_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_pyp_base),
                sub=_wrap_simple_format(get_pyp_sub),
                dir=_wrap_simple_format(get_pyp_dir),
                now=_wrap_simple_format(get_pyp_now),
                tmp=_wrap_simple_format(get_pyp_tmp),
                pre=_wrap_simple_format(get_pyp_pre),
                cache=_wrap_simple_format(get_pyp_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_pyp_base),
                sub=_wrap_simple_format(set_pyp_sub),
                dir=_wrap_simple_format(set_pyp_dir),
                now=_wrap_simple_format(set_pyp_now),
                tmp=_wrap_simple_format(set_pyp_tmp),
                pre=_wrap_simple_format(set_pyp_pre),
                cache=_wrap_simple_format(set_pyp_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
PypNV = PypNVCore()

__all__ = ["PypNV", "PypNVCore"]
