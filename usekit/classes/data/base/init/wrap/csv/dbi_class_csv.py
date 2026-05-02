# Path: usekit.classes.data.base.init.wrap.csv.dbi_class_csv.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Csv-specific IO wrapper — bridge between loader_csv_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Csv data IO loader
from usekit.classes.data.base.init.wrap.csv.dbi_wrap_csv import (
    # READ
    read_csv_base, read_csv_sub, read_csv_dir, read_csv_now, read_csv_tmp, read_csv_pre, read_csv_cache,
    # WRITE
    write_csv_base, write_csv_sub, write_csv_dir, write_csv_now, write_csv_tmp, write_csv_pre, write_csv_cache,
    # UPDATE
    update_csv_base, update_csv_sub, update_csv_dir, update_csv_now, update_csv_tmp, update_csv_pre, update_csv_cache,
    # DELETE
    delete_csv_base, delete_csv_sub, delete_csv_dir, delete_csv_now, delete_csv_tmp, delete_csv_pre, delete_csv_cache,
    # EXISTS
    has_csv_base, has_csv_sub, has_csv_dir, has_csv_now, has_csv_tmp, has_csv_pre, has_csv_cache,
    # EMIT
    emit_csv_mem,
)

class CsvIOCore(SimpleNamespace):
    """
    Csv-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.csv.dbi_class_csv import CsvIO

        # Original style
        CsvIO.write.base(data=data, name="config")
        CsvIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        CsvIO.write.base(dt=data, nm="config")
        CsvIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        CsvIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        CsvIO.read.sub(nm="cache", dp="session01")
        CsvIO.write.tmp(dt=data, nm="temp01")
        CsvIO.read.pre(nm="meta", pre="job01")

        # Existence check
        CsvIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_csv_base),
                sub=_wrap_read_format(read_csv_sub),
                dir=_wrap_read_format(read_csv_dir),
                now=_wrap_read_format(read_csv_now),
                tmp=_wrap_read_format(read_csv_tmp),
                pre=_wrap_read_format(read_csv_pre),
                cache=_wrap_read_format(read_csv_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_csv_base),
                sub=_wrap_write_format(write_csv_sub),
                dir=_wrap_write_format(write_csv_dir),
                now=_wrap_write_format(write_csv_now),
                tmp=_wrap_write_format(write_csv_tmp),
                pre=_wrap_write_format(write_csv_pre),
                cache=_wrap_write_format(write_csv_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_csv_base),
                sub=_wrap_write_format(update_csv_sub),
                dir=_wrap_write_format(update_csv_dir),
                now=_wrap_write_format(update_csv_now),
                tmp=_wrap_write_format(update_csv_tmp),
                pre=_wrap_write_format(update_csv_pre),
                cache=_wrap_write_format(update_csv_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_csv_base),
                sub=_wrap_read_format(delete_csv_sub),
                dir=_wrap_read_format(delete_csv_dir),
                now=_wrap_read_format(delete_csv_now),
                tmp=_wrap_read_format(delete_csv_tmp),
                pre=_wrap_read_format(delete_csv_pre),
                cache=_wrap_read_format(delete_csv_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_csv_base),
                sub=_wrap_read_format(has_csv_sub),
                dir=_wrap_read_format(has_csv_dir),
                now=_wrap_read_format(has_csv_now),
                tmp=_wrap_read_format(has_csv_tmp),
                pre=_wrap_read_format(has_csv_pre),
                cache=_wrap_read_format(has_csv_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_csv_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
CsvIO = CsvIOCore()

__all__ = ["CsvIO", "CsvIOCore"]
