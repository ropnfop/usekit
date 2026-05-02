# Path: usekit.classes.navi.base.init.wrap.md.nbi_class_md.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Md-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Md data IO loader
from usekit.classes.navi.base.init.wrap.md.nbi_wrap_md import (
    # PATH
    path_md_base, path_md_sub, path_md_dir, path_md_now, path_md_tmp, path_md_pre, path_md_cache,
    # FIND
    find_md_base, find_md_sub, find_md_dir, find_md_now, find_md_tmp, find_md_pre, find_md_cache,
    # LIST
    list_md_base, list_md_sub, list_md_dir, list_md_now, list_md_tmp, list_md_pre, list_md_cache,
    # GET
    get_md_base, get_md_sub, get_md_dir, get_md_now, get_md_tmp, get_md_pre, get_md_cache,
    # SET
    set_md_base, set_md_sub, set_md_dir, set_md_now, set_md_tmp, set_md_pre, set_md_cache,
)

class MdNVCore(SimpleNamespace):
    """
    Md-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.md.nbi_class_md import MdNV

        # Original style
        MdNV.find.base(name="config")
        MdNV.path.base()

        # Alias style (shorter)
        MdNV.find.base(nm="config", stat=True)
        MdNV.path.base(wk=True, stat=True)
        MdNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_md_base),
                sub=_wrap_simple_format(path_md_sub),
                dir=_wrap_simple_format(path_md_dir),
                now=_wrap_simple_format(path_md_now),
                tmp=_wrap_simple_format(path_md_tmp),
                pre=_wrap_simple_format(path_md_pre),
                cache=_wrap_simple_format(path_md_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_md_base),
                sub=_wrap_simple_format(find_md_sub),
                dir=_wrap_simple_format(find_md_dir),
                now=_wrap_simple_format(find_md_now),
                tmp=_wrap_simple_format(find_md_tmp),
                pre=_wrap_simple_format(find_md_pre),
                cache=_wrap_simple_format(find_md_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_md_base),
                sub=_wrap_simple_format(list_md_sub),
                dir=_wrap_simple_format(list_md_dir),
                now=_wrap_simple_format(list_md_now),
                tmp=_wrap_simple_format(list_md_tmp),
                pre=_wrap_simple_format(list_md_pre),
                cache=_wrap_simple_format(list_md_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_md_base),
                sub=_wrap_simple_format(get_md_sub),
                dir=_wrap_simple_format(get_md_dir),
                now=_wrap_simple_format(get_md_now),
                tmp=_wrap_simple_format(get_md_tmp),
                pre=_wrap_simple_format(get_md_pre),
                cache=_wrap_simple_format(get_md_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_md_base),
                sub=_wrap_simple_format(set_md_sub),
                dir=_wrap_simple_format(set_md_dir),
                now=_wrap_simple_format(set_md_now),
                tmp=_wrap_simple_format(set_md_tmp),
                pre=_wrap_simple_format(set_md_pre),
                cache=_wrap_simple_format(set_md_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
MdNV = MdNVCore()

__all__ = ["MdNV", "MdNVCore"]
