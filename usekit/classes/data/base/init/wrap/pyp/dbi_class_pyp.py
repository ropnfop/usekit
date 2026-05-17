# Path: usekit.classes.data.base.init.wrap.pyp.dbi_class_pyp.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Pyp-specific IO wrapper — bridge between loader_pyp_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Pyp data IO loader
from usekit.classes.data.base.init.wrap.pyp.dbi_wrap_pyp import (
    # READ
    read_pyp_base, read_pyp_sub, read_pyp_dir, read_pyp_now, read_pyp_tmp, read_pyp_pre, read_pyp_cache,
    # WRITE
    write_pyp_base, write_pyp_sub, write_pyp_dir, write_pyp_now, write_pyp_tmp, write_pyp_pre, write_pyp_cache,
    # UPDATE
    update_pyp_base, update_pyp_sub, update_pyp_dir, update_pyp_now, update_pyp_tmp, update_pyp_pre, update_pyp_cache,
    # DELETE
    delete_pyp_base, delete_pyp_sub, delete_pyp_dir, delete_pyp_now, delete_pyp_tmp, delete_pyp_pre, delete_pyp_cache,
    # EXISTS
    has_pyp_base, has_pyp_sub, has_pyp_dir, has_pyp_now, has_pyp_tmp, has_pyp_pre, has_pyp_cache,
    # EMIT
    emit_pyp_mem,
)

class PypIOCore(SimpleNamespace):
    """
    Pyp-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.pyp.dbi_class_pyp import PypIO

        # Original style
        PypIO.write.base(data=data, name="config")
        PypIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        PypIO.write.base(dt=data, nm="config")
        PypIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        PypIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        PypIO.read.sub(nm="cache", dp="session01")
        PypIO.write.tmp(dt=data, nm="temp01")
        PypIO.read.pre(nm="meta", pre="job01")

        # Existence check
        PypIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_pyp_base),
                sub=_wrap_read_format(read_pyp_sub),
                dir=_wrap_read_format(read_pyp_dir),
                now=_wrap_read_format(read_pyp_now),
                tmp=_wrap_read_format(read_pyp_tmp),
                pre=_wrap_read_format(read_pyp_pre),
                cache=_wrap_read_format(read_pyp_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_pyp_base),
                sub=_wrap_write_format(write_pyp_sub),
                dir=_wrap_write_format(write_pyp_dir),
                now=_wrap_write_format(write_pyp_now),
                tmp=_wrap_write_format(write_pyp_tmp),
                pre=_wrap_write_format(write_pyp_pre),
                cache=_wrap_write_format(write_pyp_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_pyp_base),
                sub=_wrap_write_format(update_pyp_sub),
                dir=_wrap_write_format(update_pyp_dir),
                now=_wrap_write_format(update_pyp_now),
                tmp=_wrap_write_format(update_pyp_tmp),
                pre=_wrap_write_format(update_pyp_pre),
                cache=_wrap_write_format(update_pyp_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_pyp_base),
                sub=_wrap_read_format(delete_pyp_sub),
                dir=_wrap_read_format(delete_pyp_dir),
                now=_wrap_read_format(delete_pyp_now),
                tmp=_wrap_read_format(delete_pyp_tmp),
                pre=_wrap_read_format(delete_pyp_pre),
                cache=_wrap_read_format(delete_pyp_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_pyp_base),
                sub=_wrap_read_format(has_pyp_sub),
                dir=_wrap_read_format(has_pyp_dir),
                now=_wrap_read_format(has_pyp_now),
                tmp=_wrap_read_format(has_pyp_tmp),
                pre=_wrap_read_format(has_pyp_pre),
                cache=_wrap_read_format(has_pyp_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_pyp_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
PypIO = PypIOCore()

__all__ = ["PypIO", "PypIOCore"]
