# 3-Letter Routing

```
u.[ACTION][FORMAT][LOCATION]()
```

---

## ACTION (15)

| Category | Code | Full Name |
|----------|------|-----------|
| **Data** | `r` | read |
| | `w` | write |
| | `u` | update |
| | `d` | delete |
| | `h` | has |
| | `e` | emit |
| **Navi** | `p` | path |
| | `f` | find |
| | `l` | list |
| | `g` | get |
| | `s` | set |
| **Exec** | `x` | exec |
| | `i` | imp (import) |
| | `b` | boot |
| | `c` | close |

## FORMAT (10)

| Category | Code | Full Name |
|----------|------|-----------|
| **General** | `j` | json |
| | `y` | yaml |
| | `c` | csv |
| | `t` | txt |
| | `m` | md |
| | `s` | sql |
| | `d` | ddl |
| | `p` | pyp |
| **Other** | `k` | km (keymemory) |
| | `a` | any |

## LOCATION (8)

| Category | Code | Full Name |
|----------|------|-----------|
| **Base** | `b` | base |
| | `s` | sub |
| | `t` | tmp |
| | `d` | dir |
| **Other** | `n` | now |
| | `c` | cache |
| | `m` | mem (process memory, no file) |
| | — | cus (custom preset, specified via `cus=` param) |

> `m` (mem) — supports all DATA·NAVI actions r/w/u/d/h/l. No file I/O.  
> `e` (emit) is also mem-only but for serialization only (returns str).  
> `loc=p` → `pre` (pre-defined path), not "path"

---

## Common Patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| `u.rjb()` | read json base | `u.rjb("config")` |
| `u.wjb()` | write json base | `u.wjb({"k":"v"}, "out")` |
| `u.hjb()` | has json base | `if u.hjb("config"): ...` |
| `u.ljb()` | list json base | `files = u.ljb()` |
| `u.fjb()` | find json base | `u.fjb("user_*")` |
| `u.pjb()` | path json base | `u.pjb()` → directory path |
| `u.wtb()` | write txt base | `u.wtb(report, "log")` |
| `u.wmb()` | write md base | `u.wmb(md_text, "doc")` |
| `u.xsb()` | exec sql base | `rows = u.xsb("SELECT ...")` |
| `u.xdb()` | exec ddl base | `u.xdb("CREATE TABLE ...")` |
| `u.xpb()` | exec pyp base | `u.xpb("mod:func", arg1)` |
| `u.ipb()` | import pyp base | `u.ipb("module_name")` |
| `u.ejm()` | emit json mem | `u.ejm({"k": "v"})` → str |
| `u.wjm()` | write json mem | `u.wjm(data, "key")` |
| `u.rjm()` | read json mem | `u.rjm("key")` |
| `u.ujm()` | update json mem | `u.ujm({"b": 99}, "key")` (dict merge) |
| `u.djm()` | delete json mem | `u.djm("key")` |
| `u.hjm()` | has json mem | `u.hjm("key")` → bool |
| `u.ljm()` | list json mem | `u.ljm()` → all keys |
| `u.sjb()` | set json base | `u.sjb("data/dev", "env_path")` |
| `u.gjb()` | get json base | `u.gjb("env_path")` |
