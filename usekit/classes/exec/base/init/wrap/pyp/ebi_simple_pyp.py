# Path: usekit.classes.exec.base.init.wrap.pyp.ebi_simple_pyp.py
# -----------------------------------------------------------------------------------------------
#  Simple Pyp Exec Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: x / i / b / c : exec / import / boot / close
#    obj: p : pyp
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import (
    _wrap_exec_operation, _wrap_exec_operation
)
from usekit.classes.exec.base.init.wrap.pyp.ebi_wrap_pyp import (
    # EXEC
    exec_pyp_base, exec_pyp_sub, exec_pyp_dir, exec_pyp_now, 
    exec_pyp_tmp, exec_pyp_pre, exec_pyp_cache,
    # IMPORT
    import_pyp_base, import_pyp_sub, import_pyp_dir, import_pyp_now,
    import_pyp_tmp, import_pyp_pre, import_pyp_cache,
    # BOOT
    boot_pyp_base, boot_pyp_sub, boot_pyp_dir, boot_pyp_now,
    boot_pyp_tmp, boot_pyp_pre, boot_pyp_cache,
    # CLOSE
    close_pyp_base, close_pyp_sub, close_pyp_dir, close_pyp_now,
    close_pyp_tmp, close_pyp_pre, close_pyp_cache,
)

# ===============================================================================
# PypSimple class - Ultra-short interface with alias support
# ===============================================================================

class PypExecSimple:
    """
    Ultra-short pyp wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (pattern, name, dir_path, keydata)
    - Alias parameters (pt, nm, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        PypSP.xpb("my_module::main", arg1, arg2)
        PypSP.ipb("config_module")
        
        # Original parameters
        PypSP.xpb(pattern="my_module::main", keydata="user")
        PypSP.ipb(name="config_module")
        
        # Alias parameters (recommended)
        PypSP.xpb(pt="my_module::main", kd="user")
        PypSP.ipb(nm="config_module", dp="session")
        
        # Mixed (natural)
        PypSP.xpb("my_module::main", arg1, kd="user/email")
        PypSP.ipb("config_module", dp="session")
    """

    # ─────────────────────────────────────
    # EXEC (xp*)
    # ─────────────────────────────────────
    @staticmethod
    def xpb(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp base : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_base)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xps(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp sub : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_sub)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xpd(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp dir : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_dir)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xpn(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp now : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_now)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xpt(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp tmp : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_tmp)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xpp(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp pre : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_pre)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xpc(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec pyp cache : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_pyp_cache)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    # ─────────────────────────────────────
    # IMPORT (ip*)
    # ─────────────────────────────────────
    @staticmethod
    def ipb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ips(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ipd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ipn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ipt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ipp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ipc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import pyp cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # BOOT (bp*)
    # ─────────────────────────────────────
    @staticmethod
    def bpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot pyp cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # CLOSE (cp*)
    # ─────────────────────────────────────
    @staticmethod
    def cpb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp base : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_base)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cps(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp sub : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_sub)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cpd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp dir : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_dir)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cpn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp now : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_now)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cpt(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp tmp : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_tmp)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cpp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp pre : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_pre)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cpc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close pyp cache : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_pyp_cache)(name, dir_path, op=op, restore=restore, **kwargs)

# Singleton-style export
PypEX = PypExecSimple()

__all__ = [
    "PypExecSimple",
    "PypEX",
]
