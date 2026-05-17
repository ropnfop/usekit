# Path: usekit.classes.exec.base.init.wrap.sql.ebi_class_sql.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Sql-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_exec, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import _wrap_exec_operation
# [1] Sql data IO loader
from usekit.classes.exec.base.init.wrap.sql.ebi_wrap_sql import (
    # EXEC
    exec_sql_base, exec_sql_sub, exec_sql_dir, exec_sql_now, exec_sql_tmp, exec_sql_pre, exec_sql_cache,
    # import
    import_sql_base, import_sql_sub, import_sql_dir, import_sql_now, import_sql_tmp, import_sql_pre, import_sql_cache,
    # boot
    boot_sql_base, boot_sql_sub, boot_sql_dir, boot_sql_now, boot_sql_tmp, boot_sql_pre, boot_sql_cache,
    # CLOSE
    close_sql_base, close_sql_sub, close_sql_dir, close_sql_now, close_sql_tmp, close_sql_pre, close_sql_cache,
)

class SqlEXCore(SimpleNamespace):
    """
    Sql-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.exec.base.wrap.sql.ebi_class_sql import SqlEX

        # Original style
        SqlEX.imp.base(name="config")
        SqlEX.exec.base()

        # Alias style (shorter)
        SqlEX.imp.base(nm="config", stat=True)
        SqlEX.exec.base(wk=True, stat=True)
        SqlEX.set.base(dp="myjob", op="exec")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            exec=SimpleNamespace(
                base=_wrap_exec_operation(exec_sql_base),
                sub=_wrap_exec_operation(exec_sql_sub),
                dir=_wrap_exec_operation(exec_sql_dir),
                now=_wrap_exec_operation(exec_sql_now),
                tmp=_wrap_exec_operation(exec_sql_tmp),
                pre=_wrap_exec_operation(exec_sql_pre),
                cache=_wrap_exec_operation(exec_sql_cache),
            ),
            imp=SimpleNamespace(
                base=_wrap_exec_operation(import_sql_base),
                sub=_wrap_exec_operation(import_sql_sub),
                dir=_wrap_exec_operation(import_sql_dir),
                now=_wrap_exec_operation(import_sql_now),
                tmp=_wrap_exec_operation(import_sql_tmp),
                pre=_wrap_exec_operation(import_sql_pre),
                cache=_wrap_exec_operation(import_sql_cache),           
            ),
            boot=SimpleNamespace(
                base=_wrap_exec_operation(boot_sql_base),
                sub=_wrap_exec_operation(boot_sql_sub),
                dir=_wrap_exec_operation(boot_sql_dir),
                now=_wrap_exec_operation(boot_sql_now),
                tmp=_wrap_exec_operation(boot_sql_tmp),
                pre=_wrap_exec_operation(boot_sql_pre),
                cache=_wrap_exec_operation(boot_sql_cache),              
            ),
            close=SimpleNamespace(
                base=_wrap_exec_operation(close_sql_base),
                sub=_wrap_exec_operation(close_sql_sub),
                dir=_wrap_exec_operation(close_sql_dir),
                now=_wrap_exec_operation(close_sql_now),
                tmp=_wrap_exec_operation(close_sql_tmp),
                pre=_wrap_exec_operation(close_sql_pre),
                cache=_wrap_exec_operation(close_sql_cache),                
            ),
        )

# Singleton instance (the actual object to import and use)
SqlEX = SqlEXCore()

__all__ = ["SqlEX", "SqlEXCore"]
