# CLAUDE.md

This is a **USEKIT project** — Memory-Oriented Software Architecture (MOSA).

---

## Quick Reference

```python
from usekit import u          # 3-letter shorthand (REPL, scripts)
from usekit import use        # full-chain (readable code)
from usekit import safe, s    # safe mode (lazy load, ~8s first use)
from usekit import uw         # watch/output: uw.p(), uw.ok(), uw.warn()
from usekit import ut         # time utils: ut.now(), ut.stamp()
from usekit import ud         # DB utils: ud.query(), ud.execute()

# Same thing, two styles:
u.rjb(name="config")          # read json base
use.read.json.base("config")  # identical
```

---

## Core Rules

1. **Use USEKIT APIs first.** No raw `open()`, `os.path`, `pathlib` for project data.
2. **No hardcoded absolute paths.** All paths relative to `ENV_BASE_PATH`.
3. **No `sys.path.append`.** Use `u.ipb("module")` or `u.xpb("mod:func")`.
4. **Do not rewrite project structure** unless explicitly requested.

---

## 3-Letter Routing

```
u.[ACTION][FORMAT][LOCATION]()
```

### ACTION (15)

| 분류 | 코드 | 전체 이름 |
|------|------|-----------|
| **데이터** | `r` | read |
| | `w` | write |
| | `u` | update |
| | `d` | delete |
| | `h` | has |
| | `e` | emit |
| **네비** | `p` | path |
| | `f` | find |
| | `l` | list |
| | `g` | get |
| | `s` | set |
| **실행** | `x` | exec |
| | `i` | imp (import) |
| | `b` | boot |
| | `c` | close |

### FORMAT (10)

| 분류 | 코드 | 전체 이름 |
|------|------|-----------|
| **일반** | `j` | json |
| | `y` | yaml |
| | `c` | csv |
| | `t` | txt |
| | `m` | md |
| | `s` | sql |
| | `d` | ddl |
| | `p` | pyp |
| **기타** | `k` | km (keymemory) |
| | `a` | any |

### LOCATION (8)

| 분류 | 코드 | 전체 이름 |
|------|------|-----------|
| **기본** | `b` | base |
| | `s` | sub |
| | `d` | dir |
| | `n` | now |
| | `t` | tmp |
| **확장** | `p` | pre |
| | `c` | cache |
| | `m` | mem |

---

## Most-Used Patterns

| 패턴 | 의미 | 예시 |
|------|------|------|
| `u.rjb()` | read json base | `u.rjb("config")` |
| `u.wjb()` | write json base | `u.wjb({"k":"v"}, "out")` |
| `u.hjb()` | has json base | `if u.hjb("config"): ...` |
| `u.ljb()` | list json base | `files = u.ljb()` |
| `u.wtb()` | write txt base | `u.wtb(report, "log")` |
| `u.wmb()` | write md base | `u.wmb(md_text, "doc")` |
| `u.xsb()` | exec sql base | `rows = u.xsb("SELECT ...")` |
| `u.xdb()` | exec ddl base | `u.xdb("CREATE TABLE ...")` |
| `u.xpb()` | exec pyp base | `u.xpb("mod:func", arg1)` |
| `u.ipb()` | import pyp base | `u.ipb("module_name")` |
| `u.gjb()` | get json base (read+keydata) | `u.gjb("cfg", keydata="user/email")` |
| `u.ejm()` | emit json mem | `u.ejm({"k": "v"})` |

### Positional Args

`name`과 `data`는 keyword 없이 positional로 사용 가능:

```python
u.rjb("config")              # name="config" 생략
u.wjb({"k": "v"}, "out")    # data=, name= 생략
u.hjb("config")
```

### Key Parameters

```python
data=           # 쓸 데이터 (w/u 필수)
name=           # 파일명 (확장자 자동추가, 미지정=dumps)
keydata=        # 중첩 경로 "user/email", "items[0]/name"
walk=True       # 하위 디렉토리 재귀 검색
default=        # keydata 없을 때 기본값
append=True     # 기존 파일에 추가
append_mode=    # "jsonl" | "array" | "object" | (미지정=자동감지)
jsonl=True      # JSONL 형식으로 읽기
dir_path=       # loc 기준 서브 경로 추가
```

### dir_path — 서브 경로 지정

두 번째 positional 인자로 loc 기준 하위 경로를 자유롭게 지정:

```python
# data/json/base/mytest/abc/test.json
u.wjb({"k": "v"}, "test", "mytest/abc")
u.rjb("test", "mytest/abc")

# full-chain도 동일
use.read.json.base("test", "mytest/abc")

# /로 시작하면 절대 경로
u.rjb("test", "/external/path")
```

### JSON Append 패턴

```python
# JSONL (줄 단위 JSON)
u.wjb({"date": "2026-01-01", "user": "Alice"}, "log", append=True, append_mode="jsonl")
u.rjb("log", jsonl=True)   # → [{"date":...}, ...]

# 배열에 항목 추가
u.wjb([{"id": 1}], "items")
u.wjb({"id": 2}, "items", append=True, append_mode="array")

# 오브젝트 병합
u.wjb({"a": 1}, "cfg")
u.wjb({"b": 2}, "cfg", append=True, append_mode="object")

# 자동 감지 (기존 파일 구조 보고 array/object 자동 선택)
u.wjb(new_item, "data", append=True)
```

---

## Directory Convention

```
src/base/          — main source code        (loc=b)
src/sub/           — sub modules             (loc=s)
data/json/base/    — JSON data
data/table/db/     — SQLite databases (base.db)
data/table/sql/    — SQL query files
data/table/ddl/    — DDL files
data/common/txt/   — text files
data/common/csv/   — CSV files
data/common/md/    — markdown files
data/log/base/     — log files
data/tmp/          — temporary files         (loc=t)
docs/base/         — documentation
```

---

## SQL

```python
# DDL
u.xdb("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")

# DML/Query — returns namedtuple-like DotDict rows
rows = u.xsb("SELECT * FROM users WHERE age > 20")
for row in rows:
    print(row.id, row.name)    # attribute access
    print(row._fields)         # column names
```

---

## Location-Based Import (EXEC layer)

USEKIT의 핵심 추상화 — `sys.path` 조작 없이 **위치(loc) 기준으로 모듈을 동적 탐색**.

```
u.[ACTION]pb("[dotted.path]:[func]", *args)
              ↑                ↑
         src/base/ 기준     실행할 함수명
         점(.)은 디렉토리 구분자
```

### 일반 Python vs USEKIT

```python
# 일반 Python
import sys
sys.path.append("/some/path/src/base")
from a.b.c import func
func(1, 2)

# USEKIT
u.xpb("a.b.c:func", 1, 2)   # 실행 → 결과 반환
u.ipb("a.b.c")               # import → 모듈 객체 반환
```

### 경로 규칙

```
src/base/
  calc.py              → "calc:func"
  test/
    test.py            → "test.test:func"
    utils/
      math.py          → "test.utils.math:func"
```

### API

```python
# xpb — 함수 실행, 결과 반환 (args / kwargs 모두 지원)
result = u.xpb("calc:add", 10, 20)               # → 30
result = u.xpb("test.test:add", 10, 20)          # → 30  (중첩 경로)
result = u.xpb("demo:report", "Alice", 95)        # → {'name': 'Alice', ...}
result = u.xpb("demo:report", "Bob", grade="B")   # → kwargs 지원

# ipb — 모듈 객체 반환
calc = u.ipb("calc")                              # → <module>
calc.add(3, 4)                                    # → 7

# imp.pyp.sub — sub 모듈에서 함수를 현재 네임스페이스로 주입
use.imp.pyp.sub("utils : upper, repeat")          # upper(), repeat() 직접 사용 가능
use.imp.pyp.sub("ledger_parts.data : get_records, get_budgets")
```

### REPL 실행기 패턴

`from usekit import u` 한 줄이면 **import 없이 어떤 모듈의 함수든 즉시 실행** 가능.
REPL, 스크립트, 자동화 모두 동일한 방식으로 동작한다.

```python
from usekit import u

# 파일이 src/base/에 있으면 바로 호출
u.xpb("calc:add", 3, 7)              # → 10
u.xpb("calc:greet", "world")         # → "안녕, world!"
u.xpb("test.test:add", 100, 200)     # → 300

# 루프에서도 동일
for name, score in [("Alice", 95), ("Bob", 72)]:
    result = u.xpb("demo:report", name, score)
```

### 두 가지 실행 모드

```python
# 1. 스크립트 모드 — 함수명 생략, if __name__ == "__main__" 블록 실행
u.xpb("main")           # main.py 의 __main__ 블록 실행, 반환값 없음

# 2. 함수 모드 — 특정 함수 호출, 반환값 있음
result = u.xpb("main:main")    # → "done"
result = u.xpb("calc:add", 3, 7)  # → 10
```

| 형태 | 실행 대상 | 반환값 |
|------|-----------|--------|
| `u.xpb("mod")` | `if __name__ == "__main__"` 블록 | 없음 |
| `u.xpb("mod:func", *args)` | 지정 함수 | 함수 반환값 |

### base / sub 분리 구조

`base`는 진입점, `sub`는 기능 모듈 — `use.imp.pyp.sub()`으로 연결.

```
src/base/
  score_app.py          ← 진입점: u.xpb("score_app")

src/sub/
  score_parts/
    db.py               ← SQL 처리
    report.py           ← JSON 처리
```

```python
# score_app.py (base)
from usekit import use, uw

def main():
    use.imp.pyp.sub("score_parts.db : reset, insert, fetch_all")
    use.imp.pyp.sub("score_parts.report : save, load")

    reset()
    insert("Alice", 95)
    rows = fetch_all()
    save(rows)

if __name__ == "__main__":
    main()
```

```python
# 실행 (REPL or 스크립트)
u.xpb("score_app")
```

### 출력 보관 패턴

실행 결과를 JSON / TXT / MD 로 별도 저장:

```python
from usekit import u, uw, ut

# JSON으로 결과 보관 (JSONL 누적)
u.wjb({"ts": ut.str(), "result": result}, "output_log", append=True, append_mode="jsonl")

# TXT로 로그 누적
u.wtb(f"[{ut.str()}] {message}", "run_log", append=True)

# MD로 리포트 저장 → docs/base/report.md
md = f"""# 결과 리포트

생성: {ut.str()}

## 내용
...
"""
u.wmb(md, "report")
```

저장 위치:
- `u.wjb()` → `data/json/base/`
- `u.wtb()` → `data/common/txt/`
- `u.wmb()` → `docs/base/`

> `uw.history()`는 `uw.p()`로 출력한 것만 기록함. `uw.ok()` / `uw.info()` 등은 포함 안 됨.

### 작성 후 즉시 실행 패턴

`u.wpb()`로 소스를 작성하고 `u.xpb()`로 바로 실행 — 코드 생성과 실행을 한 흐름으로 처리.
**AI 코딩 워크플로우의 핵심 패턴**: AI가 코드를 작성하고 결과 확인까지 한 번에 수행.

```python
# 1. 소스 작성 (src/base/test.py 로 저장됨)
u.wpb(r'''
def main():
    print("동적 스크립트")
    return 42

if __name__ == "__main__":
    main()
''', "test")

# 2. 즉시 실행
u.xpb("test")           # 스크립트 모드 — __main__ 블록 실행
u.xpb("test:main")      # 함수 모드 — 반환값 42
```

> AI는 `u.wpb()`로 코드를 작성하고 `u.xpb()`로 즉시 실행 및 검증한다.
> 파일로 저장되므로 이후 `u.xpb()` / `u.ipb()`로 재사용 가능.

---

## Support Utilities

### uw — Watch/Output

```python
uw.p(value)          # print (타입 무관)
uw.info("msg")       # [INFO] msg
uw.warn("msg")       # [WARN] msg
uw.err("msg")        # [ERR]  msg
uw.ok("msg")         # [OK]   msg
uw.tag("msg", "TAG") # [TAG]  msg
uw.here()            # 현재 호출 위치 출력 (디버그)
uw.history()         # 출력 기록 반환
uw.clear()           # 기록 초기화
```

### ut — Time

```python
ut.now()                          # datetime 객체
ut.str()                          # "2026-01-01 12:00:00" (현재 시각 문자열)
ut.str(dt, fmt="%Y%m%d")         # 포맷 지정
ut.stamp()                        # Unix timestamp (int)
ut.diff(dt1, dt2)                 # timedelta
ut.sleep(1.5)                     # 초 단위 대기
ut.sleep_ms(500)                  # 밀리초 단위 대기
```

### s — Safe Layer

`u.*`는 실패 시 에러 발생, `s.*`는 실패 시 조용히 넘어감 (cleanup, optional 작업에 사용):

```python
s.djb("name")    # safe delete — 파일 없어도 crash 없음
s.rjb("name")    # safe read   — 없으면 None 반환
```

---

## Help System

```python
# 토픽별 도움말
use.help("overview")    # MOSA 아키텍처 개요
use.help("quick")       # 퀵스타트 가이드
use.help("action")      # 액션 목록
use.help("object")      # 포맷 목록
use.help("location")    # 위치 목록
use.help("examples")    # 사용 예제
use.help("keydata")     # 중첩 경로 접근
use.help("walk")        # 재귀 검색
use.help("alias")       # 파라미터 별칭
use.help("pattern")     # 패턴 매칭

# 개별 메서드 도움말
help(u.rjb)             # "read json base"
```

---

## Constraints

- **emit(e)** → `u.ejm()` 사용 (short alias만 안정), `use.emit.json.mem()` full-name은 현재 미작동
- **emit(e)** → mem(m) 위치만: `u.ejm(data={...})` ✅ / `u.ejb()` ❌
- **emit 반환값** → 항상 `str` (파일 저장 없음, 메모리 직렬화만)
  ```python
  u.ejm({"k": "v"})   # → '{\n  "k": "v"\n}'  (str)
  u.ejm([1, 2, 3])    # → '[\n  1,\n  2,\n  3\n]'  (str)
  u.ejm("hello")      # → 'hello'  (str)
  ```
- **delete 패턴 안전장치** → `u.djb(name="*")` 차단됨
- **name 미지정** → dumps(가상메모리), 파일 생성 안 됨
- **SQL row** → `row.col` 속성 접근, `row._fields` 컬럼명 리스트
- **loc=p** → `pre`(pre-defined path), path가 아님
- **모바일 환경** → Termux + Samsung Browser, 출력 간결하게
