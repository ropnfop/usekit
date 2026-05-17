# Path: usekit.classes.exec.base.init.wrap.sql.ebi_simple_sql.py
# -----------------------------------------------------------------------------------------------
#  Simple Sql Exec Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: x / i / b / c : exec / import / boot / close
#    obj: s : sql
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.exec.base.init.wrap.common.ebi_common_wrap import (
    _wrap_exec_operation, _wrap_exec_operation
)
from usekit.classes.exec.base.init.wrap.sql.ebi_wrap_sql import (
    # EXEC
    exec_sql_base, exec_sql_sub, exec_sql_dir, exec_sql_now, 
    exec_sql_tmp, exec_sql_pre, exec_sql_cache,
    # IMPORT
    import_sql_base, import_sql_sub, import_sql_dir, import_sql_now,
    import_sql_tmp, import_sql_pre, import_sql_cache,
    # BOOT
    boot_sql_base, boot_sql_sub, boot_sql_dir, boot_sql_now,
    boot_sql_tmp, boot_sql_pre, boot_sql_cache,
    # CLOSE
    close_sql_base, close_sql_sub, close_sql_dir, close_sql_now,
    close_sql_tmp, close_sql_pre, close_sql_cache,
)

# ===============================================================================
# SqlSimple class - Ultra-short interface with alias support
# ===============================================================================

class SqlExecSimple:
    """
    Ultra-short sql wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (pattern, name, dir_path, keydata)
    - Alias parameters (pt, nm, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        SqlSP.xpb("my_module::main", arg1, arg2)
        SqlSP.ipb("config_module")
        
        # Original parameters
        SqlSP.xpb(pattern="my_module::main", keydata="user")
        SqlSP.ipb(name="config_module")
        
        # Alias parameters (recommended)
        SqlSP.xpb(pt="my_module::main", kd="user")
        SqlSP.ipb(nm="config_module", dp="session")
        
        # Mixed (natural)
        SqlSP.xpb("my_module::main", arg1, kd="user/email")
        SqlSP.ipb("config_module", dp="session")
    """

    # ─────────────────────────────────────
    # EXEC (xp*)
    # ─────────────────────────────────────
    @staticmethod
    def xsb(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql base : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_base)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xss(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql sub : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_sub)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xsd(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql dir : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_dir)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xsn(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql now : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_now)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xst(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql tmp : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_tmp)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xsp(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql pre : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_pre)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    @staticmethod
    def xsc(pattern=None, *args, dir_path=None, keydata=None, cus=None, **kwargs):
        """exec sql cache : supports positional, keyword, and alias (pt, dp, kd)"""
        return _wrap_exec_operation(exec_sql_cache)(pattern, *args, dir_path=dir_path, keydata=keydata, cus=cus, **kwargs)

    # ─────────────────────────────────────
    # IMPORT (ip*)
    # ─────────────────────────────────────
    @staticmethod
    def isb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def iss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def isd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def isn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ist(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def isp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def isc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """import sql cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(import_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # BOOT (bp*)
    # ─────────────────────────────────────
    @staticmethod
    def bsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def bsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """boot sql cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_exec_operation(boot_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # CLOSE (cp*)
    # ─────────────────────────────────────
    @staticmethod
    def csb(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql base : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_base)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def css(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql sub : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_sub)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def csd(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql dir : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_dir)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def csn(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql now : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_now)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def cst(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql tmp : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_tmp)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def csp(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql pre : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_pre)(name, dir_path, op=op, restore=restore, **kwargs)

    @staticmethod
    def csc(name=None, dir_path=None, op=None, restore=None, **kwargs):
        """close sql cache : supports positional, keyword, and alias (nm, dp)"""
        return _wrap_exec_operation(close_sql_cache)(name, dir_path, op=op, restore=restore, **kwargs)

# Singleton-style export
SqlEX = SqlExecSimple()

__all__ = [
    "SqlExecSimple",
    "SqlEX",
]
