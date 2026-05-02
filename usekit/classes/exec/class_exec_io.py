# Path: usekit.classes.exec.class_exec_io.py
# -----------------------------------------------------------------------------------------------
#  Created by: THE Little Prince, in harmony with ROP and FOP
#  — memory is execgation —
# -----------------------------------------------------------------------------------------------
# -----------------------------------------------------------------------------------------------
#  Lazy Parallel Exec IO binder with transparent access
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
        mod = __import__(f"usekit.classes.exec.base.init.wrap.{fmt}.ebi_class_{fmt}", fromlist=["*"])
        return getattr(mod, f"{fmt.capitalize()}EX")
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

def _import_operation(fmt, operation):
    """특정 operation (exec/imp/boot/close)만 반환"""
    def factory():
        mod = __import__(f"usekit.classes.exec.base.init.wrap.{fmt}.ebi_class_{fmt}", fromlist=["*"])
        exec_instance = getattr(mod, f"{fmt.capitalize()}EX")
        return getattr(exec_instance, operation)  # operation 속성만 반환
    
    lazy_value = lazy.value(factory)
    return TransparentLazyIO(lazy_value)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy 포맷 매핑 (Exec)
# ─────────────────────────────────────────────────────────────────────────────
_json_exec = _import("json")
_yaml_exec = _import("yaml")
_csv_exec = _import("csv")
_txt_exec = _import("txt")
_md_exec = _import("md")
_sql_exec = _import("sql")
_ddl_exec = _import("ddl")
_pyp_exec = _import("pyp")
_km_exec = _import("km")
_any_exec = _import("any")

# ─────────────────────────────────────────────────────────────────────────────
# Operation-first structure (consistent across all formats)
# DATA/NAVI: path/find/list/get/set (all formats)
# EXEC: exec/imp/boot/close (all formats - use as needed)
# ─────────────────────────────────────────────────────────────────────────────
ExecIO = SimpleNamespace(
    # ─────────────────────────────────────────────────────────────────────────
    # EXEC Operations (all formats - structure maintained)
    # Primary use: pyp/sql/ddl (executable code)
    # Secondary use: other formats as needed (e.g., km query execution)
    # ─────────────────────────────────────────────────────────────────────────
    exec=SimpleNamespace(
        json=_import_operation("json", "exec"),
        yaml=_import_operation("yaml", "exec"),
        csv=_import_operation("csv", "exec"),
        txt=_import_operation("txt", "exec"),
        md=_import_operation("md", "exec"),
        sql=_import_operation("sql", "exec"),
        ddl=_import_operation("ddl", "exec"),
        pyp=_import_operation("pyp", "exec"),
        km=_import_operation("km", "exec"),
        any=_import_operation("any", "exec"),
    ),
    imp=SimpleNamespace(
        json=_import_operation("json", "imp"),
        yaml=_import_operation("yaml", "imp"),
        csv=_import_operation("csv", "imp"),
        txt=_import_operation("txt", "imp"),
        md=_import_operation("md", "imp"),
        sql=_import_operation("sql", "imp"),
        ddl=_import_operation("ddl", "imp"),
        pyp=_import_operation("pyp", "imp"),
        km=_import_operation("km", "imp"),
        any=_import_operation("any", "imp"),
    ),
    boot=SimpleNamespace(
        json=_import_operation("json", "boot"),
        yaml=_import_operation("yaml", "boot"),
        csv=_import_operation("csv", "boot"),
        txt=_import_operation("txt", "boot"),
        md=_import_operation("md", "boot"),
        sql=_import_operation("sql", "boot"),
        ddl=_import_operation("ddl", "boot"),
        pyp=_import_operation("pyp", "boot"),
        km=_import_operation("km", "boot"),
        any=_import_operation("any", "boot"),
    ),
    close=SimpleNamespace(
        json=_import_operation("json", "close"),
        yaml=_import_operation("yaml", "close"),
        csv=_import_operation("csv", "close"),
        txt=_import_operation("txt", "close"),
        md=_import_operation("md", "close"),
        sql=_import_operation("sql", "close"),
        ddl=_import_operation("ddl", "close"),
        pyp=_import_operation("pyp", "close"),
        km=_import_operation("km", "close"),
        any=_import_operation("any", "close"),
    ),
)

# 기존 format-first structure도 유지
ExecUse = SimpleNamespace(
    json=_json_exec,
    yaml=_yaml_exec,
    csv=_csv_exec,
    txt=_txt_exec,
    md=_md_exec,
    sql=_sql_exec,
    ddl=_ddl_exec,
    pyp=_pyp_exec,
    km=_km_exec,
    any=_any_exec,
)

# ─────────────────────────────────────────────────────────────────────────────
# 병렬 프리로드
# ─────────────────────────────────────────────────────────────────────────────
def preload_exec_io():
    """모든 포맷 Exec 모듈을 백그라운드 병렬 로딩."""
    # 모든 operation에서 사용되는 기본 Exec 객체들만 preload
    lazy_values = [
        obj._lazy_value for obj in [
            _json_exec, _yaml_exec, _csv_exec,
            _txt_exec, _md_exec, _sql_exec,
            _ddl_exec, _pyp_exec, _km_exec, _any_exec
        ]
    ]
    from usekit.classes.common.init.helper_lazy import lazy
    lazy.preload(*lazy_values, max_workers=10)

__all__ = ["ExecUse", "ExecIO", "preload_exec_io"]