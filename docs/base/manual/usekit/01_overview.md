# USEKIT Overview

USEKIT — Memory-Oriented Software Architecture (MOSA).
`use` / `u` 가 정규화된 문법 기준이며 나머지는 모두 지원 도구다.

---

## Import

```python
from usekit import u     # 3-letter shorthand (REPL, scripts)
from usekit import use   # full-chain (readable code)
from usekit import s     # safe mode — 실패 시 None 반환

from usekit import uw    # watch/output
from usekit import ut    # time
from usekit import ud    # database (SQLite3)
```

---

## Core Rules

1. **Use USEKIT APIs first.** `open()`, `os.path`, `pathlib` 직접 사용 금지.
2. **No hardcoded absolute paths.** 모든 경로는 `ENV_BASE_PATH` 기준 상대경로.
3. **No `sys.path.append`.** `u.ipb("module")` 또는 `u.xpb("mod:func")` 사용.
4. **Do not rewrite project structure** unless explicitly requested.

---

## 두 가지 스타일

같은 동작, 두 가지 표현:

```python
u.rjb("config")                   # 3-letter shorthand
use.read.json.base("config")       # full-chain (동일)
```

REPL / 스크립트 → `u.*`  
가독성이 중요한 코드 → `use.*`

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
