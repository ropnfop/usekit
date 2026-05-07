# s — Safe Layer

`u.*` 는 실패 시 예외 발생.  
`s.*` 는 실패 시 조용히 넘어감 — `None` 반환 또는 무시.

cleanup, optional 작업, 존재 여부 불확실한 파일 처리에 사용.

```python
from usekit import s
# 또는
from usekit import safe
```

---

## 예시

```python
s.rjb("config")      # 파일 없으면 None 반환 (예외 없음)
s.djb("temp")        # 파일 없어도 crash 없음
```

---

## u vs s

| | `u.*` | `s.*` |
|---|---|---|
| 실패 시 | 예외 발생 | None / 무시 |
| 용도 | 일반 로직 | 정리 작업, optional I/O |

---

## 패턴

```python
# 설정 파일이 없을 수도 있을 때
cfg = s.rjb("config") or {}

# 임시 파일 정리 (없어도 무방)
s.djb("run_tmp")
s.djb("lock")
```
