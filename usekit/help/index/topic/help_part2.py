# Path: usekit.help.index.topic.help_part2.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Memory-Oriented Software Architecture Documentation
#  Created by: THE Little Prince × ROP × FOP
# -----------------------------------------------------------------------------------------------

from typing import Optional, Literal
import textwrap

# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Pattern, Walk, Keydata
# -----------------------------------------------------------------------------------------------

HELP_PATTERN = """
╔══════════════════════════════════════════════════════════════════════════╗
║  패턴 매칭 (Pattern Matching)                                            ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 패턴 문자
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    *       0개 이상의 문자 매칭
    ?       정확히 1개 문자 매칭
    %       SQL LIKE 스타일 (* 와 동일)
    [abc]   a, b, c 중 하나
    [a-z]   a부터 z까지 하나

📖 사용 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 모든 user 파일
    u.rjb(name="user_*")
    [user_001.json, user_002.json, user_alice.json]
    
    # 특정 길이
    u.rjb(name="log_????")
    [log_2024.json, log_2025.json]
    
    # SQL LIKE 스타일
    u.rjb(name="%test%")
    [my_test_file.json, test_config.json]
    
    # 조합
    u.rjb(name="user_[0-9]*.json")
    [user_001.json, user_123.json]

🔄 walk와 조합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 현재 디렉토리만
    u.rjb(name="user_*")
    base/user_001.json
    base/user_002.json
    
    # 하위 디렉토리까지
    u.rjb(name="user_*", walk=True)
    base/user_001.json
    base/subdir/user_002.json
    base/subdir/deep/user_003.json

📊 반환 형태
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # read: 파일별 결과 리스트
    [
        {"file": "user_001", "path": "...", "data": {...}},
        {"file": "user_002", "path": "...", "data": {...}}
    ]
    
    # has: 하나라도 있으면 True
    True / False
    
    # delete: 상세 결과
    {
        "deleted": [Path(...), Path(...)],
        "failed": [],
        "total": 2,
        "success": 2
    }

⚠️ 안전성 (delete 전용)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 위험한 패턴 차단
    u.djb(name="*")              # ❌ ValueError
    u.djb(name="**")             # ❌ ValueError
    u.djb(name="*.*")            # ❌ ValueError
    u.djb(name="*_*", walk=True) # ❌ ValueError
    
    # 안전한 패턴
    u.djb(name="temp_*")         # ✅ OK
    u.djb(name="old_20241107_*") # ✅ OK
"""


HELP_WALK = """
╔══════════════════════════════════════════════════════════════════════════╗
║  재귀 검색 (walk)                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 개념
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    walk=False (기본값)
        지정된 디렉토리만 검색
        
    walk=True
        하위 디렉토리까지 재귀 검색

📂 디렉토리 구조 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    base/
    ├── config.json
    ├── user_001.json
    └── subdir/
        ├── user_002.json
        └── deep/
            └── user_003.json

📖 사용 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # walk=False (기본)
    u.rjb(name="user_*")
    결과: [user_001.json]  # base/ 만
    
    # walk=True
    u.rjb(name="user_*", walk=True)
    결과: [
        user_001.json,         # base/
        user_002.json,         # base/subdir/
        user_003.json          # base/subdir/deep/
    ]

🔗 loc와의 관계
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    loc와 walk는 독립적!
    
    • loc: "어디서" 검색할지 (base/sub/now/tmp/...)
    • walk: "얼마나 깊이" 검색할지 (True/False)
    
    예시:
    u.rjs(name="config_*")              # sub/ 만
    u.rjs(name="config_*", walk=True)   # sub/ 및 하위
    u.rjt(name="temp_*", walk=True)     # tmp/ 및 하위

⚡ 성능 고려
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    walk=True는 모든 하위 디렉토리를 검색하므로
    파일이 많을 경우 느릴 수 있습니다.
    
    • 정확한 위치를 알면: walk=False (기본값)
    • 어디 있는지 모르면: walk=True
    • 특정 범위 검색: loc 조합
"""


HELP_KEYDATA = """
╔══════════════════════════════════════════════════════════════════════════╗
║  중첩 경로 탐색 (keydata)                                                ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 개념
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    keydata는 중첩된 데이터 구조 내의 특정 경로를 지정합니다.
    
    구분자: "/" (슬래시)
    배열: [인덱스] 또는 /인덱스

📊 데이터 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
        "user": {
            "name": "Alice",
            "email": "alice@example.com",
            "profile": {
                "age": 25,
                "city": "Seoul"
            }
        },
        "items": [
            {"id": 1, "name": "Item A"},
            {"id": 2, "name": "Item B"}
        ]
    }

📖 사용 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 단일 키
    u.rjb(name="config", keydata="user")
    결과: {"name": "Alice", "email": "...", "profile": {...}}
    
    # 중첩 경로
    u.rjb(name="config", keydata="user/email")
    결과: "alice@example.com"
    
    # 더 깊은 경로
    u.rjb(name="config", keydata="user/profile/city")
    결과: "Seoul"
    
    # 배열 인덱스
    u.rjb(name="config", keydata="items[0]")
    u.rjb(name="config", keydata="items/0")
    결과: {"id": 1, "name": "Item A"}
    
    # 배열 + 키
    u.rjb(name="config", keydata="items[0]/name")
    결과: "Item A"

🔧 Operations별 동작
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    read
        keydata 경로의 값 반환
        u.rjb(name="config", keydata="user/email")
        
    update
        keydata 경로의 값만 업데이트 (나머지 유지)
        u.ujb(name="config", keydata="user/email", data="new@example.com")
        
    delete
        keydata 경로만 삭제 (파일은 유지)
        u.djb(name="config", keydata="user/temp_data")
        
    has
        keydata 경로 존재 여부 확인
        u.hjb(name="config", keydata="user/email")

⚙️ 고급 옵션
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    default
        keydata 없을 때 기본값
        u.rjb(keydata="user/phone", default="N/A")
        
    recursive
        재귀적으로 모든 매칭 경로 탐색
        u.rjb(keydata="email", recursive=True)
        
    find_all
        모든 매칭 값 반환 (리스트)
        u.rjb(keydata="items/*/name", find_all=True)
        
    create_missing
        중간 경로 자동 생성 (update/write)
        u.ujb(keydata="new/deep/path", data="value", create_missing=True)

🎨 Pattern + keydata 조합
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 여러 파일의 특정 필드만 읽기
    u.rjb(name="user_*", keydata="email")
    [
        {"file": "user_001", "data": "alice@example.com"},
        {"file": "user_002", "data": "bob@example.com"}
    ]
    
    # 여러 파일의 특정 필드 삭제
    u.djb(name="user_*", keydata="profile/temp_data")
    {
        "deleted": [Path(...), Path(...)],
        "success": 2
    }
"""

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "HELP_PATTERN",
    "HELP_WALK",
    "HELP_KEYDATA",
]
