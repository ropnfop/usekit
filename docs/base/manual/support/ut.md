# ut — Time

Time utilities.

```python
from usekit import ut
```

---

## API

```python
ut.now()                          # datetime object (current time)
ut.str()                          # "2026-01-01 12:00:00" (current time as string)
ut.str(dt, fmt="%Y%m%d")         # datetime → formatted string
ut.stamp()                        # Unix timestamp (int)
ut.diff(dt1, dt2)                 # timedelta
ut.sleep(1.5)                     # wait in seconds
ut.sleep_ms(500)                  # wait in milliseconds
```

---

## Example

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

## Log Timestamp Pattern

```python
from usekit import u, ut

u.wjb({"ts": ut.str(), "event": "start"}, "run_log", append=True, append_mode="jsonl")
u.wtb(f"[{ut.str()}] done", "log", append=True)
```
