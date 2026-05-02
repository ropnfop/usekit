# Path: usekit.classes.navi.base.init.wrap.csv.nbi_class_csv.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Csv-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Csv data IO loader
from usekit.classes.navi.base.init.wrap.csv.nbi_wrap_csv import (
    # PATH
    path_csv_base, path_csv_sub, path_csv_dir, path_csv_now, path_csv_tmp, path_csv_pre, path_csv_cache,
    # FIND
    find_csv_base, find_csv_sub, find_csv_dir, find_csv_now, find_csv_tmp, find_csv_pre, find_csv_cache,
    # LIST
    list_csv_base, list_csv_sub, list_csv_dir, list_csv_now, list_csv_tmp, list_csv_pre, list_csv_cache,
    # GET
    get_csv_base, get_csv_sub, get_csv_dir, get_csv_now, get_csv_tmp, get_csv_pre, get_csv_cache,
    # SET
    set_csv_base, set_csv_sub, set_csv_dir, set_csv_now, set_csv_tmp, set_csv_pre, set_csv_cache,
)

class CsvNVCore(SimpleNamespace):
    """
    Csv-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.csv.nbi_class_csv import CsvNV

        # Original style
        CsvNV.find.base(name="config")
        CsvNV.path.base()

        # Alias style (shorter)
        CsvNV.find.base(nm="config", stat=True)
        CsvNV.path.base(wk=True, stat=True)
        CsvNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_csv_base),
                sub=_wrap_simple_format(path_csv_sub),
                dir=_wrap_simple_format(path_csv_dir),
                now=_wrap_simple_format(path_csv_now),
                tmp=_wrap_simple_format(path_csv_tmp),
                pre=_wrap_simple_format(path_csv_pre),
                cache=_wrap_simple_format(path_csv_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_csv_base),
                sub=_wrap_simple_format(find_csv_sub),
                dir=_wrap_simple_format(find_csv_dir),
                now=_wrap_simple_format(find_csv_now),
                tmp=_wrap_simple_format(find_csv_tmp),
                pre=_wrap_simple_format(find_csv_pre),
                cache=_wrap_simple_format(find_csv_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_csv_base),
                sub=_wrap_simple_format(list_csv_sub),
                dir=_wrap_simple_format(list_csv_dir),
                now=_wrap_simple_format(list_csv_now),
                tmp=_wrap_simple_format(list_csv_tmp),
                pre=_wrap_simple_format(list_csv_pre),
                cache=_wrap_simple_format(list_csv_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_csv_base),
                sub=_wrap_simple_format(get_csv_sub),
                dir=_wrap_simple_format(get_csv_dir),
                now=_wrap_simple_format(get_csv_now),
                tmp=_wrap_simple_format(get_csv_tmp),
                pre=_wrap_simple_format(get_csv_pre),
                cache=_wrap_simple_format(get_csv_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_csv_base),
                sub=_wrap_simple_format(set_csv_sub),
                dir=_wrap_simple_format(set_csv_dir),
                now=_wrap_simple_format(set_csv_now),
                tmp=_wrap_simple_format(set_csv_tmp),
                pre=_wrap_simple_format(set_csv_pre),
                cache=_wrap_simple_format(set_csv_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
CsvNV = CsvNVCore()

__all__ = ["CsvNV", "CsvNVCore"]
