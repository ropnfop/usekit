# Path: usekit.classes.navi.class_navi_io.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is navigation —
# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
#  Lazy Parallel Navi IO binder with transparent access
# -----------------------------------------------------------------------------------------------

from types import SimpleNamespace
from usekit.classes.common.init.helper_lazy import lazy

class TransparentLazyIO:
    """LazyValue wrapper that provides transparent attribute access."""
    
    def __init__(self, lazy_value):
        object.__setattr__(self, '_lazy_value', lazy_value)
        object.__setattr__(self, '_instance', None)
    
    def _get_instance(self):
        instance = object.__getattribute__(self, '_instance')
        if instance is None:
            lazy_value = object.__getattribute__(self, '_lazy_value')
            instance = lazy_value()
            object.__setattr__(self, '_instance', instance)
        return instance
    
    def __getattr__(self, name):
        return getattr(self._get_instance(), name)
    
    def __setattr__(self, name, value):
        setattr(self._get_instance(), name, value)
    
    def __dir__(self):
        return dir(self._get_instance())

def _import(fmt):
    def factory():                                           
        mod = __import__(f"usekit.classes.navi.base.init.wrap.{fmt}.nbi_class_{fmt}", fromlist=["*"])
        return getattr(mod, f"{fmt.capitalize()}NV")
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

def _import_operation(fmt, operation):
    """특정 operation (path/find/list/get/set)만 반환"""
    def factory():
        mod = __import__(f"usekit.classes.navi.base.init.wrap.{fmt}.nbi_class_{fmt}", fromlist=["*"])
        navi_instance = getattr(mod, f"{fmt.capitalize()}NV")
        return getattr(navi_instance, operation)  # operation 속성만 반환
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy 포맷 매핑 (Navi)
# ─────────────────────────────────────────────────────────────────────────────
_json_navi = _import("json")
_yaml_navi = _import("yaml")
_csv_navi = _import("csv")
_txt_navi = _import("txt")
_md_navi = _import("md")
_sql_navi = _import("sql")
_ddl_navi = _import("ddl")
_pyp_navi = _import("pyp")
_km_navi = _import("km")
_any_navi = _import("any")

# ─────────────────────────────────────────────────────────────────────────────
# Operation-first structure (path/find/list/get/set)
# ─────────────────────────────────────────────────────────────────────────────
NaviIO = SimpleNamespace(
    path=SimpleNamespace(
        json=_import_operation("json", "path"),
        yaml=_import_operation("yaml", "path"),
        csv=_import_operation("csv", "path"),
        txt=_import_operation("txt", "path"),
        md=_import_operation("md", "path"),
        sql=_import_operation("sql", "path"),
        ddl=_import_operation("ddl", "path"),
        pyp=_import_operation("pyp", "path"),
        km=_import_operation("km", "path"),
        any=_import_operation("any", "path"),
    ),
    find=SimpleNamespace(
        json=_import_operation("json", "find"),
        yaml=_import_operation("yaml", "find"),
        csv=_import_operation("csv", "find"),
        txt=_import_operation("txt", "find"),
        md=_import_operation("md", "find"),
        sql=_import_operation("sql", "find"),
        ddl=_import_operation("ddl", "find"),
        pyp=_import_operation("pyp", "find"),
        km=_import_operation("km", "find"),
        any=_import_operation("any", "find"),
    ),
    list=SimpleNamespace(
        json=_import_operation("json", "list"),
        yaml=_import_operation("yaml", "list"),
        csv=_import_operation("csv", "list"),
        txt=_import_operation("txt", "list"),
        md=_import_operation("md", "list"),
        sql=_import_operation("sql", "list"),
        ddl=_import_operation("ddl", "list"),
        pyp=_import_operation("pyp", "list"),
        km=_import_operation("km", "list"),
        any=_import_operation("any", "list"),
    ),
    get=SimpleNamespace(
        json=_import_operation("json", "get"),
        yaml=_import_operation("yaml", "get"),
        csv=_import_operation("csv", "get"),
        txt=_import_operation("txt", "get"),
        md=_import_operation("md", "get"),
        sql=_import_operation("sql", "get"),
        ddl=_import_operation("ddl", "get"),
        pyp=_import_operation("pyp", "get"),
        km=_import_operation("km", "get"),
        any=_import_operation("any", "get"),
    ),
    set=SimpleNamespace(
        json=_import_operation("json", "set"),
        yaml=_import_operation("yaml", "set"),
        csv=_import_operation("csv", "set"),
        txt=_import_operation("txt", "set"),
        md=_import_operation("md", "set"),
        sql=_import_operation("sql", "set"),
        ddl=_import_operation("ddl", "set"),
        pyp=_import_operation("pyp", "set"),
        km=_import_operation("km", "set"),
        any=_import_operation("any", "set"),
    ),
)

# 기존 format-first structure도 유지
NaviUse = SimpleNamespace(
    json=_json_navi,
    yaml=_yaml_navi,
    csv=_csv_navi,
    txt=_txt_navi,
    md=_md_navi,
    sql=_sql_navi,
    ddl=_ddl_navi,
    pyp=_pyp_navi,
    km=_km_navi,
    any=_any_navi,
)

# ─────────────────────────────────────────────────────────────────────────────
# 병렬 프리로드
# ─────────────────────────────────────────────────────────────────────────────
def preload_navi_io():
    """모든 포맷 Navi 모듈을 백그라운드 병렬 로딩."""
    # 모든 operation에서 사용되는 기본 Navi 객체들만 preload
    lazy_values = [
        obj._lazy_value for obj in [
            _json_navi, _yaml_navi, _csv_navi,
            _txt_navi, _md_navi, _sql_navi,
            _ddl_navi, _pyp_navi, _km_navi, _any_navi
        ]
    ]
    from usekit.classes.common.init.helper_lazy import lazy
    lazy.preload(*lazy_values, max_workers=10)

__all__ = ["NaviUse", "NaviIO", "preload_navi_io"]