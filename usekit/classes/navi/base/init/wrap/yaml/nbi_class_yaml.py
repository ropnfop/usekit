# Path: usekit.classes.navi.base.init.wrap.yaml.nbi_class_yaml.py
# -----------------------------------------------------------------------------------------------
#  Created by: The Little Prince × ROP × FOP
#  Purpose: Yaml-specific IO wrapper
#  NOTE   : Fully aligned with NaviLd signature:
#           (data, name, dir_path, keydata, pre, **kwargs)
#  v2.0   : Added alias support (nm, kd, dp, etc.)
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.navi.base.init.wrap.common.nbi_common_wrap import _wrap_simple_format
# [1] Yaml data IO loader
from usekit.classes.navi.base.init.wrap.yaml.nbi_wrap_yaml import (
    # PATH
    path_yaml_base, path_yaml_sub, path_yaml_dir, path_yaml_now, path_yaml_tmp, path_yaml_pre, path_yaml_cache,
    # FIND
    find_yaml_base, find_yaml_sub, find_yaml_dir, find_yaml_now, find_yaml_tmp, find_yaml_pre, find_yaml_cache,
    # LIST
    list_yaml_base, list_yaml_sub, list_yaml_dir, list_yaml_now, list_yaml_tmp, list_yaml_pre, list_yaml_cache,
    # GET
    get_yaml_base, get_yaml_sub, get_yaml_dir, get_yaml_now, get_yaml_tmp, get_yaml_pre, get_yaml_cache,
    # SET
    set_yaml_base, set_yaml_sub, set_yaml_dir, set_yaml_now, set_yaml_tmp, set_yaml_pre, set_yaml_cache,
)

class YamlNVCore(SimpleNamespace):
    """
    Yaml-only IO wrapper with alias support.

    Usage example:
        from usekit.classes.navi.base.wrap.yaml.nbi_class_yaml import YamlNV

        # Original style
        YamlNV.find.base(name="config")
        YamlNV.path.base()

        # Alias style (shorter)
        YamlNV.find.base(nm="config", stat=True)
        YamlNV.path.base(wk=True, stat=True)
        YamlNV.set.base(dp="myjob", op="path")
        
    """
    
    def __init__(self):
        super().__init__(
            # ───────────────────────────────────
            # NAVI IO
            # ───────────────────────────────────
            path=SimpleNamespace(
                base=_wrap_simple_format(path_yaml_base),
                sub=_wrap_simple_format(path_yaml_sub),
                dir=_wrap_simple_format(path_yaml_dir),
                now=_wrap_simple_format(path_yaml_now),
                tmp=_wrap_simple_format(path_yaml_tmp),
                pre=_wrap_simple_format(path_yaml_pre),
                cache=_wrap_simple_format(path_yaml_cache),
            ),
            find=SimpleNamespace(
                base=_wrap_simple_format(find_yaml_base),
                sub=_wrap_simple_format(find_yaml_sub),
                dir=_wrap_simple_format(find_yaml_dir),
                now=_wrap_simple_format(find_yaml_now),
                tmp=_wrap_simple_format(find_yaml_tmp),
                pre=_wrap_simple_format(find_yaml_pre),
                cache=_wrap_simple_format(find_yaml_cache),           
            ),
            list=SimpleNamespace(
                base=_wrap_simple_format(list_yaml_base),
                sub=_wrap_simple_format(list_yaml_sub),
                dir=_wrap_simple_format(list_yaml_dir),
                now=_wrap_simple_format(list_yaml_now),
                tmp=_wrap_simple_format(list_yaml_tmp),
                pre=_wrap_simple_format(list_yaml_pre),
                cache=_wrap_simple_format(list_yaml_cache),              
            ),
            get=SimpleNamespace(
                base=_wrap_simple_format(get_yaml_base),
                sub=_wrap_simple_format(get_yaml_sub),
                dir=_wrap_simple_format(get_yaml_dir),
                now=_wrap_simple_format(get_yaml_now),
                tmp=_wrap_simple_format(get_yaml_tmp),
                pre=_wrap_simple_format(get_yaml_pre),
                cache=_wrap_simple_format(get_yaml_cache),                
            ),
            set=SimpleNamespace(
                base=_wrap_simple_format(set_yaml_base),
                sub=_wrap_simple_format(set_yaml_sub),
                dir=_wrap_simple_format(set_yaml_dir),
                now=_wrap_simple_format(set_yaml_now),
                tmp=_wrap_simple_format(set_yaml_tmp),
                pre=_wrap_simple_format(set_yaml_pre),
                cache=_wrap_simple_format(set_yaml_cache),              
            ),
        )

# Singleton instance (the actual object to import and use)
YamlNV = YamlNVCore()

__all__ = ["YamlNV", "YamlNVCore"]
