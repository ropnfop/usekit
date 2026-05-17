# Path: usekit.classes.data.base.init.wrap.ddl.dbi_class_ddl.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Ddl-specific IO wrapper — bridge between loader_ddl_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Ddl data IO loader
from usekit.classes.data.base.init.wrap.ddl.dbi_wrap_ddl import (
    # READ
    read_ddl_base, read_ddl_sub, read_ddl_dir, read_ddl_now, read_ddl_tmp, read_ddl_pre, read_ddl_cache,
    # WRITE
    write_ddl_base, write_ddl_sub, write_ddl_dir, write_ddl_now, write_ddl_tmp, write_ddl_pre, write_ddl_cache,
    # UPDATE
    update_ddl_base, update_ddl_sub, update_ddl_dir, update_ddl_now, update_ddl_tmp, update_ddl_pre, update_ddl_cache,
    # DELETE
    delete_ddl_base, delete_ddl_sub, delete_ddl_dir, delete_ddl_now, delete_ddl_tmp, delete_ddl_pre, delete_ddl_cache,
    # EXISTS
    has_ddl_base, has_ddl_sub, has_ddl_dir, has_ddl_now, has_ddl_tmp, has_ddl_pre, has_ddl_cache,
    # EMIT
    emit_ddl_mem,
)

class DdlIOCore(SimpleNamespace):
    """
    Ddl-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.ddl.dbi_class_ddl import DdlIO

        # Original style
        DdlIO.write.base(data=data, name="config")
        DdlIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        DdlIO.write.base(dt=data, nm="config")
        DdlIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        DdlIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        DdlIO.read.sub(nm="cache", dp="session01")
        DdlIO.write.tmp(dt=data, nm="temp01")
        DdlIO.read.pre(nm="meta", pre="job01")

        # Existence check
        DdlIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_ddl_base),
                sub=_wrap_read_format(read_ddl_sub),
                dir=_wrap_read_format(read_ddl_dir),
                now=_wrap_read_format(read_ddl_now),
                tmp=_wrap_read_format(read_ddl_tmp),
                pre=_wrap_read_format(read_ddl_pre),
                cache=_wrap_read_format(read_ddl_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_ddl_base),
                sub=_wrap_write_format(write_ddl_sub),
                dir=_wrap_write_format(write_ddl_dir),
                now=_wrap_write_format(write_ddl_now),
                tmp=_wrap_write_format(write_ddl_tmp),
                pre=_wrap_write_format(write_ddl_pre),
                cache=_wrap_write_format(write_ddl_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_ddl_base),
                sub=_wrap_write_format(update_ddl_sub),
                dir=_wrap_write_format(update_ddl_dir),
                now=_wrap_write_format(update_ddl_now),
                tmp=_wrap_write_format(update_ddl_tmp),
                pre=_wrap_write_format(update_ddl_pre),
                cache=_wrap_write_format(update_ddl_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_ddl_base),
                sub=_wrap_read_format(delete_ddl_sub),
                dir=_wrap_read_format(delete_ddl_dir),
                now=_wrap_read_format(delete_ddl_now),
                tmp=_wrap_read_format(delete_ddl_tmp),
                pre=_wrap_read_format(delete_ddl_pre),
                cache=_wrap_read_format(delete_ddl_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_ddl_base),
                sub=_wrap_read_format(has_ddl_sub),
                dir=_wrap_read_format(has_ddl_dir),
                now=_wrap_read_format(has_ddl_now),
                tmp=_wrap_read_format(has_ddl_tmp),
                pre=_wrap_read_format(has_ddl_pre),
                cache=_wrap_read_format(has_ddl_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_ddl_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
DdlIO = DdlIOCore()

__all__ = ["DdlIO", "DdlIOCore"]
