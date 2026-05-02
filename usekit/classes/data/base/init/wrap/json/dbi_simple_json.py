# Path: usekit.classes.data.base.init.wrap.json.dbi_simple_json.py
# -----------------------------------------------------------------------------------------------
#  Simple Json IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / has
#    obj: j : json
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.json.dbi_wrap_json import (
    # READ
    read_json_base, read_json_sub, read_json_dir, read_json_now, 
    read_json_tmp, read_json_pre, read_json_cache,
    # WRITE
    write_json_base, write_json_sub, write_json_dir, write_json_now,
    write_json_tmp, write_json_pre, write_json_cache,
    # UPDATE
    update_json_base, update_json_sub, update_json_dir, update_json_now,
    update_json_tmp, update_json_pre, update_json_cache,
    # DELETE
    delete_json_base, delete_json_sub, delete_json_dir, delete_json_now,
    delete_json_tmp, delete_json_pre, delete_json_cache,
    # HAS
    has_json_base, has_json_sub, has_json_dir, has_json_now,
    has_json_tmp, has_json_pre, has_json_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.json.dbi_wrap_json import emit_json_mem

# ===============================================================================
# JsonSimple class - Ultra-short interface with alias support
# ===============================================================================

class JsonSimple:
    """
    Ultra-short json wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        JsonSP.rjb("config")
        JsonSP.wjb({"x": 1}, "config")
        
        # Original parameters
        JsonSP.rjb(name="config", keydata="user")
        JsonSP.wjb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        JsonSP.rjb(nm="config", kd="user")
        JsonSP.wjb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        JsonSP.rjb("config", kd="user/email")
        JsonSP.wjb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rjb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rjc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read json cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_json_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wjb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjs(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wjc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write json cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_json_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def ujb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujs(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ujc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update json cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_json_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def djb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def djc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete json cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_json_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hc*)
    # ─────────────────────────────────────
    @staticmethod
    def hjb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hjc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has json cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_json_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (ejm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def ejm(data=None, type=None, **kwargs):
        """emit json mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_json_mem)(data, type, **kwargs)

JsonSP = JsonSimple()

__all__ = [
    "JsonSimple",
    "JsonSP",
]
