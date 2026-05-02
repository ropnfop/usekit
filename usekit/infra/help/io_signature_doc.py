# Path: usekit.infra.io_signature_doc.py
# -----------------------------------------------------------------------------------------------
#  Universal I/O Signature - Documentation & Examples
#  Created by: THE Little Prince × ROP × FOP
#  Version: 2.0
#  
#  This module contains documentation strings, examples, and printing utilities
#  Separated from core io_signature.py for cleaner code organization
# -----------------------------------------------------------------------------------------------

# ===============================================================================
# Parameter structure documentation string
# ===============================================================================

IO_PARAMS_STRUCTURE = """
Universal I/O Parameter Structure (3 Layers + Format-Specific):

    # ---------------------------------------------------------------
    # [1] USER LAYER - Semantic inputs
    # ---------------------------------------------------------------
    data: Any = None,
    name: Optional[str] = None,
    mod: str = "all",
    dir_path: Optional[str] = None,
    path: Optional[str] = None,
    loc: str = "base",
    cus: Optional[str] = None,
    
    # ---------------------------------------------------------------
    # [2] TARGETING LAYER - Paths & Filters
    # ---------------------------------------------------------------
    *,
    # Basic targeting
    keydata: Optional[str | list[str]] = None,
    default: Any = None,
    recursive: bool = False,
    find_all: bool = False,
    create_missing: bool = True,
    walk: bool = False,
    
    # TXT-specific: Search options
    regex: bool = False,
    case_sensitive: bool = False,
    invert_match: bool = False,
    
    # TXT-specific: Tail modes
    tail_all: Optional[int] = None,
    tail_top: Optional[int] = None,
    tail_mid: Optional[int] = None,
    tail_bottom: Optional[int] = None,
    
    # TXT-specific: Line options
    lines: bool = False,
    line_numbers: bool = False,
    strip: bool = False,
    strip_empty: bool = False,
    
    # TXT-specific: Write options
    append: bool = False,
    append_newline: bool = True,
    replace_all: bool = True,
    max_count: Optional[int] = None,
    
    # [Future] Reserved for expansion: kc, kf, pyp
    k: Optional[str] = None,
    kv: Any = None,
    kc: str = "eq",
    kf: Optional[str] = None,
    
    # ---------------------------------------------------------------
    # [3] SYSTEM LAYER - Execution control
    # ---------------------------------------------------------------
    fmt: str = "json",
    mode: str = "read",
    mode_sub: Optional[str] = None,
    
    # TXT-specific: Encoding & Safety
    encoding: str = "utf-8",
    newline: Optional[str] = None,
    wrap: bool = False,
    overwrite: bool = True,
    safe: bool = True,
    
    debug: bool = False,
    **kwargs
"""

# ===============================================================================
# Layer-specific documentation
# ===============================================================================

LAYER_DOCS = {
    "USER_LAYER": """
    ╔════════════════════════════════════════════════════════════════════╗
    ║  사용자 의도 표현 (What & Where)                                  ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    📌 Core inputs:
    ─────────────────────────────────────────────────────────────────────
    - data: 데이터 내용 (write/update에서 사용)
    - name: 파일/키 이름
    - mod: 동작 범위 ('all', 'key', 'value', 'name', 'path')
    - dir_path: 디렉토리 경로 (직접 지정)
    - path: 전체 경로 (직접 지정)
    - loc: 위치 단축키 ('base'/'sub'/'dir'/...)
    - cus: 커스텀 경로
    """,
    
    "TARGETING_LAYER": """
    ╔════════════════════════════════════════════════════════════════════╗
    ║  대상 선택 & 필터링 (Which data to target)                        ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    📌 Basic targeting (모든 포맷):
    ─────────────────────────────────────────────────────────────────────
    - keydata: 키 경로 또는 검색 패턴
    - default: 값이 없을 때 기본값
    - recursive: 중첩 구조 재귀 탐색
    - find_all: 모든 매칭 결과 반환
    - create_missing: 없는 경로 자동 생성
    - walk: 디렉토리 트리 순회
    
    📝 TXT-specific: Search & Replace
    ─────────────────────────────────────────────────────────────────────
    - regex: 정규식 사용 (grep -E)
    - case_sensitive: 대소문자 구분 (grep 기본)
    - invert_match: 역매칭 (grep -v)
    
    📝 TXT-specific: Tail modes (head/tail functionality)
    ─────────────────────────────────────────────────────────────────────
    - tail_all: 처음 N줄 (None=전체)
    - tail_top: 처음 N줄 (head)
    - tail_mid: 중간 N줄
    - tail_bottom: 마지막 N줄 (tail)
    
    📝 TXT-specific: Line operations
    ─────────────────────────────────────────────────────────────────────
    - lines: 리스트로 반환 (기존 기능)
    - line_numbers: 라인 번호 추가 (cat -n)
    - strip: 공백 제거 (기존 기능)
    - strip_empty: 빈 줄 제거
    
    📝 TXT-specific: Write & Replace
    ─────────────────────────────────────────────────────────────────────
    - append: 추가 모드 (기존 기능)
    - append_newline: 추가 시 줄바꿈 (기존 기능)
    - replace_all: 전체 교체 vs 첫 번째만 (sed 's/old/new/g')
    - max_count: 최대 교체 횟수 제한
    
    [Future] 향후 확장 (예약됨):
    ─────────────────────────────────────────────────────────────────────
    - k, kv, kc: 조건 필터링 (WHERE status='active')
    - kf: 키 정의 파일 (프리셋 경로)
    """,
    
    "SYSTEM_LAYER": """
    ╔════════════════════════════════════════════════════════════════════╗
    ║  실행 방법 제어 (How to execute)                                  ║
    ╚════════════════════════════════════════════════════════════════════╝
    
    📌 Core:
    ─────────────────────────────────────────────────────────────────────
    - fmt: 파일 포맷 (json/yaml/txt/csv 등)
    - mode: 동작 모드 (read/write/update/delete/exists)
    - mode_sub: 서브 모드 (향후 확장)
    - debug: 디버그 모드
    
    📝 TXT-specific: Encoding & Safety
    ─────────────────────────────────────────────────────────────────────
    - encoding: 파일 인코딩 (utf-8/cp949/...)
    - newline: 줄바꿈 모드 (None=platform, '\n'=Unix, '\r\n'=Windows)
    - wrap: 자동 타입 변환 (dict/list → str)
    - overwrite: 덮어쓰기 허용
    - safe: Atomic write (temp file → replace)
    """,
}

# ===============================================================================
# Print structure function
# ===============================================================================

def print_structure():
    """Print parameter structure documentation"""
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "Universal I/O Parameter Structure" + " " * 25 + "║")
    print("╚" + "═" * 78 + "╝")
    
    for layer, doc in LAYER_DOCS.items():
        print(f"\n{doc}")
    
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 30 + "TXT Feature Summary" + " " * 29 + "║")
    print("╚" + "═" * 78 + "╝")
    
    print("""
    ✅ Unix standard tools perfectly replicated:
    ───────────────────────────────────────────────────────────────────────
    cat             → load()
    head            → load(tail_top=N)
    tail            → load(tail_bottom=N)
    grep            → load(keydata="pattern")
    grep -v         → load(keydata="pattern", invert_match=True)
    grep -i         → load(keydata="pattern", case_sensitive=False)
    grep -E         → load(keydata="pattern", regex=True)
    sed 's/old/new' → dump("new", keydata="old")
    sed -i          → dump(..., safe=True)  # atomic write
    cat -n          → load(line_numbers=True)
    
    ✅ Composable operations:
    ───────────────────────────────────────────────────────────────────────
    # Search ERROR in last 100 lines
    load(keydata="ERROR", tail_bottom=100)
    
    # Replace ERROR → FIXED in last 100 lines
    dump("FIXED", keydata="ERROR", tail_bottom=100)
    
    # Redact sensitive info with regex (last 1000 lines)
    dump("[REDACTED]", keydata=r"\\d{3}-\\d{2}-\\d{4}", 
         regex=True, tail_bottom=1000)
    """)

# ===============================================================================
# Usage examples
# ===============================================================================

def print_examples():
    """Print usage examples"""
    from .io_signature import params_for_read, params_for_write, params_for_update, get_io_params
    
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 30 + "Usage Examples" + " " * 34 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    # Example 1: Basic read (all formats)
    print("📖 Example 1: Basic read")
    print("─" * 80)
    p = params_for_read(name="config", keydata="user/email")
    print(f"  mode     : {p['mode']}")
    print(f"  name     : {p['name']}")
    print(f"  keydata  : {p['keydata']}")
    print(f"  fmt      : {p['fmt']} (default)")
    print()
    
    # Example 2: TXT with tail
    print("📝 Example 2: TXT read with tail")
    print("─" * 80)
    p = params_for_read(fmt="txt", name="app.log", tail_bottom=100)
    print(f"  fmt          : {p['fmt']}")
    print(f"  tail_bottom  : {p['tail_bottom']}")
    print(f"  encoding     : {p['encoding']} (default)")
    print()
    
    # Example 3: TXT search with regex
    print("🔍 Example 3: TXT search with regex")
    print("─" * 80)
    p = params_for_read(
        fmt="txt",
        name="app.log",
        keydata=r"ERROR:\s+\d+",
        regex=True,
        case_sensitive=False,
        tail_bottom=500
    )
    print(f"  keydata        : {p['keydata']}")
    print(f"  regex          : {p['regex']}")
    print(f"  case_sensitive : {p['case_sensitive']}")
    print(f"  tail_bottom    : {p['tail_bottom']}")
    print()
    
    # Example 4: TXT replace (update mode)
    print("✏️  Example 4: TXT replace (sed-like)")
    print("─" * 80)
    p = params_for_update(
        fmt="txt",
        name="app.log",
        data="FIXED",
        keydata="ERROR",
        replace_all=True,
        max_count=100,
        tail_bottom=1000
    )
    print(f"  data         : {p['data']}")
    print(f"  keydata      : {p['keydata']}")
    print(f"  replace_all  : {p['replace_all']}")
    print(f"  max_count    : {p['max_count']}")
    print(f"  tail_bottom  : {p['tail_bottom']}")
    print(f"  safe         : {p['safe']} (atomic write)")
    print()
    
    # Example 5: TXT append
    print("➕ Example 5: TXT append")
    print("─" * 80)
    p = params_for_write(
        fmt="txt",
        name="events.log",
        data="New event occurred",
        append=True,
        append_newline=True
    )
    print(f"  append         : {p['append']}")
    print(f"  append_newline : {p['append_newline']}")
    print(f"  wrap           : {p['wrap']}")
    print()
    
    # Example 6: Pattern read with walk
    print("🗂️  Example 6: Pattern read with walk (all formats)")
    print("─" * 80)
    p = params_for_read(name="user_*", walk=True)
    print(f"  name  : {p['name']}")
    print(f"  walk  : {p['walk']}")
    print()
    
    # Example 7: Check all TXT params present
    print("🔍 Example 7: All TXT params available")
    print("─" * 80)
    p = get_io_params(fmt="txt")
    txt_params = [
        "regex", "case_sensitive", "invert_match",
        "tail_all", "tail_top", "tail_mid", "tail_bottom",
        "lines", "line_numbers", "strip", "strip_empty",
        "append", "append_newline", "replace_all", "max_count",
        "encoding", "newline", "wrap", "overwrite", "safe"
    ]
    
    for param in txt_params:
        assert param in p, f"Missing: {param}"
        print(f"  ✅ {param:20s} = {p[param]}")
    
    print("\n" + "─" * 80)
    print("✅ All TXT parameters present in io_signature!")

# ===============================================================================
# __all__ export
# ===============================================================================

__all__ = [
    "IO_PARAMS_STRUCTURE",
    "LAYER_DOCS",
    "print_structure",
    "print_examples",
]

# ===============================================================================
# Main execution
# ===============================================================================

if __name__ == "__main__":
    print_structure()
    print("\n\n")
    print_examples()