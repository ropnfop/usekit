# Path: usekit.classes.data.base.init.wrap.txt.dbi_class_txt.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Txt-specific IO wrapper — bridge between loader_txt_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Txt data IO loader
from usekit.classes.data.base.init.wrap.txt.dbi_wrap_txt import (
    # READ
    read_txt_base, read_txt_sub, read_txt_dir, read_txt_now, read_txt_tmp, read_txt_pre, read_txt_cache,
    # WRITE
    write_txt_base, write_txt_sub, write_txt_dir, write_txt_now, write_txt_tmp, write_txt_pre, write_txt_cache,
    # UPDATE
    update_txt_base, update_txt_sub, update_txt_dir, update_txt_now, update_txt_tmp, update_txt_pre, update_txt_cache,
    # DELETE
    delete_txt_base, delete_txt_sub, delete_txt_dir, delete_txt_now, delete_txt_tmp, delete_txt_pre, delete_txt_cache,
    # EXISTS
    has_txt_base, has_txt_sub, has_txt_dir, has_txt_now, has_txt_tmp, has_txt_pre, has_txt_cache,
    # EMIT
    emit_txt_mem,
)

class TxtIOCore(SimpleNamespace):
    """
    Txt-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.txt.dbi_class_txt import TxtIO

        # Original style
        TxtIO.write.base(data=data, name="config")
        TxtIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        TxtIO.write.base(dt=data, nm="config")
        TxtIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        TxtIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        TxtIO.read.sub(nm="cache", dp="session01")
        TxtIO.write.tmp(dt=data, nm="temp01")
        TxtIO.read.pre(nm="meta", pre="job01")

        # Existence check
        TxtIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_txt_base),
                sub=_wrap_read_format(read_txt_sub),
                dir=_wrap_read_format(read_txt_dir),
                now=_wrap_read_format(read_txt_now),
                tmp=_wrap_read_format(read_txt_tmp),
                pre=_wrap_read_format(read_txt_pre),
                cache=_wrap_read_format(read_txt_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_txt_base),
                sub=_wrap_write_format(write_txt_sub),
                dir=_wrap_write_format(write_txt_dir),
                now=_wrap_write_format(write_txt_now),
                tmp=_wrap_write_format(write_txt_tmp),
                pre=_wrap_write_format(write_txt_pre),
                cache=_wrap_write_format(write_txt_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_txt_base),
                sub=_wrap_write_format(update_txt_sub),
                dir=_wrap_write_format(update_txt_dir),
                now=_wrap_write_format(update_txt_now),
                tmp=_wrap_write_format(update_txt_tmp),
                pre=_wrap_write_format(update_txt_pre),
                cache=_wrap_write_format(update_txt_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_txt_base),
                sub=_wrap_read_format(delete_txt_sub),
                dir=_wrap_read_format(delete_txt_dir),
                now=_wrap_read_format(delete_txt_now),
                tmp=_wrap_read_format(delete_txt_tmp),
                pre=_wrap_read_format(delete_txt_pre),
                cache=_wrap_read_format(delete_txt_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_txt_base),
                sub=_wrap_read_format(has_txt_sub),
                dir=_wrap_read_format(has_txt_dir),
                now=_wrap_read_format(has_txt_now),
                tmp=_wrap_read_format(has_txt_tmp),
                pre=_wrap_read_format(has_txt_pre),
                cache=_wrap_read_format(has_txt_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_txt_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
TxtIO = TxtIOCore()

__all__ = ["TxtIO", "TxtIOCore"]
