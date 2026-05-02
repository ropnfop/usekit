# Path: usekit.classes.data.base.init.wrap.ddl.dbi_simple_ddl.py
# -----------------------------------------------------------------------------------------------
#  Simple Ddl IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: d : ddl
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.ddl.dbi_wrap_ddl import (
    # READ
    read_ddl_base, read_ddl_sub, read_ddl_dir, read_ddl_now, 
    read_ddl_tmp, read_ddl_pre, read_ddl_cache,
    # WRITE
    write_ddl_base, write_ddl_sub, write_ddl_dir, write_ddl_now,
    write_ddl_tmp, write_ddl_pre, write_ddl_cache,
    # UPDATE
    update_ddl_base, update_ddl_sub, update_ddl_dir, update_ddl_now,
    update_ddl_tmp, update_ddl_pre, update_ddl_cache,
    # DELETE
    delete_ddl_base, delete_ddl_sub, delete_ddl_dir, delete_ddl_now,
    delete_ddl_tmp, delete_ddl_pre, delete_ddl_cache,
    # HAS
    has_ddl_base, has_ddl_sub, has_ddl_dir, has_ddl_now,
    has_ddl_tmp, has_ddl_pre, has_ddl_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.ddl.dbi_wrap_ddl import emit_ddl_mem

# ===============================================================================
# DdlSimple class - Ultra-short interface with alias support
# ===============================================================================

class DdlSimple:
    """
    Ultra-short ddl wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        DdlSP.rdb("config")
        DdlSP.wdb({"x": 1}, "config")
        
        # Original parameters
        DdlSP.rdb(name="config", keydata="user")
        DdlSP.wdb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        DdlSP.rdb(nm="config", kd="user")
        DdlSP.wdb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        DdlSP.rdb("config", kd="user/email")
        DdlSP.wdb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rdb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rdd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rdn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rdt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rdp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rdc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read ddl cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wdb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wds(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wdd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wdn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wdt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wdp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wdc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write ddl cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_ddl_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def udb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uds(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def udd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def udn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def udt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def udp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def udc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update ddl cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_ddl_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def ddb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ddd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ddn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ddt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ddp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ddc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete ddl cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hd*)
    # ─────────────────────────────────────
    @staticmethod
    def hdb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hds(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hdd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hdn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hdt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hdp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hdc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has ddl cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_ddl_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (edm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def edm(data=None, type=None, **kwargs):
        """emit ddl mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_ddl_mem)(data, type, **kwargs)

DdlSP = DdlSimple()

__all__ = [
    "DdlSimple",
    "DdlSP",
]
