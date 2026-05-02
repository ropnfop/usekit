# Path: usekit.classes.data.base.init.wrap.md.dbi_class_md.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Md-specific IO wrapper — bridge between loader_md_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Md data IO loader
from usekit.classes.data.base.init.wrap.md.dbi_wrap_md import (
    # READ
    read_md_base, read_md_sub, read_md_dir, read_md_now, read_md_tmp, read_md_pre, read_md_cache,
    # WRITE
    write_md_base, write_md_sub, write_md_dir, write_md_now, write_md_tmp, write_md_pre, write_md_cache,
    # UPDATE
    update_md_base, update_md_sub, update_md_dir, update_md_now, update_md_tmp, update_md_pre, update_md_cache,
    # DELETE
    delete_md_base, delete_md_sub, delete_md_dir, delete_md_now, delete_md_tmp, delete_md_pre, delete_md_cache,
    # EXISTS
    has_md_base, has_md_sub, has_md_dir, has_md_now, has_md_tmp, has_md_pre, has_md_cache,
    # EMIT
    emit_md_mem,
)

class MdIOCore(SimpleNamespace):
    """
    Md-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.md.dbi_class_md import MdIO

        # Original style
        MdIO.write.base(data=data, name="config")
        MdIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        MdIO.write.base(dt=data, nm="config")
        MdIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        MdIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        MdIO.read.sub(nm="cache", dp="session01")
        MdIO.write.tmp(dt=data, nm="temp01")
        MdIO.read.pre(nm="meta", pre="job01")

        # Existence check
        MdIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_md_base),
                sub=_wrap_read_format(read_md_sub),
                dir=_wrap_read_format(read_md_dir),
                now=_wrap_read_format(read_md_now),
                tmp=_wrap_read_format(read_md_tmp),
                pre=_wrap_read_format(read_md_pre),
                cache=_wrap_read_format(read_md_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_md_base),
                sub=_wrap_write_format(write_md_sub),
                dir=_wrap_write_format(write_md_dir),
                now=_wrap_write_format(write_md_now),
                tmp=_wrap_write_format(write_md_tmp),
                pre=_wrap_write_format(write_md_pre),
                cache=_wrap_write_format(write_md_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_md_base),
                sub=_wrap_write_format(update_md_sub),
                dir=_wrap_write_format(update_md_dir),
                now=_wrap_write_format(update_md_now),
                tmp=_wrap_write_format(update_md_tmp),
                pre=_wrap_write_format(update_md_pre),
                cache=_wrap_write_format(update_md_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_md_base),
                sub=_wrap_read_format(delete_md_sub),
                dir=_wrap_read_format(delete_md_dir),
                now=_wrap_read_format(delete_md_now),
                tmp=_wrap_read_format(delete_md_tmp),
                pre=_wrap_read_format(delete_md_pre),
                cache=_wrap_read_format(delete_md_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_md_base),
                sub=_wrap_read_format(has_md_sub),
                dir=_wrap_read_format(has_md_dir),
                now=_wrap_read_format(has_md_now),
                tmp=_wrap_read_format(has_md_tmp),
                pre=_wrap_read_format(has_md_pre),
                cache=_wrap_read_format(has_md_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_md_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
MdIO = MdIOCore()

__all__ = ["MdIO", "MdIOCore"]
