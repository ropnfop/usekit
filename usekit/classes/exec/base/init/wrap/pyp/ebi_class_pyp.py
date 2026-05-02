# Path: usekit.classes.exec.base.init.wrap.pyp.ebi_class_pyp.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Pyp-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_exec, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import _wrap_exec_operation
# [1] Pyp data IO loader
from usekit.classes.exec.base.init.wrap.pyp.ebi_wrap_pyp import (
    # EXEC
    exec_pyp_base, exec_pyp_sub, exec_pyp_dir, exec_pyp_now, exec_pyp_tmp, exec_pyp_pre, exec_pyp_cache,
    # import
    import_pyp_base, import_pyp_sub, import_pyp_dir, import_pyp_now, import_pyp_tmp, import_pyp_pre, import_pyp_cache,
    # boot
    boot_pyp_base, boot_pyp_sub, boot_pyp_dir, boot_pyp_now, boot_pyp_tmp, boot_pyp_pre, boot_pyp_cache,
    # CLOSE
    close_pyp_base, close_pyp_sub, close_pyp_dir, close_pyp_now, close_pyp_tmp, close_pyp_pre, close_pyp_cache,
)

class PypEXCore(SimpleNamespace):
    """
    Pyp-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.exec.base.wrap.pyp.ebi_class_pyp import PypEX

        # Original style
        PypEX.imp.base(name="config")
        PypEX.exec.base()

        # Alias style (shorter)
        PypEX.imp.base(nm="config", stat=True)
        PypEX.exec.base(wk=True, stat=True)
        PypEX.set.base(dp="myjob", op="exec")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            exec=SimpleNamespace(
                base=_wrap_exec_operation(exec_pyp_base),
                sub=_wrap_exec_operation(exec_pyp_sub),
                dir=_wrap_exec_operation(exec_pyp_dir),
                now=_wrap_exec_operation(exec_pyp_now),
                tmp=_wrap_exec_operation(exec_pyp_tmp),
                pre=_wrap_exec_operation(exec_pyp_pre),
                cache=_wrap_exec_operation(exec_pyp_cache),
            ),
            imp=SimpleNamespace(
                base=_wrap_exec_operation(import_pyp_base),
                sub=_wrap_exec_operation(import_pyp_sub),
                dir=_wrap_exec_operation(import_pyp_dir),
                now=_wrap_exec_operation(import_pyp_now),
                tmp=_wrap_exec_operation(import_pyp_tmp),
                pre=_wrap_exec_operation(import_pyp_pre),
                cache=_wrap_exec_operation(import_pyp_cache),           
            ),
            boot=SimpleNamespace(
                base=_wrap_exec_operation(boot_pyp_base),
                sub=_wrap_exec_operation(boot_pyp_sub),
                dir=_wrap_exec_operation(boot_pyp_dir),
                now=_wrap_exec_operation(boot_pyp_now),
                tmp=_wrap_exec_operation(boot_pyp_tmp),
                pre=_wrap_exec_operation(boot_pyp_pre),
                cache=_wrap_exec_operation(boot_pyp_cache),              
            ),
            close=SimpleNamespace(
                base=_wrap_exec_operation(close_pyp_base),
                sub=_wrap_exec_operation(close_pyp_sub),
                dir=_wrap_exec_operation(close_pyp_dir),
                now=_wrap_exec_operation(close_pyp_now),
                tmp=_wrap_exec_operation(close_pyp_tmp),
                pre=_wrap_exec_operation(close_pyp_pre),
                cache=_wrap_exec_operation(close_pyp_cache),                
            ),
        )

# Singleton instance (the actual object to import and use)
PypEX = PypEXCore()

__all__ = ["PypEX", "PypEXCore"]
