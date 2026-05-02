# Path: usekit.classes.data.class_data_io.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is connection —
# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
#  Lazy Parallel Data IO binder with transparent access
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
        mod = __import__(f"usekit.classes.data.base.init.wrap.{fmt}.dbi_class_{fmt}", fromlist=["*"])
        return getattr(mod, f"{fmt.capitalize()}IO")
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

def _import_operation(fmt, operation):
    """특정 operation (read/write/update/delete/exists)만 반환"""
    def factory():
        mod = __import__(f"usekit.classes.data.base.init.wrap.{fmt}.dbi_class_{fmt}", fromlist=["*"])
        io_instance = getattr(mod, f"{fmt.capitalize()}IO")
        return getattr(io_instance, operation)  # operation 속성만 반환
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy 포맷 매핑
# ─────────────────────────────────────────────────────────────────────────────
_json_io = _import("json")
_yaml_io = _import("yaml")
_csv_io = _import("csv")
_txt_io = _import("txt")
_md_io = _import("md")
_sql_io = _import("sql")
_ddl_io = _import("ddl")
_pyp_io = _import("pyp")
_km_io = _import("km")
_any_io = _import("any")

# ─────────────────────────────────────────────────────────────────────────────
# Operation-first structure (read/write/update/delete/exists)
# ─────────────────────────────────────────────────────────────────────────────
DataIO = SimpleNamespace(
    read=SimpleNamespace(
        json=_import_operation("json", "read"),
        yaml=_import_operation("yaml", "read"),
        csv=_import_operation("csv", "read"),
        txt=_import_operation("txt", "read"),
        md=_import_operation("md", "read"),
        sql=_import_operation("sql", "read"),
        ddl=_import_operation("ddl", "read"),
        pyp=_import_operation("pyp", "read"),
        km=_import_operation("km", "read"),
        any=_import_operation("any", "read"),
    ),
    write=SimpleNamespace(
        json=_import_operation("json", "write"),
        yaml=_import_operation("yaml", "write"),
        csv=_import_operation("csv", "write"),
        txt=_import_operation("txt", "write"),
        md=_import_operation("md", "write"),
        sql=_import_operation("sql", "write"),
        ddl=_import_operation("ddl", "write"),
        pyp=_import_operation("pyp", "write"),
        km=_import_operation("km", "write"),
        any=_import_operation("any", "write"),
    ),
    update=SimpleNamespace(
        json=_import_operation("json", "update"),
        yaml=_import_operation("yaml", "update"),
        csv=_import_operation("csv", "update"),
        txt=_import_operation("txt", "update"),
        md=_import_operation("md", "update"),
        sql=_import_operation("sql", "update"),
        ddl=_import_operation("ddl", "update"),
        pyp=_import_operation("pyp", "update"),
        km=_import_operation("km", "update"),
        any=_import_operation("any", "update"),
    ),
    delete=SimpleNamespace(
        json=_import_operation("json", "delete"),
        yaml=_import_operation("yaml", "delete"),
        csv=_import_operation("csv", "delete"),
        txt=_import_operation("txt", "delete"),
        md=_import_operation("md", "delete"),
        sql=_import_operation("sql", "delete"),
        ddl=_import_operation("ddl", "delete"),
        pyp=_import_operation("pyp", "delete"),
        km=_import_operation("km", "delete"),
        any=_import_operation("any", "delete"),
    ),
    has=SimpleNamespace(
        json=_import_operation("json", "has"),
        yaml=_import_operation("yaml", "has"),
        csv=_import_operation("csv", "has"),
        txt=_import_operation("txt", "has"),
        md=_import_operation("md", "has"),
        sql=_import_operation("sql", "has"),
        ddl=_import_operation("ddl", "has"),
        pyp=_import_operation("pyp", "has"),
        km=_import_operation("km", "has"),
        any=_import_operation("any", "has"),
    ),
    emit=SimpleNamespace(
        json=_import_operation("json", "emit"),
        yaml=_import_operation("yaml", "emit"),
        csv=_import_operation("csv", "emit"),
        txt=_import_operation("txt", "emit"),
        md=_import_operation("md", "emit"),
        sql=_import_operation("sql", "emit"),
        ddl=_import_operation("ddl", "emit"),
        pyp=_import_operation("pyp", "emit"),
        km=_import_operation("km", "emit"),
        any=_import_operation("any", "emit"),
    ),
)

# 기존 format-first structure도 유지
DataUse = SimpleNamespace(
    json=_json_io,
    yaml=_yaml_io,
    csv=_csv_io,
    txt=_txt_io,
    md=_md_io,
    sql=_sql_io,
    ddl=_ddl_io,
    pyp=_pyp_io,
    km=_km_io,
    any=_any_io,
)

# ─────────────────────────────────────────────────────────────────────────────
# 병렬 프리로드
# ─────────────────────────────────────────────────────────────────────────────
def preload_io():
    """모든 포맷 모듈을 백그라운드 병렬 로딩."""
    # 모든 operation에서 사용되는 기본 IO 객체들만 preload
    lazy_values = [
        obj._lazy_value for obj in [
            _json_io, _yaml_io, _csv_io,
            _txt_io, _md_io, _sql_io,
            _ddl_io, _pyp_io, _km_io, _any_io
        ]
    ]
    from usekit.classes.common.init.helper_lazy import lazy
    lazy.preload(*lazy_values, max_workers=9)

__all__ = ["DataUse", "DataIO", "preload_io"]