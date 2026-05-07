# ut — Time

시간 관련 유틸리티.

```python
from usekit import ut
```

---

## API

```python
ut.now()                          # datetime 객체 (현재 시각)
ut.str()                          # "2026-01-01 12:00:00" (현재 시각 문자열)
ut.str(dt, fmt="%Y%m%d")         # datetime → 포맷 지정 문자열
ut.stamp()                        # Unix timestamp (int)
ut.diff(dt1, dt2)                 # timedelta
ut.sleep(1.5)                     # 초 단위 대기
ut.sleep_ms(500)                  # 밀리초 단위 대기
```

---

## 예시

```python
now = ut.now()                    # datetime(2026, 5, 7, 12, 0, 0)
ts  = ut.str()                    # "2026-05-07 12:00:00"
ym  = ut.str(fmt="%Y%m")         # "202605"
day = ut.str(fmt="%Y-%m-%d")     # "2026-05-07"

stamp = ut.stamp()                # 1746604800

elapsed = ut.diff(start, ut.now())
ut.sleep(0.5)
```

---

## 로그 타임스탬프 패턴

```python
from usekit import u, ut

u.wjb({"ts": ut.str(), "event": "start"}, "run_log", append=True, append_mode="jsonl")
u.wtb(f"[{ut.str()}] 완료", "log", append=True)
```
