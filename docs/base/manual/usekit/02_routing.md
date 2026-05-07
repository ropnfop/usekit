# 3-Letter Routing

```
u.[ACTION][FORMAT][LOCATION]()
```

---

## ACTION (15)

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

## FORMAT (10)

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

## LOCATION (7)

| 분류 | 코드 | 전체 이름 |
|------|------|-----------|
| **기본** | `b` | base |
| | `s` | sub |
| | `t` | tmp |
| | `d` | dir |
| **기타** | `n` | now |
| | `c` | cache |
| | — | cus (custom preset, `cus=` 파라미터로 지정) |

> `m` (mem) 은 `u.ejm()` emit 전용 — 일반 loc 아님  
> `loc=p` → `pre`(pre-defined path), path가 아님

---

## 자주 쓰는 패턴

| 패턴 | 의미 | 예시 |
|------|------|------|
| `u.rjb()` | read json base | `u.rjb("config")` |
| `u.wjb()` | write json base | `u.wjb({"k":"v"}, "out")` |
| `u.hjb()` | has json base | `if u.hjb("config"): ...` |
| `u.ljb()` | list json base | `files = u.ljb()` |
| `u.fjb()` | find json base | `u.fjb("user_*")` |
| `u.pjb()` | path json base | `u.pjb()` → 디렉토리 경로 |
| `u.wtb()` | write txt base | `u.wtb(report, "log")` |
| `u.wmb()` | write md base | `u.wmb(md_text, "doc")` |
| `u.xsb()` | exec sql base | `rows = u.xsb("SELECT ...")` |
| `u.xdb()` | exec ddl base | `u.xdb("CREATE TABLE ...")` |
| `u.xpb()` | exec pyp base | `u.xpb("mod:func", arg1)` |
| `u.ipb()` | import pyp base | `u.ipb("module_name")` |
| `u.ejm()` | emit json mem | `u.ejm({"k": "v"})` |
| `u.sjb()` | set json base | `u.sjb("data/dev", "env_path")` |
| `u.gjb()` | get json base | `u.gjb("env_path")` |
