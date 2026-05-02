# Path: usekit.classes.data.base.init.wrap.pyp.dbi_simple_pyp.py
# -----------------------------------------------------------------------------------------------
#  Simple Pyp IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: p : pyp
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.pyp.dbi_wrap_pyp import (
    # READ
    read_pyp_base, read_pyp_sub, read_pyp_dir, read_pyp_now, 
    read_pyp_tmp, read_pyp_pre, read_pyp_cache,
    # WRITE
    write_pyp_base, write_pyp_sub, write_pyp_dir, write_pyp_now,
    write_pyp_tmp, write_pyp_pre, write_pyp_cache,
    # UPDATE
    update_pyp_base, update_pyp_sub, update_pyp_dir, update_pyp_now,
    update_pyp_tmp, update_pyp_pre, update_pyp_cache,
    # DELETE
    delete_pyp_base, delete_pyp_sub, delete_pyp_dir, delete_pyp_now,
    delete_pyp_tmp, delete_pyp_pre, delete_pyp_cache,
    # HAS
    has_pyp_base, has_pyp_sub, has_pyp_dir, has_pyp_now,
    has_pyp_tmp, has_pyp_pre, has_pyp_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.pyp.dbi_wrap_pyp import emit_pyp_mem

# ===============================================================================
# PypSimple class - Ultra-short interface with alias support
# ===============================================================================

class PypSimple:
    """
    Ultra-short pyp wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        PypSP.rpb("config")
        PypSP.wpb({"x": 1}, "config")
        
        # Original parameters
        PypSP.rpb(name="config", keydata="user")
        PypSP.wpb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        PypSP.rpb(nm="config", kd="user")
        PypSP.wpb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        PypSP.rpb("config", kd="user/email")
        PypSP.wpb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read pyp cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wpb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wps(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wpd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wpn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wpt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wpp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wpc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write pyp cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_pyp_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def upb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ups(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def upd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def upn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def upt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def upp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def upc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update pyp cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_pyp_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete pyp cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hp*)
    # ─────────────────────────────────────
    @staticmethod
    def hpb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hps(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hpd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hpn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hpt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hpp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hpc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has pyp cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_pyp_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (epm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def epm(data=None, type=None, **kwargs):
        """emit pyp mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_pyp_mem)(data, type, **kwargs)

PypSP = PypSimple()

__all__ = [
    "PypSimple",
    "PypSP",
]
