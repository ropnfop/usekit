# Path: usekit.classes.data.base.init.wrap.km.dbi_class_km.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Km-specific IO wrapper — bridge between loader_txt_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, ekc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Km data IO loader
from usekit.classes.data.base.init.wrap.km.dbi_wrap_km import (
    # READ
    read_km_base, read_km_sub, read_km_dir, read_km_now, read_km_tmp, read_km_pre, read_km_cache,
    # WRITE
    write_km_base, write_km_sub, write_km_dir, write_km_now, write_km_tmp, write_km_pre, write_km_cache,
    # UPDATE
    update_km_base, update_km_sub, update_km_dir, update_km_now, update_km_tmp, update_km_pre, update_km_cache,
    # DELETE
    delete_km_base, delete_km_sub, delete_km_dir, delete_km_now, delete_km_tmp, delete_km_pre, delete_km_cache,
    # EXISTS
    has_km_base, has_km_sub, has_km_dir, has_km_now, has_km_tmp, has_km_pre, has_km_cache,
    # EMIT
    emit_km_mem,
)

class KmIOCore(SimpleNamespace):
    """
    Km-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.km.dbi_class_km import KmIO

        # Original style
        KmIO.write.base(data=data, name="config")
        KmIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        KmIO.write.base(dt=data, nm="config")
        KmIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        KmIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        KmIO.read.sub(nm="cache", dp="session01")
        KmIO.write.tmp(dt=data, nm="temp01")
        KmIO.read.pre(nm="meta", pre="job01")

        # Existence check
        KmIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_km_base),
                sub=_wrap_read_format(read_km_sub),
                dir=_wrap_read_format(read_km_dir),
                now=_wrap_read_format(read_km_now),
                tmp=_wrap_read_format(read_km_tmp),
                pre=_wrap_read_format(read_km_pre),
                cache=_wrap_read_format(read_km_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_km_base),
                sub=_wrap_write_format(write_km_sub),
                dir=_wrap_write_format(write_km_dir),
                now=_wrap_write_format(write_km_now),
                tmp=_wrap_write_format(write_km_tmp),
                pre=_wrap_write_format(write_km_pre),
                cache=_wrap_write_format(write_km_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_km_base),
                sub=_wrap_write_format(update_km_sub),
                dir=_wrap_write_format(update_km_dir),
                now=_wrap_write_format(update_km_now),
                tmp=_wrap_write_format(update_km_tmp),
                pre=_wrap_write_format(update_km_pre),
                cache=_wrap_write_format(update_km_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_km_base),
                sub=_wrap_read_format(delete_km_sub),
                dir=_wrap_read_format(delete_km_dir),
                now=_wrap_read_format(delete_km_now),
                tmp=_wrap_read_format(delete_km_tmp),
                pre=_wrap_read_format(delete_km_pre),
                cache=_wrap_read_format(delete_km_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_km_base),
                sub=_wrap_read_format(has_km_sub),
                dir=_wrap_read_format(has_km_dir),
                now=_wrap_read_format(has_km_now),
                tmp=_wrap_read_format(has_km_tmp),
                pre=_wrap_read_format(has_km_pre),
                cache=_wrap_read_format(has_km_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_km_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
KmIO = KmIOCore()

__all__ = ["KmIO", "KmIOCore"]
