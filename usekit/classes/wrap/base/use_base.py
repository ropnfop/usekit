# Path: usekit.classes.wrap.base.use_base.py
# -----------------------------------------------------------------------------------------------
# Created by: THE Little Prince × ROP × FOP
# — memory is flow —
# -----------------------------------------------------------------------------------------------

from usekit.classes.common.utils.helper_timer import _tick, _clear
from types import SimpleNamespace
_tick("Use IO start")
from usekit.classes.data.class_data_io import DataUse, DataIO, preload_io
_tick("DataUse DataIO END")
from usekit.classes.navi.class_navi_io import NaviUse, NaviIO, preload_navi_io
_tick("NaviUse NaviIO END")
from usekit.classes.exec.class_exec_io import ExecUse, ExecIO, preload_exec_io
_tick("ExecUse ExecIO END")
from usekit.classes.wrap.simple.use_simple import UseSP, preload_sp
_tick("NaviUse UseSP END")
from concurrent.futures import ThreadPoolExecutor
_tick("I/O config")

from usekit.help.use_help import show_help
from usekit.classes.wrap.base.use_interface import termux, colab, check, editor
from usekit.classes.core.env.loader_env import is_colab as _is_colab

# ───────────────────────────────────────────────────────────────
# 병렬 로딩 최적화 (Colab 제외 — 인터렉티브 환경은 첫 호출 지연 무관)
# ───────────────────────────────────────────────────────────────
_executor = ThreadPoolExecutor(max_workers=20)

if not _is_colab():
    preload_io()
    _tick("DataUse preload_io end")
    preload_navi_io()
    _tick("NaviUse preload_navi_io end")
    preload_exec_io()
    _tick("ExecUse preload_exec_io end")
    preload_sp()
    _tick("Simple preload_sp end")


# ───────────────────────────────────────────────────────────────
# use 네임스페이스: 모르는 속성은 DataSP로 위임
# ───────────────────────────────────────────────────────────────
class _UseNamespace(SimpleNamespace):
    """
    USEKIT Core Interface
    
    Data Operations:
    - 기본 필드: read/write/update/delete/has, json/yaml/...
    
    Navi Operations:
    - 기본 필드: path/find/list/get/set, json/yaml/...
    
    Exec Operations:
    - 기본 필드: exec/imp/boot/close, pyp/sql/ddl/...
    
    모르는 속성 접근 시: DataSP/NaviSP로 위임 (3글자 rjb, pjb 등)
    
    예)
        # Data Operations
        >>> from usekit.classes.class_use import use
        >>> use.read.json.base(name="test")
        >>> use.json.read.base(name="test")
        >>> use.rjb("test")      # → DataSP.rjb("test")
        
        # Navi Operations
        >>> use.path.json.base()
        >>> use.json.path.base()
        >>> use.pjb("test")      # → NaviSP.pjb("test")
        
        # Exec Operations
        >>> use.exec.pyp.base("test:add", 10, 20)
        >>> use.pyp.exec.base("test:add", 10, 20)
        >>> use.xpb("test:add", 10, 20)  # → ExecSP.xpb (if exists)
    """

    def __getattr__(self, name):
        # 1차: 기존 SimpleNamespace 속성 시도
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        # 2차: UseSP로 위임 (3글자 메서드)
        try:
            return getattr(UseSP, name)
        except AttributeError as e:
            # 에러 메시지는 기본 AttributeError 유지
            raise e

# ───────────────────────────────────────────────────────────────
# USEKIT Core Skeleton
# ───────────────────────────────────────────────────────────────
use = _UseNamespace(
    # ========== DATA Operations ==========
    # Operation-first access (use.read.json.base)
    read=DataIO.read,
    write=DataIO.write,
    update=DataIO.update,
    delete=DataIO.delete,
    has=DataIO.has,
    emit=DataIO.emit,

    # ========== NAVI Operations ==========
    # Operation-first access (use.path.json.base)
    path=NaviIO.path,
    find=NaviIO.find,
    list=NaviIO.list,
    get=NaviIO.get,
    set=NaviIO.set,

    # ========== EXEC Operations ==========
    # Operation-first access (use.exec.pyp.base)
    exec=ExecIO.exec,
    imp=ExecIO.imp,
    boot=ExecIO.boot,
    close=ExecIO.close,

    # ========== Format-first access ==========
    # Format-first access (use.json.read.base / use.json.path.base / use.json.exec.base)
    json=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.json).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.json).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.json).items() if not k.startswith('_')}
    ),
    yaml=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.yaml).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.yaml).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.yaml).items() if not k.startswith('_')}
    ),
    csv=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.csv).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.csv).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.csv).items() if not k.startswith('_')}
    ),
    txt=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.txt).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.txt).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.txt).items() if not k.startswith('_')}
    ),
    md=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.md).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.md).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.md).items() if not k.startswith('_')}
    ),
    sql=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.sql).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.sql).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.sql).items() if not k.startswith('_')}
    ),
    ddl=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.ddl).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.ddl).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.ddl).items() if not k.startswith('_')}
    ),
    pyp=SimpleNamespace(
        **{k: v for k, v in vars(DataUse.pyp).items() if not k.startswith('_')},
        **{k: v for k, v in vars(NaviUse.pyp).items() if not k.startswith('_')},
        **{k: v for k, v in vars(ExecUse.pyp).items() if not k.startswith('_')}
    ),

    # Grouped access (use.Data.json / use.Navi.json / use.Exec.json)
    Data=DataUse,
    Navi=NaviUse,
    Exec=ExecUse,
    
    # Help 
    help=show_help,
    
    # Termux utilities
    termux=termux,
    colab=colab,
    check=check,
    editor=editor,
)

# ───────────────────────────────────────────────────────────────
# Ultra-short alias
# ───────────────────────────────────────────────────────────────
# one unified alias
u = UseSP

u.help = show_help
u.termux = termux
u.colab = colab
u.check = check
u.editor = editor

_tick("DATA/NAVI/EXEC I/O 구성 완료")

__all__ = [
    "use",
    "u",
]