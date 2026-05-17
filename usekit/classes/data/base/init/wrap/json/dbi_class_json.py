# Path: usekit.classes.data.base.init.wrap.json.dbi_class_json.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Json-specific IO wrapper — bridge between loader_json_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Json data IO loader
from usekit.classes.data.base.init.wrap.json.dbi_wrap_json import (
    # READ
    read_json_base, read_json_sub, read_json_dir, read_json_now, read_json_tmp, read_json_pre, read_json_cache,
    # WRITE
    write_json_base, write_json_sub, write_json_dir, write_json_now, write_json_tmp, write_json_pre, write_json_cache,
    # UPDATE
    update_json_base, update_json_sub, update_json_dir, update_json_now, update_json_tmp, update_json_pre, update_json_cache,
    # DELETE
    delete_json_base, delete_json_sub, delete_json_dir, delete_json_now, delete_json_tmp, delete_json_pre, delete_json_cache,
    # EXISTS
    has_json_base, has_json_sub, has_json_dir, has_json_now, has_json_tmp, has_json_pre, has_json_cache,
    # EMIT
    emit_json_mem,
)

class JsonIOCore(SimpleNamespace):
    """
    Json-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.json.dbi_class_json import JsonIO

        # Original style
        JsonIO.write.base(data=data, name="config")
        JsonIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        JsonIO.write.base(dt=data, nm="config")
        JsonIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        JsonIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        JsonIO.read.sub(nm="cache", dp="session01")
        JsonIO.write.tmp(dt=data, nm="temp01")
        JsonIO.read.pre(nm="meta", pre="job01")

        # Existence check
        JsonIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_json_base),
                sub=_wrap_read_format(read_json_sub),
                dir=_wrap_read_format(read_json_dir),
                now=_wrap_read_format(read_json_now),
                tmp=_wrap_read_format(read_json_tmp),
                pre=_wrap_read_format(read_json_pre),
                cache=_wrap_read_format(read_json_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_json_base),
                sub=_wrap_write_format(write_json_sub),
                dir=_wrap_write_format(write_json_dir),
                now=_wrap_write_format(write_json_now),
                tmp=_wrap_write_format(write_json_tmp),
                pre=_wrap_write_format(write_json_pre),
                cache=_wrap_write_format(write_json_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_json_base),
                sub=_wrap_write_format(update_json_sub),
                dir=_wrap_write_format(update_json_dir),
                now=_wrap_write_format(update_json_now),
                tmp=_wrap_write_format(update_json_tmp),
                pre=_wrap_write_format(update_json_pre),
                cache=_wrap_write_format(update_json_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_json_base),
                sub=_wrap_read_format(delete_json_sub),
                dir=_wrap_read_format(delete_json_dir),
                now=_wrap_read_format(delete_json_now),
                tmp=_wrap_read_format(delete_json_tmp),
                pre=_wrap_read_format(delete_json_pre),
                cache=_wrap_read_format(delete_json_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_json_base),
                sub=_wrap_read_format(has_json_sub),
                dir=_wrap_read_format(has_json_dir),
                now=_wrap_read_format(has_json_now),
                tmp=_wrap_read_format(has_json_tmp),
                pre=_wrap_read_format(has_json_pre),
                cache=_wrap_read_format(has_json_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_json_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
JsonIO = JsonIOCore()

__all__ = ["JsonIO", "JsonIOCore"]
