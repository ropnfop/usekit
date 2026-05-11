"""
ud 샘플 — 간단한 메모 앱
ud를 직접 사용해 메모를 저장·조회·수정·삭제하는 흐름을 보여줍니다.
"""
import os
from usekit import ud, uw

DB = "/tmp/memo.db"
if os.path.exists(DB):
    os.remove(DB)

# ── 연결 & 테이블 생성 ───────────────────────────────
ud.conn(DB)
ud.script("""
    CREATE TABLE IF NOT EXISTS memo (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        title   TEXT    NOT NULL,
        body    TEXT,
        pinned  INTEGER DEFAULT 0
    );
""")
uw.ok("연결 & 테이블 준비")

# ── 입력 ────────────────────────────────────────────
notes = [
    {"title": "장보기",    "body": "우유, 계란, 빵",   "pinned": 1},
    {"title": "독서 메모", "body": "클린 코드 3장",    "pinned": 0},
    {"title": "할 일",     "body": "PR 리뷰, 테스트",  "pinned": 1},
    {"title": "아이디어",  "body": "새 프로젝트 구상", "pinned": 0},
]
for n in notes:
    ud.insert("memo", n)
ud.commit()
uw.ok(f"{len(notes)}개 메모 저장 완료")

# ── 전체 조회 (pinned 우선) ──────────────────────────
uw.p("\n── 전체 메모 (pinned 우선) ──")
rows = ud.fetch("SELECT * FROM memo ORDER BY pinned DESC, id")
for r in rows:
    pin = "📌" if r.pinned else "  "
    uw.p(f"  {pin} [{r.id}] {r.title} — {r.body}")

# ── 단건 조회 ────────────────────────────────────────
uw.p("\n── 단건 조회 ──")
row = ud.one("SELECT * FROM memo WHERE title = ?", "독서 메모")
if row:
    uw.ok(f"찾음: id={row.id}, body={row.body}")

# ── 수정 (tx 사용) ────────────────────────────────────
uw.p("\n── 수정 (tx) ──")
with ud.tx():
    ud.update("memo", {"body": "클린 코드 3~5장"}, "title = ?", ("독서 메모",))
    ud.update("memo", {"pinned": 0},               "title = ?", ("장보기",))

updated = ud.one("SELECT * FROM memo WHERE title = ?", "독서 메모")
uw.ok(f"수정 후: {updated.body}")

# ── 삭제 ─────────────────────────────────────────────
uw.p("\n── 삭제 ──")
cnt = ud.delete("memo", "pinned = ?", (0,))
ud.commit()
uw.ok(f"pinned=0 메모 {cnt}건 삭제  남은 수={ud.count('memo')}")

# ── 최종 목록 ────────────────────────────────────────
uw.p("\n── 최종 메모 ──")
for r in ud.select("memo", order="id"):
    uw.p(f"  [{r.id}] {r.title} — {r.body}")

# ── 유틸 & 종료 ──────────────────────────────────────
uw.p(f"\n  cols: {ud.cols('memo')}")
uw.p(f"  count: {ud.count('memo')}")
ud.vacuum()
ud.close()
uw.ok("완료")
