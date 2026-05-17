# Path: usekit.classes.exec.base.init.wrap.ddl.ebi_class_ddl.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Ddl-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_exec, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import _wrap_exec_operation
# [1] Ddl data IO loader
from usekit.classes.exec.base.init.wrap.ddl.ebi_wrap_ddl import (
    # EXEC
    exec_ddl_base, exec_ddl_sub, exec_ddl_dir, exec_ddl_now, exec_ddl_tmp, exec_ddl_pre, exec_ddl_cache,
    # import
    import_ddl_base, import_ddl_sub, import_ddl_dir, import_ddl_now, import_ddl_tmp, import_ddl_pre, import_ddl_cache,
    # boot
    boot_ddl_base, boot_ddl_sub, boot_ddl_dir, boot_ddl_now, boot_ddl_tmp, boot_ddl_pre, boot_ddl_cache,
    # CLOSE
    close_ddl_base, close_ddl_sub, close_ddl_dir, close_ddl_now, close_ddl_tmp, close_ddl_pre, close_ddl_cache,
)

class DdlEXCore(SimpleNamespace):
    """
    Ddl-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.exec.base.wrap.ddl.ebi_class_ddl import DdlEX

        # Original style
        DdlEX.imp.base(name="config")
        DdlEX.exec.base()

        # Alias style (shorter)
        DdlEX.imp.base(nm="config", stat=True)
        DdlEX.exec.base(wk=True, stat=True)
        DdlEX.set.base(dp="myjob", op="exec")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            exec=SimpleNamespace(
                base=_wrap_exec_operation(exec_ddl_base),
                sub=_wrap_exec_operation(exec_ddl_sub),
                dir=_wrap_exec_operation(exec_ddl_dir),
                now=_wrap_exec_operation(exec_ddl_now),
                tmp=_wrap_exec_operation(exec_ddl_tmp),
                pre=_wrap_exec_operation(exec_ddl_pre),
                cache=_wrap_exec_operation(exec_ddl_cache),
            ),
            imp=SimpleNamespace(
                base=_wrap_exec_operation(import_ddl_base),
                sub=_wrap_exec_operation(import_ddl_sub),
                dir=_wrap_exec_operation(import_ddl_dir),
                now=_wrap_exec_operation(import_ddl_now),
                tmp=_wrap_exec_operation(import_ddl_tmp),
                pre=_wrap_exec_operation(import_ddl_pre),
                cache=_wrap_exec_operation(import_ddl_cache),           
            ),
            boot=SimpleNamespace(
                base=_wrap_exec_operation(boot_ddl_base),
                sub=_wrap_exec_operation(boot_ddl_sub),
                dir=_wrap_exec_operation(boot_ddl_dir),
                now=_wrap_exec_operation(boot_ddl_now),
                tmp=_wrap_exec_operation(boot_ddl_tmp),
                pre=_wrap_exec_operation(boot_ddl_pre),
                cache=_wrap_exec_operation(boot_ddl_cache),              
            ),
            close=SimpleNamespace(
                base=_wrap_exec_operation(close_ddl_base),
                sub=_wrap_exec_operation(close_ddl_sub),
                dir=_wrap_exec_operation(close_ddl_dir),
                now=_wrap_exec_operation(close_ddl_now),
                tmp=_wrap_exec_operation(close_ddl_tmp),
                pre=_wrap_exec_operation(close_ddl_pre),
                cache=_wrap_exec_operation(close_ddl_cache),                
            ),
        )

# Singleton instance (the actual object to import and use)
DdlEX = DdlEXCore()

__all__ = ["DdlEX", "DdlEXCore"]
