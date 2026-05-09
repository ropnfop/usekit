# NAVI Layer

NAVI is an ACTION category — dedicated to **file search + path/value storage**.

| Code | Name | Role |
|------|------|------|
| `p` | path | return directory path |
| `f` | find | search files → PosixPath list |
| `l` | list | file listing → filename string list |
| `g` | get | retrieve stored path/value |
| `s` | set | store path/value |

---

## p — path (directory path)

```python
u.pjb()                        # absolute path of data/json/base/
u.pjb(dir_path="sub/dir")     # absolute path of data/json/base/sub/dir/
u.ptb()                        # absolute path of data/tmp/
```

> Returns: `PosixPath` — can be converted with `str()` or used with `/` operator  
> First positional argument is interpreted as `name=`. Sub path must be specified with the `dir_path=` keyword.

---

## f — find (pattern search)

Pattern argument required — raises `ValueError` if omitted.

```python
u.fjb("user_*")                      # match user_*.json in data/json/base/
u.fjb("log_*", walk=True)            # recursive search including subdirectories
u.fjb("report_*", dir_path="2026")   # specify sub path
```

> Returns: `List[PosixPath]`

---

## l — list (file listing)

```python
u.ljb()                        # files and directories in data/json/base/
u.ljb(dir_path="sub/dir")     # specify sub path
```

> Returns: `List[str]` — filenames as strings (directories included as `"sub/"`)  
> Sub path must be specified with the `dir_path=` keyword.

---

## g / s — get / set (path/value cache)

Store with `s`(set), retrieve with `g`(get). Primary use: **dynamic path switching** and **cached value storage**.

```python
# store path → dynamic switching
u.sjb("data/prod", "env_path")
u.sjb("data/dev",  "env_path")    # overwrite
env = u.gjb("env_path")           # → "data/dev"

# use retrieved path as dir_path
u.rjb("config", dir_path=env)

# cache-style value storage
u.sjb("session_abc123", "current_session")
u.gjb("current_session")          # → "session_abc123"
```

> Nested data access via `keydata` (`u.rjb("name", keydata="user/email")`) is a DATA action, not NAVI.

---

## f vs l Comparison

| | `u.fjb()` | `u.ljb()` |
|---|---|---|
| Returns | `List[PosixPath]` | `List[str]` |
| Pattern | `u.fjb("user_*")` | none |
| Recursive | `walk=True` supported | — |
| Use case | when you need file paths | when you only need filenames |
