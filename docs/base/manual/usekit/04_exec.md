# EXEC Layer

`sys.path` 조작 없이 **위치(loc) 기준으로 모듈을 동적 탐색·실행**.

```
u.[ACTION]pb("[dotted.path]:[func]", *args)
              ↑                ↑
         src/base/ 기준     실행할 함수명
         점(.)은 디렉토리 구분자
```

---

## 일반 Python vs USEKIT

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

---

## 경로 규칙

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
# xpb — 함수 실행, 결과 반환
result = u.xpb("calc:add", 10, 20)               # → 30
result = u.xpb("test.test:add", 10, 20)          # → 30
result = u.xpb("demo:report", "Alice", 95)
result = u.xpb("demo:report", "Bob", grade="B")  # kwargs 지원

# ipb — 모듈 객체 반환
calc = u.ipb("calc")    # → <module>
calc.add(3, 4)          # → 7

# imp.pyp.sub — sub 모듈 함수를 현재 네임스페이스로 주입
use.imp.pyp.sub("utils : upper, repeat")
use.imp.pyp.sub("score_parts.db : reset, insert, fetch_all")
```

---

## 두 가지 실행 모드

```python
# 스크립트 모드 — if __name__ == "__main__" 블록 실행, 반환값 없음
u.xpb("main")

# 함수 모드 — 지정 함수 실행, 반환값 있음
result = u.xpb("main:main")
result = u.xpb("calc:add", 3, 7)   # → 10
```

| 형태 | 실행 대상 | 반환값 |
|------|-----------|--------|
| `u.xpb("mod")` | `__main__` 블록 | 없음 |
| `u.xpb("mod:func", *args)` | 지정 함수 | 함수 반환값 |

---

## base / sub 분리 구조

`base` — 진입점 / `sub` — 기능 모듈

```
src/base/
  score_app.py       ← 진입점

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
# 실행
u.xpb("score_app")
```

---

## 작성 후 즉시 실행 패턴

AI 코딩 워크플로우의 핵심 — 코드 작성과 실행을 한 흐름으로.

```python
# 1. 소스 작성 → src/base/test.py 로 저장
u.wpb(r'''
def main():
    print("동적 스크립트")
    return 42

if __name__ == "__main__":
    main()
''', "test")

# 2. 즉시 실행
u.xpb("test")         # 스크립트 모드
u.xpb("test:main")    # 함수 모드 → 42
```

---

## SQL / DDL

```python
# DDL — 테이블 생성
u.xdb("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")

# DML/Query — namedtuple 행 반환 (속성 접근)
rows = u.xsb("SELECT * FROM users WHERE age > 20")
for row in rows:
    print(row.id, row.name)
    print(row._fields)    # 컬럼명 리스트

# SQL 파일 실행 (data/table/sql/ 기준)
rows = u.xsb("users_list", id=10)
```
