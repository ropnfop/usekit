# Path: usekit.classes.data.base.init.wrap.md.dbi_simple_md.py
# -----------------------------------------------------------------------------------------------
#  Simple Md IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: m : md
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.md.dbi_wrap_md import (
    # READ
    read_md_base, read_md_sub, read_md_dir, read_md_now, 
    read_md_tmp, read_md_pre, read_md_cache,
    # WRITE
    write_md_base, write_md_sub, write_md_dir, write_md_now,
    write_md_tmp, write_md_pre, write_md_cache,
    # UPDATE
    update_md_base, update_md_sub, update_md_dir, update_md_now,
    update_md_tmp, update_md_pre, update_md_cache,
    # DELETE
    delete_md_base, delete_md_sub, delete_md_dir, delete_md_now,
    delete_md_tmp, delete_md_pre, delete_md_cache,
    # HAS
    has_md_base, has_md_sub, has_md_dir, has_md_now,
    has_md_tmp, has_md_pre, has_md_cache,
)
# EMIT + MEM
from usekit.classes.data.base.init.wrap.md.dbi_wrap_md import (
    emit_md_mem,
    read_md_mem, write_md_mem, update_md_mem,
    delete_md_mem, has_md_mem, list_md_mem,
)

# ===============================================================================
# MdSimple class - Ultra-short interface with alias support
# ===============================================================================

class MdSimple:
    """
    Ultra-short md wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        MdSP.rmb("config")
        MdSP.wmb({"x": 1}, "config")
        
        # Original parameters
        MdSP.rmb(name="config", keydata="user")
        MdSP.wmb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        MdSP.rmb(nm="config", kd="user")
        MdSP.wmb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        MdSP.rmb("config", kd="user/email")
        MdSP.wmb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read md cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wmb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wms(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wmd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wmn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wmt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wmp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wmc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write md cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_md_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def umb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ums(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def umd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def umn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def umt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ump(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def umc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update md cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_md_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete md cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hm*)
    # ─────────────────────────────────────
    @staticmethod
    def hmb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hms(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hmd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hmn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hmt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hmp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hmc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has md cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_md_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # MEM (rmm/wmm/umm/dmm/hmm/lmm) - in-memory store
    # ─────────────────────────────────────
    @staticmethod
    def rmm(name=None, **kwargs):
        """read md mem : read from in-memory store"""
        return read_md_mem(name=name, **kwargs)

    @staticmethod
    def wmm(data=None, name=None, **kwargs):
        """write md mem : write to in-memory store"""
        return write_md_mem(data=data, name=name, **kwargs)

    @staticmethod
    def umm(data=None, name=None, **kwargs):
        """update md mem : merge dict into existing in-memory store entry"""
        return update_md_mem(data=data, name=name, **kwargs)

    @staticmethod
    def dmm(name=None, **kwargs):
        """delete md mem : delete from in-memory store"""
        return delete_md_mem(name=name, **kwargs)

    @staticmethod
    def hmm(name=None, **kwargs):
        """has md mem : check existence in in-memory store"""
        return has_md_mem(name=name, **kwargs)

    @staticmethod
    def lmm(**kwargs):
        """list md mem : list all keys in in-memory store"""
        return list_md_mem()

    # ─────────────────────────────────────
    # EMIT (emm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def emm(data=None, type=None, **kwargs):
        """emit md mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_md_mem)(data, type, **kwargs)

MdSP = MdSimple()

__all__ = [
    "MdSimple",
    "MdSP",
]
