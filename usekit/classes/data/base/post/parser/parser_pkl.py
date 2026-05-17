# Path: usekit.classes.data.base.post.parser.parser_pkl.py
# -----------------------------------------------------------------------------------------------
# A creation by: THE Little Prince × ROP × FOP
# Purpose: Pickle binary parser - 객체 직렬화/역직렬화 전용
# -----------------------------------------------------------------------------------------------

import os
import tempfile
import pickle
from pathlib import Path
from typing import Any, Union, Optional


# ───────────────────────────────────────────────────────────────
# Utilities
# ───────────────────────────────────────────────────────────────

def _ensure_path(file: Union[str, Path]) -> Path:
    """Path 객체 보장"""
    return file if isinstance(file, Path) else Path(file)


def _atomic_write_binary(path: Path, data: bytes) -> None:
    """임시 파일에 먼저 쓰고 os.replace로 교체하는 원자적 바이너리 쓰기"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("wb", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(data)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


# ───────────────────────────────────────────────────────────────
# Load / Loads
# ───────────────────────────────────────────────────────────────

def load(
    file,
    keydata: Optional[str] = None,
    search_value: Any = None,
    keydata_exists: bool = False,
    case_sensitive: bool = False,
    regex: bool = False,
    recursive: bool = False,
    find_all: bool = False,
    **kwargs
) -> Any:
    """
    피클 파일 로딩 (binary → 객체 복원)
    
    Args:
        file: Path/str or file-like object
        keydata: Keypath for dict/list navigation (e.g., "user/email")
        search_value: Optional value to match
        keydata_exists: Return True/False instead of data (performance)
        case_sensitive: Case-sensitive matching
        regex: Use regex for pattern matching
        recursive: Search recursively in nested structures
        find_all: Return all matches (recursive mode)
        **kwargs: Additional pickle options
    
    Returns:
        - If keydata specified: filtered result based on keydata
        - Otherwise: full unpickled object
    
    Examples:
        >>> # Basic load
        >>> data = load("cache.pkl")
        
        >>> # Keypath search (if PKL contains dict)
        >>> email = load("user.pkl", keydata="email")
        
        >>> # Filter list (if PKL contains list)
        >>> gmail_users = load("users.pkl", keydata="email", search_value="gmail")
        
        >>> # Existence check
        >>> has_email = load("config.pkl", keydata="email", keydata_exists=True)
    """
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Keydata search mode
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if keydata is not None:
        # Import sub-module for keydata search
        from usekit.classes.data.base.post.parser.parser_pkl_sub import _load_and_search
        
        return _load_and_search(
            file_path=file,
            keydata=keydata,
            search_value=search_value,
            keydata_exists=keydata_exists,
            case_sensitive=case_sensitive,
            regex=regex,
            recursive=recursive,
            find_all=find_all,
            **kwargs
        )
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Normal load mode
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    
    # file-like 객체 (Binary I/O)
    if hasattr(file, "read") and not isinstance(file, (str, Path)):
        return pickle.load(file)

    # 경로 기반
    path = _ensure_path(file)
    with path.open("rb") as f:
        return pickle.load(f)


def loads(binary: bytes, **kwargs) -> Any:
    """메모리 상의 바이너리에서 객체 복원"""
    return pickle.loads(binary)


# ───────────────────────────────────────────────────────────────
# Dump / Dumps
# ───────────────────────────────────────────────────────────────

def dump(
    data: Any,
    file,
    *,
    protocol: Optional[int] = None,
    overwrite: bool = True,
    safe: bool = True,
    append: bool = False,
    **kwargs
) -> None:
    """
    객체를 피클 파일로 저장 (객체 → binary)

    - file 이 file-like 이면 그대로 pickle.dump
    - file 이 Path/str 이면 실제 .pkl 파일로 저장
    - overwrite=False 이면 기존 파일 있을 때 예외
    - safe=True 이면 원자적 쓰기 사용
    - append=True 이면 기존 값을 리스트로 묶어 누적 저장
    """
    # 1) file-like 객체 (Binary I/O)
    if hasattr(file, "write") and not isinstance(file, (str, Path)):
        # 여기서는 호출하는 쪽에서 반드시 "wb" 모드로 열었다고 가정
        pickle.dump(data, file, protocol=protocol)
        return

    # 2) Path/str → 실제 파일 경로
    path = _ensure_path(file)

    if path.exists() and not overwrite:
        raise FileExistsError(f"[pkl.dump] Target exists and overwrite=False: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    # append 모드: 기존 데이터를 불러와 리스트로 누적
    if append and path.exists():
        try:
            with path.open("rb") as f:
                old = pickle.load(f)
            if isinstance(old, list):
                old.append(data)
            else:
                old = [old, data]
            data = old
        except Exception:
            data = [data]

    binary = pickle.dumps(data, protocol=protocol)

    if safe:
        _atomic_write_binary(path, binary)
    else:
        with path.open("wb") as f:
            f.write(binary)


def dumps(data: Any, *, protocol: Optional[int] = None, **kwargs) -> bytes:
    """
    객체를 바이너리로 직렬화 (메모리 상)
    """
    return pickle.dumps(data, protocol=protocol)


# ───────────────────────────────────────────────────────────────
# Test helper
# ───────────────────────────────────────────────────────────────

def _test(base="sample.pkl"):
    sample_data = {
        "name": "DSL",
        "version": "0.1.0",
        "features": ["pickle", "routing", "dsl", "ext"]
    }

    dump(sample_data, base)
    print("[PKL] wrote:", base)

    loaded = load(base)
    print("[PKL] read:", loaded)

    dump({"extra": 123}, base, append=True)
    print("[PKL] append:", load(base))

    binary = dumps(sample_data)
    print("[PKL] dumps:", binary[:40], "...")

    restored = loads(binary)
    print("[PKL] loads:", restored)