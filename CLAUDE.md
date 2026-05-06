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

```python
# base의 모듈 실행
use.exec.pyp.base("examples.ledger_app.main")

# sub에서 함수 import (sys.path 조작 불필요)
use.imp.pyp.sub("ledger_parts.data : get_records, get_budgets")
use.imp.pyp.sub("ledger_parts.db : reset_tables, insert_records")

# 실행 with args
use.exec.pyp.base("examples.pyp_args_demo:add", 10, 20)
use.exec.pyp.base("mod:func", arg1, key=val)
```

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

## Constraints

- **emit(e)** → `u.ejm()` 사용 (short alias만 안정), `use.emit.json.mem()` full-name은 현재 미작동
- **emit(e)** → mem(m) 위치만: `u.ejm(data={...})` ✅ / `u.ejb()` ❌
- **delete 패턴 안전장치** → `u.djb(name="*")` 차단됨
- **name 미지정** → dumps(가상메모리), 파일 생성 안 됨
- **SQL row** → `row.col` 속성 접근, `row._fields` 컬럼명 리스트
- **loc=p** → `pre`(pre-defined path), path가 아님
- **모바일 환경** → Termux + Samsung Browser, 출력 간결하게
