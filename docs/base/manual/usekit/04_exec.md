# EXEC Layer

Dynamically resolves and runs modules **by location (loc) without touching `sys.path`**.

```
u.[ACTION]pb("[dotted.path]:[func]", *args)
              ↑                ↑
         relative to src/base/     function to call
         dot (.) is directory separator
```

---

## Standard Python vs USEKIT

```python
# Standard Python
import sys
sys.path.append("/some/path/src/base")
from a.b.c import func
func(1, 2)

# USEKIT
u.xpb("a.b.c:func", 1, 2)   # run → return result
u.ipb("a.b.c")               # import → return module object
```

---

## Path Rules

```
src/base/
  calc.py              → "calc:func"
  test/
    test.py            → "test.test:func"
    utils/
      math.py          → "test.utils.math:func"
```

---

## API

```python
# xpb — run function, return result
result = u.xpb("calc:add", 10, 20)               # → 30
result = u.xpb("test.test:add", 10, 20)          # → 30
result = u.xpb("demo:report", "Alice", 95)
result = u.xpb("demo:report", "Bob", grade="B")  # kwargs supported

# ipb — return module object
calc = u.ipb("calc")    # → <module>
calc.add(3, 4)          # → 7

# wpb — write source → saves to src/base/{name}.py
u.wpb("def add(a,b): return a+b", "calc")        # creates src/base/calc.py

# imp.pyp.sub — inject sub module functions into current namespace
use.imp.pyp.sub("utils : upper, repeat")
use.imp.pyp.sub("score_parts.db : reset, insert, fetch_all")
```

---

## Two Execution Modes

```python
# script mode — runs if __name__ == "__main__" block, no return value
u.xpb("main")

# function mode — runs specified function, returns value
result = u.xpb("main:main")
result = u.xpb("calc:add", 3, 7)   # → 10
```

| Form | Target | Return value |
|------|--------|--------------|
| `u.xpb("mod")` | `__main__` block | none |
| `u.xpb("mod:func", *args)` | specified function | function return value |

---

## base / sub Split Structure

`base` — entry point / `sub` — feature modules

```
src/base/
  score_app.py       ← entry point

src/sub/
  score_parts/
    db.py
    report.py
```

```python
# score_app.py
from usekit import use

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
# run
u.xpb("score_app")
```

---

## Write-then-Run Pattern

Core AI coding workflow — write and run in one flow.

```python
# 1. write source → saves to src/base/test.py
u.wpb(r'''
def main():
    print("dynamic script")
    return 42

if __name__ == "__main__":
    main()
''', "test")

# 2. run immediately
u.xpb("test")         # script mode
u.xpb("test:main")    # function mode → 42
```

---

## Output Storage Pattern

Save execution results to JSON / TXT / MD — with timestamps via `ut`.

```python
from usekit import u, ut

# JSON accumulation (JSONL)
u.wjb({"ts": ut.str(), "result": result}, "output_log", append=True, append_mode="jsonl")

# TXT log accumulation
u.wtb(f"[{ut.str()}] {message}", "run_log", append=True)

# MD report
u.wmb(f"# Report\n\nGenerated: {ut.str()}\n\n...", "report")
```

Storage paths:
- `u.wjb()` → `data/json/base/`
- `u.wtb()` → `data/common/txt/`
- `u.wmb()` → `docs/base/`

---

## SQL / DDL

```python
# DDL — create table
u.xdb("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")

# DML/Query — returns namedtuple rows (attribute access)
rows = u.xsb("SELECT * FROM users WHERE age > 20")
for row in rows:
    print(row.id, row.name)
    print(row._fields)    # column name list

# run SQL file (relative to data/table/sql/)
rows = u.xsb("users_list", id=10)
```
