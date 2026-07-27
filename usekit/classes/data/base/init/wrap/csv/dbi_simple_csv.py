# Path: usekit.classes.data.base.init.wrap.csv.dbi_simple_csv.py
# -----------------------------------------------------------------------------------------------
#  Simple Csv IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.1: Optimized to call wrap functions directly (removed duplicate wrapper layer)
# -----------------------------------------------------------------------------------------------
#    act: r / w / u / d / e : read / write / update / delete / exists
#    obj: c : csv
#    loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format, _wrap_write_format, _wrap_emit_format
)
from usekit.classes.data.base.init.wrap.csv.dbi_wrap_csv import (
    # READ
    read_csv_base, read_csv_sub, read_csv_dir, read_csv_now, 
    read_csv_tmp, read_csv_pre, read_csv_cache,
    # WRITE
    write_csv_base, write_csv_sub, write_csv_dir, write_csv_now,
    write_csv_tmp, write_csv_pre, write_csv_cache,
    # UPDATE
    update_csv_base, update_csv_sub, update_csv_dir, update_csv_now,
    update_csv_tmp, update_csv_pre, update_csv_cache,
    # DELETE
    delete_csv_base, delete_csv_sub, delete_csv_dir, delete_csv_now,
    delete_csv_tmp, delete_csv_pre, delete_csv_cache,
    # HAS
    has_csv_base, has_csv_sub, has_csv_dir, has_csv_now,
    has_csv_tmp, has_csv_pre, has_csv_cache,
)
# EMIT + MEM
from usekit.classes.data.base.init.wrap.csv.dbi_wrap_csv import (
    emit_csv_mem,
    read_csv_mem, write_csv_mem, update_csv_mem,
    delete_csv_mem, has_csv_mem, list_csv_mem,
)

# ===============================================================================
# CsvSimple class - Ultra-short interface with alias support
# ===============================================================================

class CsvSimple:
    """
    Ultra-short csv wrapper with full alias support
    
    Features:
    - 3-letter function names (act.obj.loc)
    - Positional arguments support
    - Full parameter names (name, data, dir_path, keydata)
    - Alias parameters (nm, dt, dp, kd)
    - Mix and match any style
    
    Examples:
        # Positional (shortest)
        CsvSP.rcb("config")
        CsvSP.wcb({"x": 1}, "config")
        
        # Original parameters
        CsvSP.rcb(name="config", keydata="user")
        CsvSP.wcb(data={"x": 1}, name="config")
        
        # Alias parameters (recommended)
        CsvSP.rcb(nm="config", kd="user")
        CsvSP.wcb(dt={"x": 1}, nm="config")
        
        # Mixed (natural)
        CsvSP.rcb("config", kd="user/email")
        CsvSP.wcb({"x": 1}, nm="config", dp="session")
    """

    # ─────────────────────────────────────
    # READ (rc*)
    # ─────────────────────────────────────
    @staticmethod
    def rcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def rcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """read csv cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(read_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # WRITE (wc*)
    # ─────────────────────────────────────
    @staticmethod
    def wcb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wcs(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wcd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wcn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wct(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wcp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def wcc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """write csv cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(write_csv_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # UPDATE (uc*)
    # ─────────────────────────────────────
    @staticmethod
    def ucb(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv base : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_base)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ucs(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv sub : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_sub)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ucd(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv dir : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_dir)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ucn(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv now : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_now)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def uct(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv tmp : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_tmp)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ucp(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv pre : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_pre)(data, name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def ucc(data=None, name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """update csv cache : supports positional, keyword, and alias (dt, nm, dp, kd)"""
        return _wrap_write_format(update_csv_cache)(data, name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # DELETE (dc*)
    # ─────────────────────────────────────
    @staticmethod
    def dcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def dcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """delete csv cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(delete_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # HAS (hc*)
    # ─────────────────────────────────────
    @staticmethod
    def hcb(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv base : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_base)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hcs(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv sub : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_sub)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hcd(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv dir : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_dir)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hcn(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv now : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_now)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hct(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv tmp : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_tmp)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hcp(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv pre : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_pre)(name, dir_path, keydata, cus, **kwargs)

    @staticmethod
    def hcc(name=None, dir_path=None, keydata=None, cus=None, **kwargs):
        """has csv cache : supports positional, keyword, and alias (nm, dp, kd)"""
        return _wrap_read_format(has_csv_cache)(name, dir_path, keydata, cus, **kwargs)

    # ─────────────────────────────────────
    # MEM (rcm/wcm/ucm/dcm/hcm/lcm) - in-memory store
    # ─────────────────────────────────────
    @staticmethod
    def rcm(name=None, **kwargs):
        """read csv mem : read from in-memory store"""
        return read_csv_mem(name=name, **kwargs)

    @staticmethod
    def wcm(data=None, name=None, **kwargs):
        """write csv mem : write to in-memory store"""
        return write_csv_mem(data=data, name=name, **kwargs)

    @staticmethod
    def ucm(data=None, name=None, **kwargs):
        """update csv mem : merge dict into existing in-memory store entry"""
        return update_csv_mem(data=data, name=name, **kwargs)

    @staticmethod
    def dcm(name=None, **kwargs):
        """delete csv mem : delete from in-memory store"""
        return delete_csv_mem(name=name, **kwargs)

    @staticmethod
    def hcm(name=None, **kwargs):
        """has csv mem : check existence in in-memory store"""
        return has_csv_mem(name=name, **kwargs)

    @staticmethod
    def lcm(**kwargs):
        """list csv mem : list all keys in in-memory store"""
        return list_csv_mem()

    # ─────────────────────────────────────
    # EMIT (ecm) - memory-only serialization
    # ─────────────────────────────────────
    @staticmethod
    def ecm(data=None, type=None, **kwargs):
        """emit csv mem : memory-only serialization (no file I/O)"""
        return _wrap_emit_format(emit_csv_mem)(data, type, **kwargs)

CsvSP = CsvSimple()

__all__ = [
    "CsvSimple",
    "CsvSP",
]
