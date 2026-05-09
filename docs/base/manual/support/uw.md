# uw — Watch / Output

Output and logging utility. Prints any value and stores output history internally.

```python
from usekit import uw
```

---

## Output Methods

```python
uw.p(value)           # general output (any type)
uw.info("msg")        # [INFO] msg
uw.warn("msg")        # [WARN] msg
uw.err("msg")         # [ERR]  msg
uw.ok("msg")          # [OK]   msg
uw.tag("msg", "TAG")  # [TAG]  msg
uw.here()             # print current call location (debug)
```

---

## History

```python
uw.history()    # return all output recorded so far (list)
uw.clear()      # clear history
```

> All of `uw.p()`, `uw.ok()`, `uw.info()`, `uw.warn()`, `uw.err()` are recorded in `history()`.

---

## Example

```python
uw.ok("done")
uw.warn("file not found, using default")
uw.err("DB connection failed")
uw.info(f"processed: {len(rows)}")

log = uw.history()   # → [("[OK] done", ...), ...]
uw.clear()
```
