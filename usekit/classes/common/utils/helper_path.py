# Path: usekit.classes.common.utils.helper_path.py
# -----------------------------------------------------------------------------------------------
#  a creation by: THE Little Prince × ROP × FOP
#  Purpose: Path resolver utilities for system/project management.
#  [UPDATED] path_cache 우선순위 추가
# -----------------------------------------------------------------------------------------------

import logging
from pathlib import Path
from typing import Dict
from usekit.classes.common.utils.helper_const import get_const, get_extension, resolve_format_section
from usekit.classes.core.env.loader_base_path import SYS_PATH_NOW, BASE_PATH

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------------------------
# [1] Absolute Path Resolvers (yaml-defined sections, always root+key pattern)
# -----------------------------------------------------------------------------------------------

from usekit.classes.common.utils.helper_const import get_abs_const, get_const

def inner_abs_path_const(key: str = 'SYS_PATH', subkey: str = None) -> Path:
    """
    Get safe absolute path for key/subkey from sys_const.yaml.
    """
    subkey = subkey or 'root'
    const_dict = get_const(key)
    if subkey not in const_dict:
        raise KeyError(f"Subkey '{subkey}' not found in section '{key}'")
    path_key = f"{key}.{subkey}"
    return get_abs_const(path_key).resolve()

def resolve_path(fullkey: str) -> Path:
    """
    Absolute Path from yaml full key (e.g., DATA_PATH.json).
    """
    key, subkey = fullkey.split('.', 1)
    root = get_const(f"{key}.root")
    folder = get_const(f"{key}.{subkey}")
    base = Path(BASE_PATH) / root / folder
    return base.resolve()

def resolve_path_from_fullkey(fullkey: str, name: str = None) -> Path:
    """
    Absolute Path + optional file under directory by yaml key.
    """
    key, subkey = fullkey.split('.', 1) 
    root = get_const(f"{key}.root")
    folder = get_const(f"{key}.{subkey}")
    base = Path(BASE_PATH) / root / folder
    return (base / name).resolve() if name else base.resolve()

def resolve_now_path(name: str = None) -> Path:
    """
    Path relative to SYS_PATH_NOW, fallback BASE_PATH if needed.
    """
    try:
        base = Path(SYS_PATH_NOW).resolve()
        base_path = Path(BASE_PATH).resolve()
        base.relative_to(base_path)
        return (base / name).resolve() if name else base
    except ValueError:
        logger.warning("[WARNING] SYS_PATH_NOW is outside BASE_PATH. Using BASE_PATH.")
        return (base_path / name).resolve() if name else base_path
    except Exception as e:
        logger.error(f"[ERROR] resolve_now_path error: {e}")
        raise

def resolve_user_input_path(user_input: str = "") -> Path:
    base = Path(BASE_PATH).resolve()
  
    if not user_input or str(user_input).strip() == "":
        return Path(SYS_PATH_NOW).resolve()

    user_input = str(user_input).strip()
    
    p = Path(user_input).expanduser()
    # 특정 루트 경로 직접 체크 (예: /content)
    if user_input.startswith("/content"):
        # 입력 경로 그대로 반환 (절대경로로 간주)
        return p.resolve()

    # 절대경로 입력: /aaa/bbb → BASE_PATH/aaa/bbb
    if user_input.startswith("/"):
        clean_path = user_input.lstrip("/")
        return (base / clean_path).resolve()
   
    # 이미 BASE_PATH 밑이면 그대로 반환
    p = Path(user_input).expanduser()
    try:
        p.relative_to(base)
        return p.resolve()
    except ValueError:
        pass

    # Relative path handling → based on SYS_PATH_NOW, remove common prefix
    now_parts = list(Path(SYS_PATH_NOW).resolve().parts)
    user_parts = list(Path(user_input.strip()).parts)
    
    i = 0
    for part in user_parts:
        if i < len(now_parts) and now_parts[i] == part:
            i += 1
        else:
            break

    clean_parts = now_parts + user_parts[i:]
    return Path(*clean_parts).resolve()

# -----------------------------------------------------------------------------------------------
# [2] Section Path Helpers (by yaml key) — all use root+key internally
# -----------------------------------------------------------------------------------------------
def inner_abs_fmt_path(fmt: str) -> Path:
    base_fmt = fmt.split("_")[0]
    section = get_const(f"FORMAT_SECTION_MAP.{base_fmt}")
    return get_abs_const(f"{section}.{fmt}").resolve()

# -----------------------------------------------------------------------------------------------
# [3]  스마트 경로 생성기 (포맷 + 위치 + 사용자 디렉토리) + path_cache 우선순위
# -----------------------------------------------------------------------------------------------

def get_smart_path(
    fmt: str,     
    mod: str = "log",
    filename: str = None,
    loc: str = "base",
    user_dir: str = None,
    cus: str = None,
    ensure_ext: bool = True
) -> Path:
    """
    Automatically assemble path based on format and location options.
    
    Args:
        fmt: File format (json, yaml, txt, csv, md, ddl, dml, mod, any, etc.)
        mod: Modifier for format extension (default: "log")
            - When fmt="any" and mod="json" → uses DATA_PATH.any with .json extension
            - When fmt="any" and mod="all" → uses DATA_PATH.any without specific extension
            - Otherwise, acts as default logging/debugging hint
        filename: Filename (extension optional, auto-added if ensure_ext=True)
        loc: Location specifier
            - "base": Format's default path (e.g., DATA_PATH.json)
            - "sub": Format's sub path (e.g., DATA_PATH.json_sub)
            - "now": Current working path (SYS_PATH_NOW)
            - "dir": Project root + user_dir (supports zero path)
            - "cache": Cache directory (supports zero path)
            - "tmp": Temporary directory (TMP_PATH.{fmt_category})
            - "cus": Custom directory preset (from CUS_PATH in yaml)
        user_dir: User custom directory (used with loc="dir" or "cache")
                  If starts with '/' in dir/cache modes, treated as zero path (external absolute path)
        cus: Custom path preset name (used with loc="cus" or direct specification)
             Presets are defined in CUS_PATH section of sys_const.yaml
        ensure_ext: Auto-append extension if True (.json, .yaml, etc.)
    
    Returns:
        Path: Assembled absolute path
    
    Examples:
        >>> get_smart_path("json", "config", loc="base")
        PosixPath('/content/.../data/json/json_main/config.json')
        
        >>> get_smart_path("json", "temp", loc="sub")
        PosixPath('/content/.../data/json/json_sub/temp.json')
        
        >>> get_smart_path("txt", "note", loc="now")
        PosixPath('/content/.../data/common/note.txt')
        
        >>> get_smart_path("csv", "data", loc="dir", user_dir="custom/folder")
        PosixPath('/content/.../custom/folder/data.csv')
        
        >>> get_smart_path("csv", "backup", loc="dir", user_dir="/external/path")
        PosixPath('/external/path/backup.csv')  # Zero path (external slot)
        
        >>> get_smart_path("json", "temp", loc="cache")
        PosixPath('/content/.../data/.runtime_cache/json/temp.pkl')
        
        >>> get_smart_path("any", "config", mod="json")
        PosixPath('/content/.../data/any/config.json')
        
        >>> get_smart_path("any", "settings", mod="yaml")
        PosixPath('/content/.../data/any/settings.yaml')

        >>> get_smart_path("json", "config", cus="job01")
        PosixPath('/content/.../data/custom/config.json')  # Preset from yaml
    """
    # -----------------------------------------------------------------------------------------------      
    #  오버라이드 fmt : any <- mod : fotmat 지정시 mod를 fmt 으로
    # -----------------------------------------------------------------------------------------------
    from usekit.classes.common.utils.helper_const import resolve_format_section, get_extension
    from usekit.classes.common.utils.helper_format import get_format_set
    
    ext_map: Dict[str, str] = get_const("EXTENSION_MAP")
    
    if fmt == "any":
        if mod in ext_map:
            fmt = mod
        fmt_set = "pkl" if loc== "cache" else mod
        fmt_actual = get_format_set(fmt_set)
    else:
        fmt_set = "pkl" if loc== "cache" else fmt
        fmt_actual = get_extension(fmt_set)
       
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [0] 런타임 캐시 우선 확인!
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        from usekit.classes.common.utils.helper_path_cache import get_path_cache
        
        cached_path = get_path_cache(fmt, loc)
        if cached_path:
            base_path = cached_path
            
            # user_dir 추가 처리
            if user_dir and loc != "dir":
                base_path = base_path / user_dir
            
            # filename 처리
            if not filename:
                return base_path.resolve()
            
            file_path = Path(filename)
            if ensure_ext and not file_path.suffix:
                ext = fmt_actual  # Already computed above with cache/format logic
                file_path = file_path.with_suffix(ext)
            
            final_path = base_path / file_path
            return final_path.resolve()
    except ImportError:
        # path_cache 모듈이 없으면 무시하고 계속
        pass
   
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [1] 기존 로직 (DSL_PATH → DATA_PATH)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    loc = loc.lower().strip()
    
    # [0] cus가 제공되면 loc를 "cus"로 오버라이드
    if cus is not None:
        loc = "cus"
    
    # [1] 위치별 base 디렉토리 결정
    if loc == "base":
        # 포맷의 기본 경로 (예: DATA_PATH.json)
        section = resolve_format_section(fmt)
        base_path = inner_abs_path_const(section, fmt)
        
    elif loc == "sub":
        # 포맷의 서브 경로 (예: DATA_PATH.json_sub)
        section = resolve_format_section(fmt)
        subkey = f"{fmt}_sub"
        try:
            base_path = inner_abs_path_const(section, subkey)
        except KeyError:
            # _sub이 없으면 base로 폴백
            logger.warning(f"[SMART_PATH] {section}.{subkey} not found, using base")
            base_path = inner_abs_path_const(section, fmt)
            
    elif loc == "now":
        # 현재 작업 디렉토리
        base_path = resolve_now_path()
        
    elif loc == "dir":
        # 프로젝트 루트 + 사용자 디렉토리
        # If user_dir starts with '/', treat as zero path (external absolute path)
        if user_dir and str(user_dir).strip().startswith("/"):
            base_path = Path(user_dir).expanduser().resolve()
        else:
            base_path = Path(BASE_PATH).resolve()
            if user_dir:
                base_path = base_path / user_dir
            
    elif loc == "tmp":
        # Temporary directory - uses TMP_PATH.{fmt} pattern like base
        try:
            base_path = inner_abs_path_const("TMP_PATH", fmt)
        except KeyError:
            # Fallback to generic 'any' tmp if format-specific tmp not defined
            logger.warning(f"[SMART_PATH] TMP_PATH.{fmt} not found, using TMP_PATH.any")
            base_path = inner_abs_path_const("TMP_PATH", "any")
     
    elif loc == "cus":
        # 커스텀 경로 프리셋 (CUS_PATH에서 로드)
        if cus is None:
            cus = "root"
                    
        # CUS_PATH.{cus} 에서 경로 가져오기
        try:
            custom_path = get_const(f"CUS_PATH.{cus}")
            if custom_path is None:
                raise KeyError(f"CUS_PATH.{cus} not found")
            
            # 절대 경로인지 확인
            custom_path = Path(custom_path)
            if custom_path.is_absolute():
                base_path = custom_path.resolve()
            else:
                # 상대 경로면 BASE_PATH 기준
                base_path = (Path(BASE_PATH) / custom_path).resolve()
                
        except KeyError:
            available = get_const("CUS_PATH")
            available_keys = list(available.keys()) if available else []
            raise ValueError(
                f"[SMART_PATH] Custom path preset '{cus}' not found in CUS_PATH. "
                f"Available presets: {available_keys}"
            )
            
    elif loc == "cache":
        # 캐시용 가상 경로 생성
        from usekit.classes.common.utils.helper_path_cache import set_path_cache

        # 캐시 루트는 BASE_PATH 아래의 .runtime_cache/{fmt}
        cache_root = Path(BASE_PATH) / "data" / ".runtime_cache" / fmt
        # 물리 폴더를 만들지 않고 메모리상 경로만 생성
        base_path = cache_root

        # 필요 시 set_path_cache 등록 (한 번만) / write 시 생성됨
        try:
            set_path_cache(fmt, "cache", base_path)
            logger.debug(f"[SMART_PATH] Virtual cache path set for {fmt}: {base_path}")
        except Exception as e:
            logger.warning(f"[SMART_PATH] Failed to set cache path: {e}")
       
    else:
        raise ValueError(
            f"[SMART_PATH] Unknown loc='{loc}'. "
            f"Valid options: base, sub, now, dir, tmp, cus"
        )
    
    # [2] user_dir이 loc != "dir"에서도 사용된 경우 추가 경로 붙이기
    if user_dir and loc != "dir":
        base_path = base_path / user_dir
    
    # [3] 파일명 처리
    if not filename:
        return base_path.resolve()
    
    # 확장자 자동 추가 (fmt_actual은 상단에서 이미 계산됨)
    file_path = Path(filename)
    if ensure_ext and not file_path.suffix:
        ext = fmt_actual  # Already computed at the top with any/cache logic
        file_path = file_path.with_suffix(ext)
    
    final_path = base_path / file_path
    return final_path.resolve()


def get_smart_path_str(*args, **kwargs) -> str:
    """get_smart_path의 문자열 버전"""
    return str(get_smart_path(*args, **kwargs))


# -----------------------------------------------------------------------------------------------
# [4]  배치 경로 생성 (여러 파일 한 번에)
# -----------------------------------------------------------------------------------------------

def get_smart_paths(
    fmt: str,
    filenames: list,
    loc: str = "base",
    user_dir: str = None,
    cus: str = None,
    ensure_ext: bool = True
) -> list[Path]:
    """
    여러 파일에 대한 경로를 한 번에 생성
    
    Examples:
        >>> get_smart_paths("json", ["a", "b", "c"], loc="tmp")
        [PosixPath('.../tmp/data/a.json'), ...]
        
        >>> get_smart_paths("json", ["x", "y"], cus="job01")
        [PosixPath('.../custom/x.json'), ...]
    """
    return [
        get_smart_path(fmt, fn, loc, user_dir, cus, ensure_ext)
        for fn in filenames
    ]


# -----------------------------------------------------------------------------------------------
# [5] 포맷별 경로 목록 생성
# -----------------------------------------------------------------------------------------------

def get_smart_path_list(
    fmt: str = "all",
    loc: str = "base",
    user_dir: str = None,
    cus: str = None,
    unique: bool = True
) -> list[Path]:
    """
    포맷군별 디렉토리 경로 리스트 반환
    """
    ext_map: Dict[str, str] = get_const("EXTENSION_MAP")
    
    if fmt == "all":
        format_list = list(ext_map.keys())
    else:
        format_list = [fmt]
    
    paths = []
    for format_type in format_list:
        try:
            path = get_smart_path(
                fmt=format_type,
                mod="log",
                filename=None,
                loc=loc,
                user_dir=user_dir,
                cus=cus,
                ensure_ext=False
            )
            paths.append(path)
        except Exception as e:
            logger.warning(
                f"[get_smart_path_list] Failed to get path for format '{format_type}': {e}"
            )
            continue
    
    # 중복 제거(순서 유지)
    if unique:
        paths = list(dict.fromkeys(paths))
    
    return paths

# -----------------------------------------------------------------------------------------------
# [6] 테스트 함수
# -----------------------------------------------------------------------------------------------

def test_smart_path():
    """스마트 경로 생성기 테스트"""
    test_cases = [
        # (fmt, mod, filename, loc, user_dir, cus, description)
        ("json", "any", "config", "base", None, None, "JSON 기본 경로"),
        ("json", "any", "temp", "sub", None, None, "JSON 서브 경로"),
        ("yaml", "any", "settings", "base", None, None, "YAML 기본 경로"),
        ("txt", "any", "note", "now", None, None, "현재 작업 디렉토리"),
        ("csv", "any", "data", "dir", "mydata", None, "사용자 디렉토리"),
        ("ddl", "any", "schema", "tmp", None, None, "DDL 임시 디렉토리"),
        ("json", "any", "backup", "tmp", None, None, "JSON 임시 디렉토리"),
        ("pyp", "any", "plugin", "base", None, None, "모듈 기본 경로"),
        ("md", "any", "readme", "base", "docs", None, "base + user_dir"),
        ("json", "all", "config", "cus", None, "job01", "커스텀 경로 job01"),
        ("yaml", "any", "settings", "cus", None, "backup", "커스텀 경로 backup"),
        ("txt", "any", "settings", "cus", None, None, "커스텀 경로 default"),
    ]
    
    print("=" * 80)
    print("get_smart_path() Test Results")
    print("=" * 80)
    
    for fmt, mod, fn, loc, udir, cus_preset, desc in test_cases:
        try:
            result = get_smart_path(fmt, mod, fn, loc, udir, cus_preset)
            status = "✅"
        except Exception as e:
            result = f"ERROR: {e}"
            status = "❌"
        
        print(f"\n{status} {desc}")
        print(f"   fmt={fmt}, mod={mod}, file={fn}, loc={loc}, user_dir={udir}, cus={cus_preset}")
        print(f"   → {result}")
    
    print("\n" + "=" * 80)
    
    # 🆕 get_smart_path_list 테스트
    print("\n🆕 Testing get_smart_path_list:")
    print("-" * 80)
    
    list_test_cases = [
        ("all", "base", "모든 포맷의 base 경로"),
        ("json", "base", "JSON 포맷만"),
        ("all", "tmp", "모든 포맷의 tmp 경로"),
        ("all", "sub", "모든 포맷의 sub 경로"),
    ]
    
    for fmt, loc, desc in list_test_cases:
        try:
            paths = get_smart_path_list(fmt=fmt, loc=loc)
            status = "✅"
            print(f"\n{status} {desc}")
            print(f"   fmt={fmt}, loc={loc}")
            print(f"   → Found {len(paths)} paths:")
            for i, p in enumerate(paths[:5], 1):  # 처음 5개만 표시
                print(f"      {i}. {p}")
            if len(paths) > 5:
                print(f"      ... and {len(paths) - 5} more")
        except Exception as e:
            status = "❌"
            print(f"\n{status} {desc}")
            print(f"   ERROR: {e}")
    
    print("\n" + "=" * 80)
    
    # path_cache 테스트
    print("\n Testing path_cache priority:")
    print("-" * 80)
    try:
        from usekit.classes.common.utils.helper_path_cache import set_path_cache
        
        # 캐시 설정 전
        print("\n[Before cache]")
        path1 = get_smart_path("json", "test", "base")
        print(f"json.base: {path1}")
        
        # 캐시 설정
        set_path_cache("json", "base", "custom/json")
        
        # 캐시 설정 후
        print("\n[After cache]")
        path2 = get_smart_path("json", "test", "base")
        print(f"json.base: {path2}")
        print(" Path cache working!")
        
    except ImportError:
        print("path_cache module not available")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_smart_path()

# -----------------------------------------------------------------------------------------------
#  MEMORY IS ECHO
# -----------------------------------------------------------------------------------------------