# Path: usekit.help.index.topic.help_part3.py
# -----------------------------------------------------------------------------------------------
#  MOSA Help System - Examples, Quick Start & Helper Function
# -----------------------------------------------------------------------------------------------

HELP_EXAMPLES = """
╔══════════════════════════════════════════════════════════════════════════╗
║  사용 예시 (Examples)                                                    ║
╚══════════════════════════════════════════════════════════════════════════╝

🎯 기본 사용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 읽기
    data = u.rjb()                    # config.json 읽기 (기본)
    data = u.rjb(name="users")        # users.json 읽기
    
    # 쓰기
    u.wjb(data={"key": "value"})      # dumps 쓰기
    u.wjb(data={"key": "value"}, name="new_file")
    
    # 업데이트
    u.ujb(data={"new": "data"})       # 병합
    
    # 삭제
    u.djb(name="old_file")            # 파일 삭제
    
    # 존재 확인
    if u.hjb(name="config"):
        print("파일 있음")

📍 위치 지정
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 하위 디렉토리
    u.rjs(name="config")             # data/json/json_sub/config.json
    
    # 현재 디렉토리
    u.rjn(name="local")              # 실행경로
    
    # 임시 디렉토리
    u.wjt(data={"temp": "data"})     # tmp/config.json

🎨 패턴 매칭
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 모든 user 파일 읽기
    users = u.rjb(name="user_*")
    for user in users:
        print(user["file"], user["data"])
    
    # 특정 패턴 검색
    logs = u.rjb(name="log_2024*", walk=True)
    
    # 임시 파일 삭제
    result = u.djt(name="temp_*")
    print(f"삭제: {result['success']}개")

🔍 keydata 활용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 중첩 경로 읽기
    email = u.rjb(name="config", keydata="user/email")
    
    # 중첩 경로 업데이트
    u.ujb(name="config", keydata="user/name", data="Bob")
    
    # 배열 접근
    first_item = u.rjb(keydata="items[0]/name")
    
    # 여러 파일의 특정 필드
    emails = u.rjb(name="user_*", keydata="email")

🔄 재귀 검색
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 모든 하위 디렉토리 검색
    configs = u.rjb(name="config_*", walk=True)
    
    # 특정 디렉토리 기준 재귀 검색
    u.rjs(name="settings_*", walk=True)

🎭 실전 예시
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1. 사용자 데이터 관리
    # 새 사용자 추가
    u.wjb(name="user_alice", data={
        "name": "Alice",
        "email": "alice@example.com",
        "created": "2024-11-07"
    })
    
    # 이메일만 업데이트
    u.ujb(name="user_alice", keydata="email", data="newemail@example.com")
    
    # 모든 사용자 이메일 조회
    emails = u.rjb(name="user_*", keydata="email")
    
    # 2. 설정 파일 관리
    # 기본 설정 읽기
    config = u.rjb(name="config")
    
    # 특정 설정 업데이트
    u.ujb(keydata="database/host", data="localhost")
    
    # 3. 임시 데이터 정리
    # 오래된 임시 파일 삭제
    result = u.djt(name="cache_*")
    print(f"{result['success']}개 파일 삭제")
    
    # 4. 로그 분석
    # 최근 로그 파일 찾기
    logs = u.rjb(name="log_20241107_*", walk=True)
    for log in logs:
        print(log["path"])

💎 고급 패턴
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 조건부 업데이트
    if u.hjb(name="config"):
        u.ujb(data={"updated": "2024-11-07"})
    else:
        u.wjb(data={"created": "2024-11-07"})
    
    # 배치 처리
    for user_file in u.ljb():
        data = u.rjb(name=user_file)
        # 처리 로직
        u.ujb(name=user_file, data=processed_data)
    
    # 백업 생성
    data = u.rjb(name="important")
    u.wjt(name=f"backup_{datetime.now():%Y%m%d}", data=data)
"""

HELP_QUICK = """
╔══════════════════════════════════════════════════════════════════════════╗
║  빠른 시작 가이드 (Quick Start)                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

⚡ 5분 만에 시작하기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣ 가장 기본 (JSON 파일) - small -> big -> option
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 쓰기
    u.wjb(data={"name": "Alice", "age": 25})
    
    # 읽기
    data = u.rjb()
    print(data["name"])  # Alice
    
    # 업데이트
    u.ujb(data={"age": 26})
    
    # 삭제
    u.djb()

2️⃣ 이름 지정하기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 파일명 지정
    u.wjb(data={"alice": {...}}, name="users")
    u.rjb(name="users")
    
    # 확장자는 자동 추가됨 (users.json)     
    # 파일명 미지정시 가상메모리(dumps)

3️⃣ 위치 바꾸기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.rjb()    # base 디렉토리 (기본)
    u.rjs()    # sub 디렉토리 (yaml 지정 경로)
    u.rjn()    # 현재 디렉토리
    u.rjd()    # 사용자 지정 디렉토리
    u.rjt()    # 임시 디렉토리 (tmp/)
    u.rjc()    # 캐시 디렉토리

4️⃣ 여러 파일 다루기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # user_로 시작하는 모든 파일
    users = u.rjb(name="user_*")
    for user in users:
        print(user["file"], user["data"])

5️⃣ 중첩 데이터 접근
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 데이터: {"user": {"profile": {"email": "a@b.com"}}}
    
    # 이메일만 읽기
    email = u.rjb(keydata="user/profile/email")
    
    # 이메일만 업데이트
    u.ujb(keydata="user/profile/email", data="new@example.com")

📝 다른 포맷 사용
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.wyb()    # YAML
    u.wtb()    # Text
    u.wcb()    # CSV
    u.wmb()    # Markdown

🎯 핵심 패턴 3가지
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1. 기본 사용
       u.rjb()  u.wjb()  u.ujb()  u.djb()
    
    2. 이름 + 위치
       u.rjs(name="config")
    
    3. 패턴 + keydata
       u.rjb(name="user_*", keydata="email")

💡 외우기 쉬운 방법
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.[무엇을][어떤포맷][어디서] / 동사 목적어 부사
    
    u.r j b    →  use.read.json.base
      ↑ ↑ ↑
      읽기/쓰기  json/yaml  base/sub
      
    예시:
    u.rjb()    read json base
    u.wys()    write yaml sub
    u.ujt()    update json tmp

🚀 바로 시작하기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 1단계: 데이터 쓰기
    u.wjb(data={"hello": "MOSA"})
    
    # 2단계: 데이터 읽기
    print(u.rjb())
    
    # 3단계: 수정하기
    u.ujb(data={"version": "1.0"})
    
    # 완료! 🎉

📚 더 알아보기
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    u.help("examples")    # 더 많은 예시
    u.help("pattern")     # 패턴 매칭 상세
    u.help("keydata")     # keydata 상세
"""

# ===============================================================================
# Export
# ===============================================================================

__all__ = [
    "HELP_EXAMPLES",
    "HELP_QUICK",
]
