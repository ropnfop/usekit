"""
ud 실습 — SQLite3 직접 제어
단계별로 모든 주요 API를 순서대로 사용합니다.
"""
import os
from usekit import ud, uw

DB = "/tmp/ud_practice.db"
if os.path.exists(DB):
    os.remove(DB)

uw.p("=" * 48)
uw.p("  ud 실습 시작")
uw.p("=" * 48)

# ── 1. 연결 ──────────────────────────────────────
uw.p("\n[1] 연결")
ud.conn(DB)
uw.ok(f"연결 완료 → {DB}")
uw.p(f"  is_open: {ud.is_open()}")

# ── 2. DDL — 테이블 생성 ─────────────────────────
uw.p("\n[2] 테이블 생성 (DDL)")
ud.exec("""
    CREATE TABLE IF NOT EXISTS users (
        id   INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT    NOT NULL,
        age  INTEGER
    )
""")
ud.exec("""
    CREATE TABLE IF NOT EXISTS orders (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        item    TEXT,
        price   REAL
    )
""")
ud.commit()
uw.ok("users / orders 테이블 생성")
uw.p(f"  tables: {ud.tables()}")

# ── 3. INSERT — 단건 ─────────────────────────────
uw.p("\n[3] 단건 INSERT")
ud.exec("INSERT INTO users (name, age) VALUES (?, ?)", "Alice", 30)
ud.exec("INSERT INTO users (name, age) VALUES (?, ?)", "Bob",   25)
ud.exec("INSERT INTO users (name, age) VALUES (?, ?)", "Carol", 35, commit=True)
uw.ok(f"3건 삽입 완료  count={ud.count('users')}")

# ── 4. many — 배치 삽입 ──────────────────────────
uw.p("\n[4] 배치 INSERT (many)")
batch = [
    ("Laptop",  999.99),
    ("Mouse",    19.99),
    ("Keyboard", 49.99),
]
ud.many("INSERT INTO orders (user_id, item, price) VALUES (1, ?, ?)", batch, commit=True)
uw.ok(f"배치 3건 삽입  count={ud.count('orders')}")

# ── 5. fetch — 여러 행 조회 ───────────────────────
uw.p("\n[5] fetch — 전체 조회")
rows = ud.fetch("SELECT * FROM users ORDER BY id")
for row in rows:
    uw.p(f"  id={row.id}  name={row.name}  age={row.age}")
uw.p(f"  _fields: {rows[0]._fields if rows else '-'}")

# ── 6. one — 단건 조회 ───────────────────────────
uw.p("\n[6] one — 단건 조회")
row = ud.one("SELECT * FROM users WHERE name = ?", "Bob")
if row:
    uw.ok(f"Bob 조회 성공: id={row.id}, age={row.age}")

missing = ud.one("SELECT * FROM users WHERE name = ?", "Zara")
uw.p(f"  없는 사용자 결과: {missing}")

# ── 7. CRUD 헬퍼 ─────────────────────────────────
uw.p("\n[7] CRUD 헬퍼")

lid = ud.insert("users", {"name": "Dave", "age": 28})
uw.ok(f"insert → lastrowid={lid}")

cnt = ud.update("users", {"age": 31}, "name = ?", ("Alice",))
uw.ok(f"update → rowcount={cnt}")

rows = ud.select("users", order="age", limit=10)
uw.p("  select (age 순):")
for r in rows:
    uw.p(f"    {r.id} {r.name} {r.age}")

cnt = ud.delete("users", "name = ?", ("Dave",))
uw.ok(f"delete → rowcount={cnt}")

# ── 8. 트랜잭션 (tx context) ─────────────────────
uw.p("\n[8] 트랜잭션 (tx context)")
try:
    with ud.tx():
        ud.exec("INSERT INTO orders (user_id, item, price) VALUES (?, ?, ?)", 2, "Monitor", 299.99)
        ud.exec("INSERT INTO orders (user_id, item, price) VALUES (?, ?, ?)", 2, "Webcam",   59.99)
    uw.ok(f"tx 성공  orders count={ud.count('orders')}")
except Exception as e:
    uw.err(f"tx 실패: {e}")

# rollback 시나리오
uw.p("\n  [rollback 시나리오]")
try:
    with ud.tx():
        ud.exec("INSERT INTO orders (user_id, item, price) VALUES (?, ?, ?)", 3, "Ghost", 0)
        raise ValueError("의도적 오류 → rollback")
except ValueError as e:
    uw.warn(f"예외 → rollback 처리됨: {e}")
uw.p(f"  rollback 후 orders count={ud.count('orders')}")

# ── 9. 유틸 ─────────────────────────────────────
uw.p("\n[9] 유틸")
uw.p(f"  tables : {ud.tables()}")
uw.p(f"  cols(users)  : {ud.cols('users')}")
uw.p(f"  cols(orders) : {ud.cols('orders')}")
uw.p(f"  has('users') : {ud.has('users')}")
uw.p(f"  has('ghost') : {ud.has('ghost')}")
uw.p(f"  count(users) : {ud.count('users')}")
uw.p(f"  count(orders): {ud.count('orders')}")

# ── 10. 종료 ─────────────────────────────────────
uw.p("\n[10] 연결 종료")
ud.close()
uw.p(f"  is_open: {ud.is_open()}")

uw.p("\n" + "=" * 48)
uw.ok("ud 실습 완료")
uw.p("=" * 48)
