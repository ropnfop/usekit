# Path: usekit.classes.navi.base.init.wrap.txt.nbi_class_txt.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Txt-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Txt data IO loader
from usekit.classes.navi.base.init.wrap.txt.nbi_wrap_txt import (
    # PATH
    path_txt_base, path_txt_sub, path_txt_dir, path_txt_now, path_txt_tmp, path_txt_pre, path_txt_cache,
    # FIND
    find_txt_base, find_txt_sub, find_txt_dir, find_txt_now, find_txt_tmp, find_txt_pre, find_txt_cache,
    # LIST
    list_txt_base, list_txt_sub, list_txt_dir, list_txt_now, list_txt_tmp, list_txt_pre, list_txt_cache,
    # GET
    get_txt_base, get_txt_sub, get_txt_dir, get_txt_now, get_txt_tmp, get_txt_pre, get_txt_cache,
    # SET
    set_txt_base, set_txt_sub, set_txt_dir, set_txt_now, set_txt_tmp, set_txt_pre, set_txt_cache,
)

class TxtNVCore(SimpleNamespace):
    """
    Txt-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.txt.nbi_class_txt import TxtNV

        # Original style
        TxtNV.find.base(name="config")
        TxtNV.path.base()

        # Alias style (shorter)
        TxtNV.find.base(nm="config", stat=True)
        TxtNV.path.base(wk=True, stat=True)
        TxtNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_txt_base),
                sub=_wrap_simple_format(path_txt_sub),
                dir=_wrap_simple_format(path_txt_dir),
                now=_wrap_simple_format(path_txt_now),
                tmp=_wrap_simple_format(path_txt_tmp),
                pre=_wrap_simple_format(path_txt_pre),
                cache=_wrap_simple_format(path_txt_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_txt_base),
                sub=_wrap_simple_format(find_txt_sub),
                dir=_wrap_simple_format(find_txt_dir),
                now=_wrap_simple_format(find_txt_now),
                tmp=_wrap_simple_format(find_txt_tmp),
                pre=_wrap_simple_format(find_txt_pre),
                cache=_wrap_simple_format(find_txt_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_txt_base),
                sub=_wrap_simple_format(list_txt_sub),
                dir=_wrap_simple_format(list_txt_dir),
                now=_wrap_simple_format(list_txt_now),
                tmp=_wrap_simple_format(list_txt_tmp),
                pre=_wrap_simple_format(list_txt_pre),
                cache=_wrap_simple_format(list_txt_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_txt_base),
                sub=_wrap_simple_format(get_txt_sub),
                dir=_wrap_simple_format(get_txt_dir),
                now=_wrap_simple_format(get_txt_now),
                tmp=_wrap_simple_format(get_txt_tmp),
                pre=_wrap_simple_format(get_txt_pre),
                cache=_wrap_simple_format(get_txt_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_txt_base),
                sub=_wrap_simple_format(set_txt_sub),
                dir=_wrap_simple_format(set_txt_dir),
                now=_wrap_simple_format(set_txt_now),
                tmp=_wrap_simple_format(set_txt_tmp),
                pre=_wrap_simple_format(set_txt_pre),
                cache=_wrap_simple_format(set_txt_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
TxtNV = TxtNVCore()

__all__ = ["TxtNV", "TxtNVCore"]
