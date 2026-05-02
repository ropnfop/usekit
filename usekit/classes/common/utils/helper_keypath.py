# Path: usekit.classes.common.utils.helper_keypath.py
# ----------------------------------------------------------------------------------------------- #
#  A creation by: The Little Prince × ROP × FOP
#  Universal key-path resolver — supports dict/list mixed navigation.
# ----------------------------------------------------------------------------------------------- #

from typing import Any, TypeVar

T = TypeVar('T')
_MISSING = object()


def resolve_key_path(
    data: Any, 
    keydata: str | list[str], 
    default: Any = None, 
    last_first: bool = False,
    recursive: bool = False,
    find_all: bool = False
) -> Any:
    """
    경로 키를 사용하여 중첩된 dict/list 구조를 탐색합니다.

    예시:
        # 경로 방식 (기본)
        resolve_key_path(data, "user/profile/name")
        resolve_key_path(data, "users[0]/email")
        resolve_key_path(data, ["users", "0", "email"])
        resolve_key_path(data, "items[-1]/id")  # 음수 인덱스 지원
        
        # 재귀 검색 방식
        resolve_key_path(data, "email", recursive=True)  # 첫 번째 email
        resolve_key_path(data, "email", recursive=True, find_all=True)  # 모든 email
        
    Args:
        data: 기본 구조 (dict 또는 list)
        keydata: 슬래시로 구분된 키 경로 문자열 또는 키 리스트
        default: 경로를 찾지 못한 경우 반환 값
        last_first: True인 경우 키를 역순으로 탐색
        recursive: True인 경우 전체 구조에서 키를 재귀적으로 검색
        find_all: recursive=True일 때, 모든 일치 항목을 리스트로 반환

    Returns:
        최종 해석된 값 또는 경로를 찾지 못한 경우 `default`
        find_all=True인 경우 일치하는 값들의 리스트 또는 None
    """
    if data is None:
        return default

    # 재귀 검색 모드
    if recursive:
        # keydata를 단일 키로 정규화
        if isinstance(keydata, str) and '/' not in keydata:
            target_key = keydata
        elif isinstance(keydata, list) and len(keydata) == 1:
            target_key = keydata[0]
        elif isinstance(keydata, str) and '/' in keydata:
            # 경로가 주어진 경우 마지막 키만 사용
            target_key = keydata.split('/')[-1]
        else:
            target_key = keydata[-1] if isinstance(keydata, list) else keydata
        
        results = []
        
        def search(obj, key):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == key:
                        results.append(v)
                        if not find_all:
                            return True  # 첫 번째 발견 시 중단
                    if search(v, key):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if search(item, key):
                        return True
            return False
        
        search(data, target_key)
        
        if find_all:
            return results if results else default
        else:
            return results[0] if results else default

    # 경로 탐색 모드 (기존 로직)
    if isinstance(keydata, str):
        key_chain = keydata.split('/')
    else:
        key_chain = list(keydata)
    
    if last_first:
        key_chain = list(reversed(key_chain))

    current = data
    for key in key_chain:
        if isinstance(current, dict):
            # 대괄호 표기법 처리: "users[0]" 또는 "users[-1]"
            if "[" in key and key.endswith("]"):
                base, idx_str = key[:-1].split("[", 1)
                current = current.get(base, _MISSING)
                
                if current is _MISSING:
                    return default
                
                if not isinstance(current, list):
                    return default
                    
                try:
                    idx = int(idx_str)
                    current = current[idx]
                except (ValueError, IndexError, KeyError):
                    return default
            else:
                current = current.get(key, _MISSING)
                if current is _MISSING:
                    return default
                    
        elif isinstance(current, list):
            # 숫자 인덱스 처리: "0" 또는 "-1"
            try:
                idx = int(key)
                current = current[idx]
            except (ValueError, IndexError, TypeError):
                return default
        else:
            # dict/list가 아닌 곳에서는 더 이상 탐색 불가
            return default

    return current


def set_key_path(
    data: dict | list,
    keydata: str | list[str],
    value: Any,
    create_missing: bool = True,
    recursive: bool = False
) -> bool:
    """
    경로 키를 사용하여 중첩된 dict/list 구조에 값을 설정합니다.
    
    예시:
        set_key_path(data, "user/profile/name", "John")
        set_key_path(data, "users[0]/email", "john@example.com")
        set_key_path(data, "email", "new@example.com", recursive=True)  # 모든 email 업데이트
        
    Args:
        data: 기본 구조 (dict 또는 list)
        keydata: 슬래시로 구분된 키 경로 문자열 또는 키 리스트
        value: 설정할 값
        create_missing: True인 경우 누락된 중간 dict를 자동 생성
        recursive: True인 경우 전체 구조에서 해당 키를 모두 업데이트
        
    Returns:
        성공 시 True, 실패 시 False
    """
    if data is None:
        return False
    
    # 재귀 업데이트 모드
    if recursive:
        # keydata를 단일 키로 정규화
        if isinstance(keydata, str) and '/' not in keydata:
            target_key = keydata
        elif isinstance(keydata, list) and len(keydata) == 1:
            target_key = keydata[0]
        else:
            target_key = keydata.split('/')[-1] if isinstance(keydata, str) else keydata[-1]
        
        updated = False
        
        def update_recursive(obj, key, val):
            nonlocal updated
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == key:
                        obj[k] = val
                        updated = True
                    else:
                        update_recursive(v, key, val)
            elif isinstance(obj, list):
                for item in obj:
                    update_recursive(item, key, val)
        
        update_recursive(data, target_key, value)
        return updated
    
    # 경로 설정 모드 (기존 로직)
    if isinstance(keydata, str):
        key_chain = keydata.split('/')
    else:
        key_chain = list(keydata)
    
    if not key_chain:
        return False
    
    current = data
    
    # 마지막 키를 제외하고 탐색
    for i, key in enumerate(key_chain[:-1]):
        if isinstance(current, dict):
            if "[" in key and key.endswith("]"):
                base, idx_str = key[:-1].split("[", 1)
                
                if base not in current:
                    if create_missing:
                        current[base] = []
                    else:
                        return False
                
                current = current[base]
                if not isinstance(current, list):
                    return False
                
                try:
                    idx = int(idx_str)
                    current = current[idx]
                except (ValueError, IndexError):
                    return False
            else:
                if key not in current:
                    if create_missing:
                        current[key] = {}
                    else:
                        return False
                current = current[key]
                
        elif isinstance(current, list):
            try:
                idx = int(key)
                current = current[idx]
            except (ValueError, IndexError):
                return False
        else:
            return False
    
    # 마지막 키로 값 설정
    last_key = key_chain[-1]
    
    if isinstance(current, dict):
        if "[" in last_key and last_key.endswith("]"):
            base, idx_str = last_key[:-1].split("[", 1)
            
            if base not in current:
                if create_missing:
                    current[base] = []
                else:
                    return False
            
            if not isinstance(current[base], list):
                return False
            
            try:
                idx = int(idx_str)
                current[base][idx] = value
                return True
            except (ValueError, IndexError):
                return False
        else:
            current[last_key] = value
            return True
            
    elif isinstance(current, list):
        try:
            idx = int(last_key)
            current[idx] = value
            return True
        except (ValueError, IndexError):
            return False
    
    return False


def delete_key_path(
    data: dict | list,
    keydata: str | list[str],
    recursive: bool = False
) -> bool:
    """
    경로 키를 사용하여 중첩된 dict/list 구조에서 값을 삭제합니다.
    
    예시:
        delete_key_path(data, "user/profile/name")
        delete_key_path(data, "users[0]")
        delete_key_path(data, "temp", recursive=True)  # 모든 temp 키 삭제
        
    Args:
        data: 기본 구조 (dict 또는 list)
        keydata: 슬래시로 구분된 키 경로 문자열 또는 키 리스트
        recursive: True인 경우 전체 구조에서 해당 키를 모두 삭제
        
    Returns:
        성공 시 True, 실패 시 False
    """
    if data is None:
        return False
    
    # 재귀 삭제 모드
    if recursive:
        if isinstance(keydata, str) and '/' not in keydata:
            target_key = keydata
        elif isinstance(keydata, list) and len(keydata) == 1:
            target_key = keydata[0]
        else:
            target_key = keydata.split('/')[-1] if isinstance(keydata, str) else keydata[-1]
        
        deleted = False
        
        def delete_recursive(obj, key):
            nonlocal deleted
            if isinstance(obj, dict):
                if key in obj:
                    del obj[key]
                    deleted = True
                for v in list(obj.values()):
                    delete_recursive(v, key)
            elif isinstance(obj, list):
                for item in obj:
                    delete_recursive(item, key)
        
        delete_recursive(data, target_key)
        return deleted
    
    # 경로 삭제 모드 (기존 로직)
    if isinstance(keydata, str):
        key_chain = keydata.split('/')
    else:
        key_chain = list(keydata)
    
    if not key_chain:
        return False
    
    # 부모 노드까지 탐색
    parent = data
    for key in key_chain[:-1]:
        if isinstance(parent, dict):
            if "[" in key and key.endswith("]"):
                base, idx_str = key[:-1].split("[", 1)
                parent = parent.get(base, _MISSING)
                
                if parent is _MISSING or not isinstance(parent, list):
                    return False
                
                try:
                    idx = int(idx_str)
                    parent = parent[idx]
                except (ValueError, IndexError):
                    return False
            else:
                parent = parent.get(key, _MISSING)
                if parent is _MISSING:
                    return False
                    
        elif isinstance(parent, list):
            try:
                idx = int(key)
                parent = parent[idx]
            except (ValueError, IndexError):
                return False
        else:
            return False
    
    # 마지막 키로 삭제
    last_key = key_chain[-1]
    
    if isinstance(parent, dict):
        if "[" in last_key and last_key.endswith("]"):
            base, idx_str = last_key[:-1].split("[", 1)
            
            if base not in parent or not isinstance(parent[base], list):
                return False
            
            try:
                idx = int(idx_str)
                del parent[base][idx]
                return True
            except (ValueError, IndexError):
                return False
        else:
            if last_key in parent:
                del parent[last_key]
                return True
            return False
            
    elif isinstance(parent, list):
        try:
            idx = int(last_key)
            del parent[idx]
            return True
        except (ValueError, IndexError):
            return False
    
    return False


def has_key_path(
    data: Any,
    keydata: str | list[str],
    recursive: bool = False
) -> bool:
    """
    경로 키가 존재하는지 확인합니다.
    
    예시:
        has_key_path(data, "user/profile/name")
        has_key_path(data, "users[0]/email")
        has_key_path(data, "email", recursive=True)  # 어디든 email이 있는지
        
    Args:
        data: 기본 구조 (dict 또는 list)
        keydata: 슬래시로 구분된 키 경로 문자열 또는 키 리스트
        recursive: True인 경우 전체 구조에서 키 존재 여부 확인
        
    Returns:
        경로가 존재하면 True, 그렇지 않으면 False
    """
    result = resolve_key_path(data, keydata, default=_MISSING, recursive=recursive)
    return result is not _MISSING