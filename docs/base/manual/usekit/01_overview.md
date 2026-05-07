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

## Help System

```python
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

help(u.rjb)             # 개별 메서드 도움말
```

---

## 파라미터 정의서

전체 파라미터는 `usekit/infra/` 에 3레이어로 정의:

| 파일 | 대상 | 역할 |
|------|------|------|
| `infra/io_signature.py` | DATA / NAVI | I/O 파라미터 정의 |
| `infra/exec_signature.py` | EXEC | 실행 파라미터 정의 |
| `infra/io_signature_doc.py` | 공통 | 파라미터 문서 + 예제 |

```
USER LAYER      — 의도 표현: data, name, dir_path, keydata, loc, cus
TARGETING LAYER — 대상 선택: walk, append, append_mode, regex 등
SYSTEM LAYER    — 실행 제어: fmt, mode, encoding, debug 등
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
