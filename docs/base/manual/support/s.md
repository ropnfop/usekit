# s — Safe Layer

`u.*` raises exceptions on failure.  
`s.*` silently handles failure — returns `None` or ignores the error.

Use for cleanup, optional operations, or files that may not exist.

```python
from usekit import s
# or
from usekit import safe
```

---

## Example

```python
s.rjb("config")      # returns None if file not found (no exception)
s.djb("temp")        # no crash if file not found
```

---

## u vs s

| | `u.*` | `s.*` |
|---|---|---|
| On failure | raises exception | None / ignored |
| Use case | general logic | cleanup, optional I/O |

---

## Patterns

```python
# when config file may not exist
cfg = s.rjb("config") or {}

# cleanup temp files (safe if missing)
s.djb("run_tmp")
s.djb("lock")
```
