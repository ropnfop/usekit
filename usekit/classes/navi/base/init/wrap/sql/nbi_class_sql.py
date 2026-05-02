# Path: usekit.classes.navi.base.init.wrap.sql.nbi_class_sql.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Sql-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Sql data IO loader
from usekit.classes.navi.base.init.wrap.sql.nbi_wrap_sql import (
    # PATH
    path_sql_base, path_sql_sub, path_sql_dir, path_sql_now, path_sql_tmp, path_sql_pre, path_sql_cache,
    # FIND
    find_sql_base, find_sql_sub, find_sql_dir, find_sql_now, find_sql_tmp, find_sql_pre, find_sql_cache,
    # LIST
    list_sql_base, list_sql_sub, list_sql_dir, list_sql_now, list_sql_tmp, list_sql_pre, list_sql_cache,
    # GET
    get_sql_base, get_sql_sub, get_sql_dir, get_sql_now, get_sql_tmp, get_sql_pre, get_sql_cache,
    # SET
    set_sql_base, set_sql_sub, set_sql_dir, set_sql_now, set_sql_tmp, set_sql_pre, set_sql_cache,
)

class SqlNVCore(SimpleNamespace):
    """
    Sql-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.sql.nbi_class_sql import SqlNV

        # Original style
        SqlNV.find.base(name="config")
        SqlNV.path.base()

        # Alias style (shorter)
        SqlNV.find.base(nm="config", stat=True)
        SqlNV.path.base(wk=True, stat=True)
        SqlNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_sql_base),
                sub=_wrap_simple_format(path_sql_sub),
                dir=_wrap_simple_format(path_sql_dir),
                now=_wrap_simple_format(path_sql_now),
                tmp=_wrap_simple_format(path_sql_tmp),
                pre=_wrap_simple_format(path_sql_pre),
                cache=_wrap_simple_format(path_sql_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_sql_base),
                sub=_wrap_simple_format(find_sql_sub),
                dir=_wrap_simple_format(find_sql_dir),
                now=_wrap_simple_format(find_sql_now),
                tmp=_wrap_simple_format(find_sql_tmp),
                pre=_wrap_simple_format(find_sql_pre),
                cache=_wrap_simple_format(find_sql_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_sql_base),
                sub=_wrap_simple_format(list_sql_sub),
                dir=_wrap_simple_format(list_sql_dir),
                now=_wrap_simple_format(list_sql_now),
                tmp=_wrap_simple_format(list_sql_tmp),
                pre=_wrap_simple_format(list_sql_pre),
                cache=_wrap_simple_format(list_sql_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_sql_base),
                sub=_wrap_simple_format(get_sql_sub),
                dir=_wrap_simple_format(get_sql_dir),
                now=_wrap_simple_format(get_sql_now),
                tmp=_wrap_simple_format(get_sql_tmp),
                pre=_wrap_simple_format(get_sql_pre),
                cache=_wrap_simple_format(get_sql_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_sql_base),
                sub=_wrap_simple_format(set_sql_sub),
                dir=_wrap_simple_format(set_sql_dir),
                now=_wrap_simple_format(set_sql_now),
                tmp=_wrap_simple_format(set_sql_tmp),
                pre=_wrap_simple_format(set_sql_pre),
                cache=_wrap_simple_format(set_sql_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
SqlNV = SqlNVCore()

__all__ = ["SqlNV", "SqlNVCore"]
