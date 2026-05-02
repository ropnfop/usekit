# Path: usekit.classes.exec.base.init.wrap.ddl.ebi_simple_ddl.py
# -----------------------------------------------------------------------------------------------
#  Simple Ddl Exec Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: x / i / b / c : exec / import / boot / close
#    obj: d : ddl
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import (
    _wrap_exec_operation, _wrap_exec_operation
)
from usekit.classes.exec.base.init.wrap.ddl.ebi_wrap_ddl import (
    # EXEC
    exec_ddl_base, exec_ddl_sub, exec_ddl_dir, exec_ddl_now, 
    exec_ddl_tmp, exec_ddl_pre, exec_ddl_cache,
    # IMPORT
    import_ddl_base, import_ddl_sub, import_ddl_dir, import_ddl_now,
    import_ddl_tmp, import_ddl_pre, import_ddl_cache,
    # BOOT
    boot_ddl_base, boot_ddl_sub, boot_ddl_dir, boot_ddl_now,
    boot_ddl_tmp, boot_ddl_pre, boot_ddl_cache,
    # CLOSE
    close_ddl_base, close_ddl_sub, close_ddl_dir, close_ddl_now,
    close_ddl_tmp, close_ddl_pre, close_ddl_cache,
)

# ===============================================================================
# DdlSimple class - Ultra-short interface with alias support
# ===============================================================================

class DdlExecSimple:
    """
    Ultra-short ddl wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (pattern, name, dir_path, keydata)
    - Alias parameters (pt, nm, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        DdlSP.xpb("my_module::main", arg1, arg2)
        DdlSP.ipb("config_module")
        
        # Original parameters
        DdlSP.xpb(pattern="my_module::main", keydata="user")
        DdlSP.ipb(name="config_module")
        
        # Alias parameters (recommended)
        DdlSP.xpb(pt="my_module::main", kd="user")
        DdlSP.ipb(nm="config_module", dp="session")
        
        # Mixed (natural)
        DdlSP.xpb("my_module::main", arg1, kd="user/email")
        DdlSP.ipb("config_module", dp="session")
    """

    # ─────────────────────────────────────
    # EXEC (xd*)
    # ─────────────────────────────────────
    @staticmethod
    def xdb(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl base : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_base)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xds(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl sub : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_sub)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xdd(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl dir : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_dir)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xdn(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl now : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_now)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xdt(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl tmp : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_tmp)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xdp(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl pre : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_pre)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xdc(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec ddl cache : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_ddl_cache)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    # ─────────────────────────────────────
    # IMPORT (id*)
    # ─────────────────────────────────────
    @staticmethod
    def idb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ids(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def idd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def idn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def idt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def idp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def idc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import ddl cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # BOOT (bd*)
    # ─────────────────────────────────────
    @staticmethod
    def bdb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bdd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bdn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bdt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bdp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bdc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot ddl cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # CLOSE (cd*)
    # ─────────────────────────────────────
    @staticmethod
    def cdb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl base : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_base)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cds(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl sub : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_sub)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cdd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl dir : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_dir)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cdn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl now : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_now)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cdt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl tmp : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_tmp)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cdp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl pre : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_pre)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cdc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close ddl cache : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_ddl_cache)(name, dir_path, op=op, restore=restore, **kwargs)

# Singleton-style export
DdlEX = DdlExecSimple()

__all__ = [
    "DdlExecSimple",
    "DdlEX",
]
