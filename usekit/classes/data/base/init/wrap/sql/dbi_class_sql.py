# Path: usekit.classes.data.base.init.wrap.sql.dbi_class_sql.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Sql-specific IO wrapper — bridge between loader_sql_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Sql data IO loader
from usekit.classes.data.base.init.wrap.sql.dbi_wrap_sql import (
    # READ
    read_sql_base, read_sql_sub, read_sql_dir, read_sql_now, read_sql_tmp, read_sql_pre, read_sql_cache,
    # WRITE
    write_sql_base, write_sql_sub, write_sql_dir, write_sql_now, write_sql_tmp, write_sql_pre, write_sql_cache,
    # UPDATE
    update_sql_base, update_sql_sub, update_sql_dir, update_sql_now, update_sql_tmp, update_sql_pre, update_sql_cache,
    # DELETE
    delete_sql_base, delete_sql_sub, delete_sql_dir, delete_sql_now, delete_sql_tmp, delete_sql_pre, delete_sql_cache,
    # EXISTS
    has_sql_base, has_sql_sub, has_sql_dir, has_sql_now, has_sql_tmp, has_sql_pre, has_sql_cache,
    # EMIT
    emit_sql_mem,
)

class SqlIOCore(SimpleNamespace):
    """
    Sql-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.sql.dbi_class_sql import SqlIO

        # Original style
        SqlIO.write.base(data=data, name="config")
        SqlIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        SqlIO.write.base(dt=data, nm="config")
        SqlIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        SqlIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        SqlIO.read.sub(nm="cache", dp="session01")
        SqlIO.write.tmp(dt=data, nm="temp01")
        SqlIO.read.pre(nm="meta", pre="job01")

        # Existence check
        SqlIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_sql_base),
                sub=_wrap_read_format(read_sql_sub),
                dir=_wrap_read_format(read_sql_dir),
                now=_wrap_read_format(read_sql_now),
                tmp=_wrap_read_format(read_sql_tmp),
                pre=_wrap_read_format(read_sql_pre),
                cache=_wrap_read_format(read_sql_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_sql_base),
                sub=_wrap_write_format(write_sql_sub),
                dir=_wrap_write_format(write_sql_dir),
                now=_wrap_write_format(write_sql_now),
                tmp=_wrap_write_format(write_sql_tmp),
                pre=_wrap_write_format(write_sql_pre),
                cache=_wrap_write_format(write_sql_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_sql_base),
                sub=_wrap_write_format(update_sql_sub),
                dir=_wrap_write_format(update_sql_dir),
                now=_wrap_write_format(update_sql_now),
                tmp=_wrap_write_format(update_sql_tmp),
                pre=_wrap_write_format(update_sql_pre),
                cache=_wrap_write_format(update_sql_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_sql_base),
                sub=_wrap_read_format(delete_sql_sub),
                dir=_wrap_read_format(delete_sql_dir),
                now=_wrap_read_format(delete_sql_now),
                tmp=_wrap_read_format(delete_sql_tmp),
                pre=_wrap_read_format(delete_sql_pre),
                cache=_wrap_read_format(delete_sql_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_sql_base),
                sub=_wrap_read_format(has_sql_sub),
                dir=_wrap_read_format(has_sql_dir),
                now=_wrap_read_format(has_sql_now),
                tmp=_wrap_read_format(has_sql_tmp),
                pre=_wrap_read_format(has_sql_pre),
                cache=_wrap_read_format(has_sql_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_sql_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
SqlIO = SqlIOCore()

__all__ = ["SqlIO", "SqlIOCore"]
