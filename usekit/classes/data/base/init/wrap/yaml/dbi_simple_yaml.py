# Path: usekit.classes.data.base.init.wrap.yaml.dbi_simple_yaml.py
# -----------------------------------------------------------------------------------------------
#  Simple Yaml IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: y : yaml
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.yaml.dbi_wrap_yaml import (
    # READ
    read_yaml_base, read_yaml_sub, read_yaml_dir, read_yaml_now, 
    read_yaml_tmp, read_yaml_pre, read_yaml_cache,
    # WRITE
    write_yaml_base, write_yaml_sub, write_yaml_dir, write_yaml_now,
    write_yaml_tmp, write_yaml_pre, write_yaml_cache,
    # UPDATE
    update_yaml_base, update_yaml_sub, update_yaml_dir, update_yaml_now,
    update_yaml_tmp, update_yaml_pre, update_yaml_cache,
    # DELETE
    delete_yaml_base, delete_yaml_sub, delete_yaml_dir, delete_yaml_now,
    delete_yaml_tmp, delete_yaml_pre, delete_yaml_cache,
    # HAS
    has_yaml_base, has_yaml_sub, has_yaml_dir, has_yaml_now,
    has_yaml_tmp, has_yaml_pre, has_yaml_cache,
)
# EMIT
from usekit.classes.data.base.init.wrap.yaml.dbi_wrap_yaml import emit_yaml_mem

# ===============================================================================
# YamlSimple class - Ultra-short interface with alias support
# ===============================================================================

class YamlSimple:
    """
    Ultra-short yaml wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        YamlSP.ryb("config")
        YamlSP.wyb({"x": 1}, "config")
        
        # Original parameters
        YamlSP.ryb(name="config", keydata="user")
        YamlSP.wyb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        YamlSP.ryb(nm="config", kd="user")
        YamlSP.wyb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        YamlSP.ryb("config", kd="user/email")
        YamlSP.wyb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def ryb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ryd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ryn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ryt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ryp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ryc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read yaml cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wyb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wys(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wyd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wyn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wyt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wyp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wyc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write yaml cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_yaml_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def uyb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uys(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uyd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uyn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uyt(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uyp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uyc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update yaml cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_yaml_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dyb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dyd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dyn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dyt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dyp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dyc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete yaml cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hy*)
    # ─────────────────────────────────────
    @staticmethod
    def hyb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hys(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hyd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hyn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hyt(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hyp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hyc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has yaml cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_yaml_cache)(name, dir_path, keydata, cus, **kwargs)

# Singleton-style export

    # ─────────────────────────────────────
    # EMIT (eym) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def eym(data=None, type=None, **kwargs):
        """emit yaml mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_yaml_mem)(data, type, **kwargs)

YamlSP = YamlSimple()

__all__ = [
    "YamlSimple",
    "YamlSP",
]
