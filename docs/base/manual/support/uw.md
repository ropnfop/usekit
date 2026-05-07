# uw — Watch / Output

출력 및 로그 유틸리티. 타입 무관하게 출력하고, 기록을 내부에 보관한다.

```python
from usekit import uw
```

---

## 출력 메서드

```python
uw.p(value)           # 일반 출력 (타입 무관)
uw.info("msg")        # [INFO] msg
uw.warn("msg")        # [WARN] msg
uw.err("msg")         # [ERR]  msg
uw.ok("msg")          # [OK]   msg
uw.tag("msg", "TAG")  # [TAG]  msg
uw.here()             # 현재 호출 위치 출력 (디버그용)
```

---

## 기록 관리

```python
uw.history()    # 지금까지 출력한 내용 전체 반환 (list)
uw.clear()      # 기록 초기화
```

> `uw.p()`, `uw.ok()`, `uw.info()`, `uw.warn()`, `uw.err()` 모두 `history()`에 기록됨.

---

## 예시

```python
uw.ok("처리 완료")
uw.warn("파일 없음, 기본값 사용")
uw.err("DB 연결 실패")
uw.info(f"처리 건수: {len(rows)}")

log = uw.history()   # → [("[OK] 처리 완료", ...), ...]
uw.clear()
```
