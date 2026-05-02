# Path: usekit.classes.navi.base.init.wrap.json.nbi_class_json.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Json-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Json data IO loader
from usekit.classes.navi.base.init.wrap.json.nbi_wrap_json import (
    # PATH
    path_json_base, path_json_sub, path_json_dir, path_json_now, path_json_tmp, path_json_pre, path_json_cache,
    # FIND
    find_json_base, find_json_sub, find_json_dir, find_json_now, find_json_tmp, find_json_pre, find_json_cache,
    # LIST
    list_json_base, list_json_sub, list_json_dir, list_json_now, list_json_tmp, list_json_pre, list_json_cache,
    # GET
    get_json_base, get_json_sub, get_json_dir, get_json_now, get_json_tmp, get_json_pre, get_json_cache,
    # SET
    set_json_base, set_json_sub, set_json_dir, set_json_now, set_json_tmp, set_json_pre, set_json_cache,
)

class JsonNVCore(SimpleNamespace):
    """
    Json-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.json.nbi_class_json import JsonNV

        # Original style
        JsonNV.find.base(name="config")
        JsonNV.path.base()

        # Alias style (shorter)
        JsonNV.find.base(nm="config", stat=True)
        JsonNV.path.base(wk=True, stat=True)
        JsonNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_json_base),
                sub=_wrap_simple_format(path_json_sub),
                dir=_wrap_simple_format(path_json_dir),
                now=_wrap_simple_format(path_json_now),
                tmp=_wrap_simple_format(path_json_tmp),
                pre=_wrap_simple_format(path_json_pre),
                cache=_wrap_simple_format(path_json_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_json_base),
                sub=_wrap_simple_format(find_json_sub),
                dir=_wrap_simple_format(find_json_dir),
                now=_wrap_simple_format(find_json_now),
                tmp=_wrap_simple_format(find_json_tmp),
                pre=_wrap_simple_format(find_json_pre),
                cache=_wrap_simple_format(find_json_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_json_base),
                sub=_wrap_simple_format(list_json_sub),
                dir=_wrap_simple_format(list_json_dir),
                now=_wrap_simple_format(list_json_now),
                tmp=_wrap_simple_format(list_json_tmp),
                pre=_wrap_simple_format(list_json_pre),
                cache=_wrap_simple_format(list_json_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_json_base),
                sub=_wrap_simple_format(get_json_sub),
                dir=_wrap_simple_format(get_json_dir),
                now=_wrap_simple_format(get_json_now),
                tmp=_wrap_simple_format(get_json_tmp),
                pre=_wrap_simple_format(get_json_pre),
                cache=_wrap_simple_format(get_json_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_json_base),
                sub=_wrap_simple_format(set_json_sub),
                dir=_wrap_simple_format(set_json_dir),
                now=_wrap_simple_format(set_json_now),
                tmp=_wrap_simple_format(set_json_tmp),
                pre=_wrap_simple_format(set_json_pre),
                cache=_wrap_simple_format(set_json_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
JsonNV = JsonNVCore()

__all__ = ["JsonNV", "JsonNVCore"]
