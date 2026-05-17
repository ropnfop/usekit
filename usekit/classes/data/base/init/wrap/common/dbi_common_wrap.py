# Path: usekit.classes.data.base.init.wrap.common.dbi_common_wrap.py
# -----------------------------------------------------------------------------------------------
#  Simple Common IO Aliases (3-letter ultra-short interface)
#  Created by: THE Little Prince × ROP × FOP
#  v2.0: Added parameter alias support (nm, kd, dp, dt)
# -----------------------------------------------------------------------------------------------
#  act: r / w / u / d / e : read / write / update / delete / exists
#  obj: (a)ny / (c)sv / (d)dl / (j)son / (m)d / (p)yp / (s)ql / (t)xt / (y)aml 
#  loc: b / s / d / n / t / p / c : base / sub / dir / now / tmp / pre / cache
# -----------------------------------------------------------------------------------------------

from typing import Any, Optional
from usekit.infra.params_alias import normalize_params

# ===============================================================================
#  Internal wrapper helpers
#  Converts: nm → name, kd → keydata, dp → dir_path, etc.
#  Still matches DataLd core signature:
#  (data, name, mod, dir_path, keydata, pre, **kwargs)
# ===============================================================================

def _wrap_read_format(fn):
    """
    Wrapper for read operations with alias support
    Supports: positional, keyword, and alias parameters
    """
    def _inner(
        name: Optional[str] = None,
        dir_path: Optional[str] = None,
        keydata: Optional[Any] = None,
        cus: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        # Normalize aliases
        params = normalize_params(**kwargs)
        
        # Positional arguments take precedence
        if name is not None:
            params["name"] = name
        if dir_path is not None:
            params["dir_path"] = dir_path
        if keydata is not None:
            params["keydata"] = keydata
        if cus is not None:
            params["cus"] = cus
        
        return fn(
            name=params.get("name"),
            dir_path=params.get("dir_path"),
            keydata=params.get("keydata"),
            cus=params.get("cus"),
            **{k: v for k, v in params.items() 
               if k not in ["name", "dir_path", "keydata", "cus"]},
        )
    return _inner

def _wrap_write_format(fn):
    """
    Wrapper for write/update operations with alias support
    Supports: positional, keyword, and alias parameters
    """
    def _inner(
        data: Any = None,
        name: Optional[str] = None,
        dir_path: Optional[str] = None,
        keydata: Optional[Any] = None,
        cus: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        # Normalize aliases
        params = normalize_params(**kwargs)
        
        # Positional arguments take precedence
        if data is not None:
            params["data"] = data
        if name is not None:
            params["name"] = name
        if dir_path is not None:
            params["dir_path"] = dir_path
        if keydata is not None:
            params["keydata"] = keydata
        if cus is not None:
            params["cus"] = cus
        
        return fn(
            data=params.get("data"),
            name=params.get("name"),
            dir_path=params.get("dir_path"),
            keydata=params.get("keydata"),
            cus=params.get("cus"),
            **{k: v for k, v in params.items() 
               if k not in ["data", "name", "dir_path", "keydata", "cus"]},
        )
    return _inner

def _wrap_emit_format(fn):
    """
    Wrapper for emit operations with alias support.
    Emit is memory-only serialization (no file I/O).
    Signature: (data, type, **kwargs)
    """
    def _inner(
        data: Any = None,
        type: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        # Normalize aliases
        params = normalize_params(**kwargs)

        # Positional arguments take precedence
        if data is not None:
            params["data"] = data
        if type is not None:
            params["type"] = type

        return fn(
            data=params.get("data"),
            type=params.get("type"),
            **{k: v for k, v in params.items()
               if k not in ["data", "type"]},
        )
    return _inner


def _wrap_read_any_fmt(fn):
    """
    Wrapper for read operations with alias support
    
    Supports:
        - Positional: AnyIO.read.base("config", "subdir", "user/email")
        - Original: name="config", mod="all", keydata="user"
        - Alias: nm="config", kd="user"
        - Mixed: AnyIO.read.base("config", kd="user")
    """
    def _inner(
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        keydata: Optional[Any] = None,
        cus: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        # Normalize aliases to full parameter names
        params = normalize_params(**kwargs)
        
        # Positional arguments take precedence
        if name is not None:
            params["name"] = name
        if mod is not None:
            params["mod"] = mod
        if dir_path is not None:
            params["dir_path"] = dir_path
        if keydata is not None:
            params["keydata"] = keydata
        if cus is not None:
            params["cus"] = cus
        
        return fn(
            name=params.get("name"),
            mod=params.get("mod"),
            dir_path=params.get("dir_path"),
            keydata=params.get("keydata"),
            cus=params.get("cus"),
            **{k: v for k, v in params.items() 
               if k not in ["name", "mod", "dir_path", "keydata", "cus"]},
        )
    return _inner
    
def _wrap_write_any_fmt(fn):
    """
    Wrapper for write/update operations with alias support
    
    Supports:
        - Positional: AnyIO.write.base({"x": 1}, "config" ,"json", "subdir")
        - Original: data={"x": 1}, name="config", mod="json"
        - Alias: dt={"x": 1}, nm="config", mod="json"
        - Mixed: AnyIO.write.base({"x": 1}, nm="config", mod="json")
    """
    def _inner(
        data: Any = None,
        name: Optional[str] = None,
        mod: Optional[str] = None,
        dir_path: Optional[str] = None,
        keydata: Optional[Any] = None,
        cus: Optional[str] = None,
        **kwargs: Any,
    ) -> Any:
        # Normalize aliases to full parameter names
        params = normalize_params(**kwargs)
        
        # Positional arguments take precedence
        if data is not None:
            params["data"] = data
        if name is not None:
            params["name"] = name
        if mod is not None:
            params["mod"] = mod
        if dir_path is not None:
            params["dir_path"] = dir_path
        if keydata is not None:
            params["keydata"] = keydata
        if cus is not None:
            params["cus"] = cus
        
        return fn(
            data=params.get("data"),
            name=params.get("name"),
            mod=params.get("mod"),
            dir_path=params.get("dir_path"),
            keydata=params.get("keydata"),
            cus=params.get("cus"),
            **{k: v for k, v in params.items() 
               if k not in ["data", "name", "mod", "dir_path", "keydata", "cus"]},
        )
    return _inner