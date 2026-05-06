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
| `u.rjb()` | read json base | `u.rjb(name="config")` |
| `u.wjb()` | write json base | `u.wjb(data={"k":"v"}, name="out")` |
| `u.hjb()` | has json base | `if u.hjb(name="config"): ...` |
| `u.ljb()` | list json base | `files = u.ljb()` |
| `u.wtb()` | write txt base | `u.wtb(data=report, name="log")` |
| `u.wmb()` | write md base | `u.wmb(data=md_text, name="doc")` |
| `u.xsb()` | exec sql base | `rows = u.xsb("SELECT ...")` |
| `u.xdb()` | exec ddl base | `u.xdb("CREATE TABLE ...")` |
| `u.xpb()` | exec pyp base | `u.xpb("mod:func", arg1)` |
| `u.ipb()` | import pyp base | `u.ipb("module_name")` |
| `u.gjb()` | get json base (read+keydata) | `u.gjb(name="cfg", keydata="user/email")` |

### Key Parameters

```python
data=       # 쓸 데이터 (w/u 필수)
name=       # 파일명 (확장자 자동추가, 미지정=dumps)
keydata=    # 중첩 경로 "user/email", "items[0]/name"
walk=True   # 하위 디렉토리 재귀 검색
default=    # keydata 없을 때 기본값
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

## Constraints

- **emit(e)** → mem(m) 위치만: `u.ejm(data={...})` ✅ / `u.ejb()` ❌
- **delete 패턴 안전장치** → `u.djb(name="*")` 차단됨
- **name 미지정** → dumps(가상메모리), 파일 생성 안 됨
- **SQL row** → `row.col` 속성 접근, `row._fields` 컬럼명 리스트
- **loc=p** → `pre`(pre-defined path), path가 아님
- **모바일 환경** → Termux + Samsung Browser, 출력 간결하게
