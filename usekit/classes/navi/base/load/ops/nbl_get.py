# Path: usekit.classes.navi.base.load.ops.nbl_get.py
# -----------------------------------------------------------------------------------------------
#  Get Operation - 캐시 조회 및 경로 조회
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional

from usekit.infra.navi_signature import params_for_get, warn_future_features
from usekit.classes.common.errors.helper_debug import log_and_raise
from usekit.classes.common.utils.helper_path import get_smart_path

# Cache imports
from usekit.classes.common.utils.helper_path_cache import get_path_cache
from usekit.classes.common.utils.helper_data_cache import get_data_cache


# ===============================================================================
# Get Path (op="path")
# ===============================================================================

def _get_path(p: dict) -> Optional[Path]:
    """
    Get current path configuration
    
    Args:
        p: params_for_get()로 추출된 파라미터
        
    Returns:
        Current configured path
        
    Priority:
        1. Runtime cache (path_cache)
        2. DSL_PATH (YAML)
        3. Default (DATA_PATH, etc.)
    """
    
    # [1] Runtime cache 확인
    cached_path = get_path_cache(p["fmt"], p["loc"])
    if cached_path:
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Path from cache: {cached_path}")
        return cached_path
    
    # [2] get_smart_path로 기본 경로 가져오기
    # (내부적으로 DSL_PATH → DATA_PATH 우선순위 적용)
    default_path = get_smart_path(
        fmt=p["fmt"],
        mod=p["mod"],
        filename=None,  # 디렉토리만
        loc=p["loc"],
        user_dir=p.get("dir_path"),
        cus=p["cus"],
        ensure_ext=False
    )
    
    if p["debug"]:
        print(f"[{p['fmt'].upper()}] Path from system: {default_path}")
    
    return default_path


# ===============================================================================
# Get Data Cache (op="cache")
# ===============================================================================

def _get_cache(p: dict) -> Any:
    """
    Get data from runtime cache
    
    Args:
        p: params_for_get()로 추출된 파라미터
        
    Returns:
        Cached data or default value
    
    Auto-naming:
        If name is not provided, uses loc as cache key
        Example: u.gjb() → cache key: "json.base.base"
    """
    
    # name이 없으면 loc를 name으로!
    if not p["name"]:
        p["name"] = p["loc"]
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Auto cache key: {p['loc']}")
    
    # 캐시에서 데이터 가져오기
    data = get_data_cache(
        fmt=p["fmt"],
        loc=p["loc"],
        name=p["name"],
        default=p["default"]
    )
    
    if p["debug"]:
        found = data is not p["default"]
        print(f"[{p['fmt'].upper()}] Get cache: {p['name']} -> {'Found' if found else 'Not found'}")
    
    # keydata 적용
    if p["keydata"] is not None and data is not p["default"]:
        from usekit.classes.common.utils.helper_keypath import resolve_key_path
        
        if p["debug"]:
            print(f"[{p['fmt'].upper()}] Navigating keydata: {p['keydata']}")
        
        return resolve_key_path(
            data,
            p["keydata"],
            default=p["default"],
            recursive=p["recursive"],
            find_all=p["find_all"]
        )
    
    return data


# ===============================================================================
# Main Get Operation
# ===============================================================================

@log_and_raise
def get_operation(**kwargs) -> Any:
    """
    Get operation - 캐시 조회 또는 경로 조회
    
    Operations:
        op="cache" (default): 데이터 캐시에서 조회
        op="path": 현재 설정된 경로 반환
    
    Args:
        **kwargs: 공통 Navigation 파라미터 (navi_signature 참조)
        
    Returns:
        op="cache": Cached data (or default)
        op="path": Path object
        
    Examples:
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [1] 빠른 캐시 조회 (name 자동 = loc)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        >>> get_operation(fmt="json", loc="base")
        # cache key: "json.base.base"
        {'key': 'value'}
        
        >>> get_operation(fmt="json", loc="sub")
        # cache key: "json.sub.sub"
        {'temp': 123}
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [2] 명시적 캐시 조회 (name 지정)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        >>> get_operation(fmt="json", loc="base", name="config")
        {'key': 'value'}  # 캐시된 데이터
        
        >>> get_operation(fmt="json", name="notfound", default={})
        {}  # 기본값
        
        # keydata 사용
        >>> get_operation(fmt="json", name="config", keydata="user/email")
        "alice@example.com"
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # [2] 경로 조회
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        >>> get_operation(fmt="json", loc="base", op="path")
        PosixPath('/project/data/json/json_main')
        
        # 런타임 캐시가 있으면 그것 반환
        >>> set_path_cache("json", "base", "custom/json")
        >>> get_operation(fmt="json", loc="base", op="path")
        PosixPath('/project/custom/json')
    """
    
    # 파라미터 추출
    p = params_for_get(**kwargs)
    
    # [Future] 향후 확장 기능 경고
    warn_future_features(p)
    
    # Operation 분기
    if p["op"] == "path":
        return _get_path(p)
    else:  # op="cache" (기본)
        return _get_cache(p)


# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = ["get_operation"]


if __name__ == "__main__":
    # Test
    print("Testing get_operation...")
    
    # Test path get
    print("\n[TEST] Get path:")
    path = get_operation(fmt="json", loc="base", op="path", debug=True)
    print(f"Result: {path}")
    
    # Test cache get (not exists)
    print("\n[TEST] Get cache (not exists):")
    data = get_operation(fmt="json", loc="base", name="test", default={}, debug=True)
    print(f"Result: {data}")
    
    # Set cache and get
    print("\n[TEST] Set and get cache:")
    from usekit.classes.common.utils.helper_data_cache import set_data_cache
    set_data_cache("json", "base", "test", {"key": "value"})
    data = get_operation(fmt="json", loc="base", name="test", debug=True)
    print(f"Result: {data}")
    
    # Get with keydata
    print("\n[TEST] Get with keydata:")
    set_data_cache("json", "base", "nested", {"user": {"email": "test@example.com"}})
    email = get_operation(fmt="json", loc="base", name="nested", keydata="user/email", debug=True)
    print(f"Result: {email}")