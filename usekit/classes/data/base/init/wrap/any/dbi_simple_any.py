# Path: usekit.classes.data.base.init.wrap.any.dbi_simple_any.py
# -----------------------------------------------------------------------------------------------
#  Simple Any IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: a : any
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_any_fmt, _wrap_write_any_fmt
)
from usekit.classes.data.base.init.wrap.any.dbi_wrap_any import (
    # READ
    read_any_base, read_any_sub, read_any_dir, read_any_now, 
    read_any_tmp, read_any_pre, read_any_cache,
    # WRITE
    write_any_base, write_any_sub, write_any_dir, write_any_now,
    write_any_tmp, write_any_pre, write_any_cache,
    # UPDATE
    update_any_base, update_any_sub, update_any_dir, update_any_now,
    update_any_tmp, update_any_pre, update_any_cache,
    # DELETE
    delete_any_base, delete_any_sub, delete_any_dir, delete_any_now,
    delete_any_tmp, delete_any_pre, delete_any_cache,
    # HAS
    has_any_base, has_any_sub, has_any_dir, has_any_now,
    has_any_tmp, has_any_pre, has_any_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.any.dbi_wrap_any import emit_any_mem

# ===============================================================================
# AnySimple class - Ultra-short interface with alias support
# ===============================================================================

class AnySimple:
    """
    Ultra-short any wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        AnySP.rab("config")
        AnySP.wab({"x": 1}, "config")
        
        # Original parameters
        AnySP.rab(name="config", keydata="user")
        AnySP.wab(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        AnySP.rab(nm="config", kd="user")
        AnySP.wab(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        AnySP.rab("config", kd="user/email")
        AnySP.wab({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ras(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rad(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ran(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read any cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(read_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wab(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_base)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def was(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_sub)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wad(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_dir)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wan(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_now)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wat(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_tmp)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wap(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_pre)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wac(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write any cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(write_any_cache)(data, name, mod, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def uab(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_base)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uas(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_sub)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uad(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_dir)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uan(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_now)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uat(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_tmp)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uap(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_pre)(data, name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uac(data=None, name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update any cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_any_fmt(update_any_cache)(data, name, mod, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def das(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dad(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dan(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete any cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(delete_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (ha*)
    # ─────────────────────────────────────
    @staticmethod
    def hab(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_base)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def has(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_sub)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def had(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_dir)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def han(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_now)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hat(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_tmp)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hap(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_pre)(name, mod, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hac(name=None, mod=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has any cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_any_fmt(has_any_cache)(name, mod, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (eam) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def eam(data=None, type=None, **kwargs):
        """emit any mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_any_mem)(data, type, **kwargs)

AnySP = AnySimple()

__all__ = [
    "AnySimple",
    "AnySP",
]
