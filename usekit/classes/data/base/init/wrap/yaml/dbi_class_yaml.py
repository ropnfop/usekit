# Path: usekit.classes.data.base.init.wrap.yaml.dbi_class_yaml.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Yaml-specific IO wrapper — bridge between loader_yaml_data
#  NOTE   : Fully aligned with DataLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.data.base.init.wrap.common.dbi_common_wrap import (
    _wrap_read_format,  _wrap_write_format, _wrap_emit_format
)
# [1] Yaml data IO loader
from usekit.classes.data.base.init.wrap.yaml.dbi_wrap_yaml import (
    # READ
    read_yaml_base, read_yaml_sub, read_yaml_dir, read_yaml_now, read_yaml_tmp, read_yaml_pre, read_yaml_cache,
    # WRITE
    write_yaml_base, write_yaml_sub, write_yaml_dir, write_yaml_now, write_yaml_tmp, write_yaml_pre, write_yaml_cache,
    # UPDATE
    update_yaml_base, update_yaml_sub, update_yaml_dir, update_yaml_now, update_yaml_tmp, update_yaml_pre, update_yaml_cache,
    # DELETE
    delete_yaml_base, delete_yaml_sub, delete_yaml_dir, delete_yaml_now, delete_yaml_tmp, delete_yaml_pre, delete_yaml_cache,
    # EXISTS
    has_yaml_base, has_yaml_sub, has_yaml_dir, has_yaml_now, has_yaml_tmp, has_yaml_pre, has_yaml_cache,
    # EMIT
    emit_yaml_mem,
)

class YamlIOCore(SimpleNamespace):
    """
    Yaml-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.data.base.wrap.yaml.dbi_class_yaml import YamlIO

        # Original style
        YamlIO.write.base(data=data, name="config")
        YamlIO.read.base(name="config", keydata="user/email")

        # Alias style (shorter)
        YamlIO.write.base(dt=data, nm="config")
        YamlIO.read.base(nm="config", kd="user/email")

        # Mixed style (recommended)
        YamlIO.read.base(nm="config", keydata="user/email", dp="session01")

        # All location types
        YamlIO.read.sub(nm="cache", dp="session01")
        YamlIO.write.tmp(dt=data, nm="temp01")
        YamlIO.read.pre(nm="meta", pre="job01")

        # Existence check
        YamlIO.has.base(nm="config")
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # DATA IO
            # ───────────────────────────────────
            read=SimpleNamespace(
                base=_wrap_read_format(read_yaml_base),
                sub=_wrap_read_format(read_yaml_sub),
                dir=_wrap_read_format(read_yaml_dir),
                now=_wrap_read_format(read_yaml_now),
                tmp=_wrap_read_format(read_yaml_tmp),
                pre=_wrap_read_format(read_yaml_pre),
                cache=_wrap_read_format(read_yaml_cache),
            ),
            write=SimpleNamespace(
                base=_wrap_write_format(write_yaml_base),
                sub=_wrap_write_format(write_yaml_sub),
                dir=_wrap_write_format(write_yaml_dir),
                now=_wrap_write_format(write_yaml_now),
                tmp=_wrap_write_format(write_yaml_tmp),
                pre=_wrap_write_format(write_yaml_pre),
                cache=_wrap_write_format(write_yaml_cache),           
            ),
            update=SimpleNamespace(
                base=_wrap_write_format(update_yaml_base),
                sub=_wrap_write_format(update_yaml_sub),
                dir=_wrap_write_format(update_yaml_dir),
                now=_wrap_write_format(update_yaml_now),
                tmp=_wrap_write_format(update_yaml_tmp),
                pre=_wrap_write_format(update_yaml_pre),
                cache=_wrap_write_format(update_yaml_cache),              
            ),
            delete=SimpleNamespace(
                base=_wrap_read_format(delete_yaml_base),
                sub=_wrap_read_format(delete_yaml_sub),
                dir=_wrap_read_format(delete_yaml_dir),
                now=_wrap_read_format(delete_yaml_now),
                tmp=_wrap_read_format(delete_yaml_tmp),
                pre=_wrap_read_format(delete_yaml_pre),
                cache=_wrap_read_format(delete_yaml_cache),                
            ),
            has=SimpleNamespace(
                base=_wrap_read_format(has_yaml_base),
                sub=_wrap_read_format(has_yaml_sub),
                dir=_wrap_read_format(has_yaml_dir),
                now=_wrap_read_format(has_yaml_now),
                tmp=_wrap_read_format(has_yaml_tmp),
                pre=_wrap_read_format(has_yaml_pre),
                cache=_wrap_read_format(has_yaml_cache),              
            ),
            emit=SimpleNamespace(
                mem=_wrap_emit_format(emit_yaml_mem),
            ),
        )

# Singleton instance (the actual object to import and use)
YamlIO = YamlIOCore()

__all__ = ["YamlIO", "YamlIOCore"]
