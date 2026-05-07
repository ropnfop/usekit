# ud — Database (SQLite3)

`use` / `u` 와 별개인 **SQLite3 저수준 직접 제어 도구**.  
연결·실행·페치·종료를 개별적으로 처리한다.

```python
from usekit import ud
```

---

## 연결 / 종료

```python
ud.conn("data/table/db/base.db")   # 연결 (디렉토리 자동 생성)
                                    # 기존 연결이 있으면 자동 close 후 재연결
ud.close()                          # 연결 종료
ud.is_open()                        # bool
```

---

## 실행 (exec)

DML / DDL 실행. params는 positional, tuple, dict 모두 지원.

```python
ud.exec("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, name TEXT)")

ud.exec("INSERT INTO t VALUES (?, ?)", 1, "Alice")           # positional
ud.exec("INSERT INTO t VALUES (?, ?)", (1, "Alice"))          # tuple
ud.exec("UPDATE t SET name=:n WHERE id=:id", {"n": "B", "id": 1})  # dict

ud.exec("DELETE FROM t WHERE id = ?", 1, commit=True)        # 즉시 commit
```

---

## 조회 (fetch / one)

rows는 namedtuple — `row.col` 속성 접근.

```python
rows = ud.fetch("SELECT * FROM t WHERE age > ?", 20)
for row in rows:
    print(row.id, row.name)
    print(row._fields)    # 컬럼명 리스트

row = ud.one("SELECT * FROM t WHERE id = ?", 1)
if row:
    print(row.name)       # None-safe

# 결과 없으면: fetch → [], one → None
```

---

## 배치 / 스크립트

```python
ud.many("INSERT INTO t VALUES (?, ?)", [(1, "A"), (2, "B")], commit=True)
ud.script("CREATE TABLE a (x INT); CREATE TABLE b (y TEXT);")
```

---

## 트랜잭션

```python
ud.commit()
ud.rollback()

# tx context — 성공 시 commit, 예외 시 rollback
with ud.tx("data/table/db/base.db"):    # path 지정 → 열기 + 닫기 포함
    ud.exec("INSERT INTO t VALUES (?, ?)", 3, "Charlie")

ud.conn("data/table/db/base.db")
with ud.tx():                            # path 없음 → 기존 연결 재사용
    ud.exec("UPDATE t SET name = ? WHERE id = ?", "Dave", 1)
ud.close()
```

---

## CRUD 헬퍼

```python
ud.insert("t", {"id": 4, "name": "Eve"})                      # → lastrowid
ud.update("t", {"name": "Frank"}, "id = ?", (4,))             # → rowcount
ud.delete("t", "id = ?", (4,))                                 # → rowcount
ud.select("t", where="id > ?", params=(0,), order="name", limit=10)
```

---

## 유틸

```python
ud.tables()       # → ["t", "users", ...]
ud.cols("t")      # → ["id", "name"]
ud.has("t")       # → True / False
ud.count("t")     # → 42
ud.vacuum()       # 디스크 최적화
```

---

## ud vs u.xsb

| | `ud.*` | `u.xsb()` |
|---|---|---|
| 연결 관리 | 수동 (`conn` / `close`) | 자동 |
| DB 경로 | 직접 지정 | `data/table/db/base.db` 자동 |
| SQL 입력 | 인라인 raw SQL | 인라인 + 파일(`data/table/sql/`) |
| 반환 행 | namedtuple (속성 접근) | DotDict (속성 접근) |
| 용도 | 저수준 직접 제어 | USEKIT 경로체계 통합 |
