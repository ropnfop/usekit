# USEKIT Overview

USEKIT — Memory-Oriented Software Architecture (MOSA).
`use` / `u` are the canonical API interface; everything else is a support tool.

---

## Import

```python
from usekit import u     # 3-letter shorthand (REPL, scripts)
from usekit import use   # full-chain (readable code)
from usekit import s     # safe mode — returns None on failure

from usekit import uw    # watch/output
from usekit import ut    # time
from usekit import ud    # database (SQLite3)
```

---

## Core Rules

1. **Use USEKIT APIs first.** Do not use `open()`, `os.path`, or `pathlib` directly.
2. **No hardcoded absolute paths.** All paths are relative to `ENV_BASE_PATH`.
3. **No `sys.path.append`.** Use `u.ipb("module")` or `u.xpb("mod:func")`.
4. **Do not rewrite project structure** unless explicitly requested.

---

## Two Styles

Same operation, two expressions:

```python
u.rjb("config")                   # 3-letter shorthand
use.read.json.base("config")       # full-chain (identical)
```

REPL / scripts → `u.*`  
Readable code → `use.*`

---

## Help System

```python
use.help("overview")    # MOSA architecture overview
use.help("quick")       # quick start guide
use.help("action")      # action list
use.help("object")      # format list
use.help("location")    # location list
use.help("examples")    # usage examples
use.help("keydata")     # nested path access
use.help("walk")        # recursive search
use.help("alias")       # parameter aliases
use.help("pattern")     # pattern matching

help(u.rjb)             # individual method help
```

---

## Parameter Reference

Parameters are defined in `usekit/infra/` across 3 layers:

| File | Target | Role |
|------|--------|------|
| `infra/io_signature.py` | DATA / NAVI | I/O parameter definitions |
| `infra/exec_signature.py` | EXEC | execution parameter definitions |
| `infra/io_signature_doc.py` | common | parameter docs + examples |

```
USER LAYER      — intent: data, name, dir_path, keydata, loc, cus
TARGETING LAYER — target selection: walk, append, append_mode, regex etc.
SYSTEM LAYER    — execution control: fmt, mode, encoding, debug etc.
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
