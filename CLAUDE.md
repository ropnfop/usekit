# CLAUDE.md

This is a **USEKIT project** — Memory-Oriented Software Architecture (MOSA).

> 세션 히스토리 및 미완 과제 → `docs/base/SESSIONS.md`

---

## Manual

```
docs/base/manual/
  usekit/
    01_overview.md    — MOSA 개요, 핵심 규칙, 디렉토리 구조
    02_routing.md     — 3-letter 라우팅 (ACTION / FORMAT / LOCATION)
    03_io.md          — 데이터 I/O 패턴 (params, keydata, append, dir_path)
    04_exec.md        — EXEC 레이어 (xpb, ipb, wpb, SQL)
    05_navi.md        — NAVI 레이어 (path, find, list, get, set)
  support/
    uw.md             — Watch/Output (p, ok, warn, err, history)
    ut.md             — Time (now, str, stamp, sleep)
    ud.md             — Database SQLite3 (conn, exec, fetch, tx)
    s.md              — Safe layer (실패 시 None 반환)
```

---

## Quick Reference

```python
from usekit import u     # 3-letter shorthand
from usekit import use   # full-chain
from usekit import s     # safe mode

from usekit import uw    # watch/output
from usekit import ut    # time
from usekit import ud    # database (SQLite3)
```

```python
u.rjb("config")                    # read json base
u.wjb({"k": "v"}, "out")          # write json base
u.xsb("SELECT * FROM users")      # exec sql base → namedtuple rows
u.xdb("CREATE TABLE ...")          # exec ddl base
u.xpb("mod:func", arg)            # exec pyp base
u.ipb("module")                    # import pyp base
u.ejm({"k": "v"})                 # emit json mem → str
```

---

## Core Rules

1. **Use USEKIT APIs first.** `open()`, `os.path`, `pathlib` 직접 사용 금지.
2. **No hardcoded absolute paths.** 모든 경로는 `ENV_BASE_PATH` 기준.
3. **No `sys.path.append`.** `u.ipb()` 또는 `u.xpb()` 사용.
4. **Do not rewrite project structure** unless explicitly requested.

---

## 3-Letter Routing

```
u.[ACTION][FORMAT][LOCATION]()
```

| 분류 | ACTION | FORMAT | LOCATION |
|------|--------|--------|----------|
| 코드 | r w u d h e / p f l g s / x i b c | j y c t m s d p k a | b s t d n c |
| 전체 | read write update delete has emit / path find list get set / exec imp boot close | json yaml csv txt md sql ddl pyp km any | base sub tmp dir now cache |

> `m`(mem) — emit 전용 / `cus=` — custom preset / `loc=p` — pre-defined path

---

## 자주 쓰는 패턴

| 패턴 | 의미 |
|------|------|
| `u.rjb("name")` | read json base |
| `u.wjb(data, "name")` | write json base |
| `u.hjb("name")` | has json base |
| `u.ljb()` | list json base |
| `u.wtb(text, "name")` | write txt base |
| `u.wmb(md, "name")` | write md base |
| `u.xsb("SELECT ...")` | exec sql → rows |
| `u.xdb("CREATE TABLE ...")` | exec ddl |
| `u.xpb("mod:func", *args)` | exec python |
| `u.ejm(data)` | emit → str |
| `u.sjb(val, "key")` | set (캐시/경로 저장) |
| `u.gjb("key")` | get (캐시/경로 조회) |

---

## Key Parameters

```python
name=           # 파일명 (확장자 자동추가)
data=           # 쓸 데이터
keydata=        # 중첩 경로: "user/email", "items[0]/name"
dir_path=       # loc 기준 서브 경로 (두 번째 positional)
walk=True       # 하위 디렉토리 재귀
append=True     # 기존 파일에 추가
append_mode=    # "jsonl" | "array" | "object"
jsonl=True      # JSONL 형식으로 읽기
default=        # keydata 없을 때 기본값
```

---

## Support 요약

```python
# uw
uw.p(v) / uw.ok("") / uw.warn("") / uw.err("") / uw.info("")
uw.history()   # 출력 기록 반환
uw.clear()

# ut
ut.now() / ut.str() / ut.stamp() / ut.sleep(s) / ut.sleep_ms(ms)

# ud (SQLite3 직접 제어)
ud.conn("path/to/db")
ud.exec("SQL", *params, commit=False)
ud.fetch("SELECT ...") / ud.one("SELECT ...")   # row.col 속성 접근
ud.commit() / ud.rollback()
with ud.tx("path"):  ...                        # 트랜잭션
ud.insert(table, data) / ud.update(...) / ud.delete(...) / ud.select(...)
ud.tables() / ud.cols(t) / ud.has(t) / ud.count(t)

# s (safe)
s.rjb("name")   # 없으면 None
s.djb("name")   # 없어도 무시
```

---

## Constraints

- `u.ejm()` — emit은 `mem` 전용. 반환값 `str`.
- `u.djb(name="*")` — 와일드카드 삭제 차단.
- `name` 미지정 → dumps 모드 (파일 생성 안 됨).
- SQL row → `row.col` 속성 접근, `row._fields` 컬럼명.
- 모바일 환경 → Termux + Samsung Browser, 출력 간결하게.
