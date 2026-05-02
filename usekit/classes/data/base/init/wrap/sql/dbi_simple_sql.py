# Path: usekit.classes.data.base.init.wrap.sql.dbi_simple_sql.py
# -----------------------------------------------------------------------------------------------
#  Simple Sql IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: s : sql
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.sql.dbi_wrap_sql import (
    # READ
    read_sql_base, read_sql_sub, read_sql_dir, read_sql_now, 
    read_sql_tmp, read_sql_pre, read_sql_cache,
    # WRITE
    write_sql_base, write_sql_sub, write_sql_dir, write_sql_now,
    write_sql_tmp, write_sql_pre, write_sql_cache,
    # UPDATE
    update_sql_base, update_sql_sub, update_sql_dir, update_sql_now,
    update_sql_tmp, update_sql_pre, update_sql_cache,
    # DELETE
    delete_sql_base, delete_sql_sub, delete_sql_dir, delete_sql_now,
    delete_sql_tmp, delete_sql_pre, delete_sql_cache,
    # HAS
    has_sql_base, has_sql_sub, has_sql_dir, has_sql_now,
    has_sql_tmp, has_sql_pre, has_sql_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.sql.dbi_wrap_sql import emit_sql_mem

# ===============================================================================
# SqlSimple class - Ultra-short interface with alias support
# ===============================================================================

class SqlSimple:
    """
    Ultra-short sql wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        SqlSP.rsb("config")
        SqlSP.wsb({"x": 1}, "config")
        
        # Original parameters
        SqlSP.rsb(name="config", keydata="user")
        SqlSP.wsb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        SqlSP.rsb(nm="config", kd="user")
        SqlSP.wsb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        SqlSP.rsb("config", kd="user/email")
        SqlSP.wsb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read sql cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wsb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wss(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wsd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wsn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wst(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wsp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wsc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write sql cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_sql_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def usb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uss(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def usd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def usn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ust(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def usp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def usc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update sql cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_sql_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete sql cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_sql_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hs*)
    # ─────────────────────────────────────
    @staticmethod
    def hsb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hss(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hsd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hsn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hst(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hsp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hsc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has sql cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_sql_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (esm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def esm(data=None, type=None, **kwargs):
        """emit sql mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_sql_mem)(data, type, **kwargs)

SqlSP = SqlSimple()

__all__ = [
    "SqlSimple",
    "SqlSP",
]
