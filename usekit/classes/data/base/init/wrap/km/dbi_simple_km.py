# Path: usekit.classes.data.base.init.wrap.km.dbi_simple_km.py
# -----------------------------------------------------------------------------------------------
#  Simple Km IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: k : km
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.km.dbi_wrap_km import (
    # READ
    read_km_base, read_km_sub, read_km_dir, read_km_now, 
    read_km_tmp, read_km_pre, read_km_cache,
    # WRITE
    write_km_base, write_km_sub, write_km_dir, write_km_now,
    write_km_tmp, write_km_pre, write_km_cache,
    # UPDATE
    update_km_base, update_km_sub, update_km_dir, update_km_now,
    update_km_tmp, update_km_pre, update_km_cache,
    # DELETE
    delete_km_base, delete_km_sub, delete_km_dir, delete_km_now,
    delete_km_tmp, delete_km_pre, delete_km_cache,
    # HAS
    has_km_base, has_km_sub, has_km_dir, has_km_now,
    has_km_tmp, has_km_pre, has_km_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.km.dbi_wrap_km import emit_km_mem

# ===============================================================================
# KmSimple class - Ultra-short interface with alias support
# ===============================================================================

class KmSimple:
    """
    Ultra-short km wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        KmSP.rkb("config")
        KmSP.wkb({"x": 1}, "config")
        
        # Original parameters
        KmSP.rkb(name="config", keydata="user")
        KmSP.wkb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        KmSP.rkb(nm="config", kd="user")
        KmSP.wkb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        KmSP.rkb("config", kd="user/email")
        KmSP.wkb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read km cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_km_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wkb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wks(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wkd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wkn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wkt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wkp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wkc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write km cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_km_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def ukb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uks(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ukd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ukn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ukt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ukp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ukc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update km cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_km_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete km cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_km_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hk*)
    # ─────────────────────────────────────
    @staticmethod
    def hkb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hks(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hkd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hkn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hkt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hkp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hkc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has km cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_km_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (ekm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def ekm(data=None, type=None, **kwargs):
        """emit km mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_km_mem)(data, type, **kwargs)

KmSP = KmSimple()

__all__ = [
    "KmSimple",
    "KmSP",
]
