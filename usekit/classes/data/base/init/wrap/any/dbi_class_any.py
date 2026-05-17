# Path: usekit.classes.data.base.init.wrap.any.dbi_class_any.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Any-specific IO wrapper — bridge between loader_any_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_any_fmt,  _wrap_write_any_fmt
)
# [1] Any data IO loader
from usekit.classes.data.base.init.wrap.any.dbi_wrap_any import (
    # READ
    read_any_base, read_any_sub, read_any_dir, read_any_now, read_any_tmp, read_any_pre, read_any_cache,
    # WRITE
    write_any_base, write_any_sub, write_any_dir, write_any_now, write_any_tmp, write_any_pre, write_any_cache,
    # UPDATE
    update_any_base, update_any_sub, update_any_dir, update_any_now, update_any_tmp, update_any_pre, update_any_cache,
    # DELETE
    delete_any_base, delete_any_sub, delete_any_dir, delete_any_now, delete_any_tmp, delete_any_pre, delete_any_cache,
    # EXISTS
    has_any_base, has_any_sub, has_any_dir, has_any_now, has_any_tmp, has_any_pre, has_any_cache,
    # EMIT
    emit_any_mem,
)

class AnyIOCore(SimpleNamespace):
    """
    Any-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.any.dbi_class_any import AnyIO

        # Original style
        AnyIO.write.base(data=data, name="config")
        AnyIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        AnyIO.write.base(dt=data, nm="config")
        AnyIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        AnyIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        AnyIO.read.sub(nm="cache", dp="session01")
        AnyIO.write.tmp(dt=data, nm="temp01")
        AnyIO.read.pre(nm="meta", pre="job01")

        # Existence check
        AnyIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_any_fmt(read_any_base),
                sub=_wrap_read_any_fmt(read_any_sub),
                dir=_wrap_read_any_fmt(read_any_dir),
                now=_wrap_read_any_fmt(read_any_now),
                tmp=_wrap_read_any_fmt(read_any_tmp),
                pre=_wrap_read_any_fmt(read_any_pre),
                cache=_wrap_read_any_fmt(read_any_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_any_fmt(write_any_base),
                sub=_wrap_write_any_fmt(write_any_sub),
                dir=_wrap_write_any_fmt(write_any_dir),
                now=_wrap_write_any_fmt(write_any_now),
                tmp=_wrap_write_any_fmt(write_any_tmp),
                pre=_wrap_write_any_fmt(write_any_pre),
                cache=_wrap_write_any_fmt(write_any_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_any_fmt(update_any_base),
                sub=_wrap_write_any_fmt(update_any_sub),
                dir=_wrap_write_any_fmt(update_any_dir),
                now=_wrap_write_any_fmt(update_any_now),
                tmp=_wrap_write_any_fmt(update_any_tmp),
                pre=_wrap_write_any_fmt(update_any_pre),
                cache=_wrap_write_any_fmt(update_any_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_any_fmt(delete_any_base),
                sub=_wrap_read_any_fmt(delete_any_sub),
                dir=_wrap_read_any_fmt(delete_any_dir),
                now=_wrap_read_any_fmt(delete_any_now),
                tmp=_wrap_read_any_fmt(delete_any_tmp),
                pre=_wrap_read_any_fmt(delete_any_pre),
                cache=_wrap_read_any_fmt(delete_any_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_any_fmt(has_any_base),
                sub=_wrap_read_any_fmt(has_any_sub),
                dir=_wrap_read_any_fmt(has_any_dir),
                now=_wrap_read_any_fmt(has_any_now),
                tmp=_wrap_read_any_fmt(has_any_tmp),
                pre=_wrap_read_any_fmt(has_any_pre),
                cache=_wrap_read_any_fmt(has_any_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_any_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
AnyIO = AnyIOCore()

__all__ = ["AnyIO", "AnyIOCore"]
