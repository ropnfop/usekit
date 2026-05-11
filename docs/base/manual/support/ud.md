# ud — Database (SQLite3)

Low-level direct SQLite3 control, separate from `use` / `u`.  
Manages connection, execution, fetch, and close individually.

```python
from usekit import ud
```

---

## SQLite Database Policy

usekit follows a simple mobile-first SQLite policy.

For most users, one database file is enough.  
Instead of creating many database files, usekit encourages organizing data
with tables inside the built-in database.

**Default layout:**

- `base.db` — main database
- `sub.db` — optional secondary database for tests, drafts, or separated workflows

**Typical structure:**

```text
base.db
 ├─ memo
 ├─ task_items
 ├─ settings
 ├─ ai_sessions
 ├─ ai_messages
 └─ feedback_logs
```

This matches the common SQLite usage pattern:

- one app or workspace = one database
- features and data types = tables

Keeping database files small in number makes mobile development easier to
inspect, back up, move, and reuse across Termux, Colab, and file managers.

```text
base.db  →  main database for production data
sub.db   →  tests, temporary data, isolated experiments
```

---

## Connect / Close

```python
ud.conn("data/table/db/base.db")   # connect (creates directory if needed)
                                    # existing connection is auto-closed before reconnect
ud.close()                          # close connection
ud.is_open()                        # bool
```

---

## Execute

Runs DML / DDL. Params can be positional, tuple, or dict.

```python
ud.exec("CREATE TABLE IF NOT EXISTS t (id INTEGER PRIMARY KEY, name TEXT)")

ud.exec("INSERT INTO t VALUES (?, ?)", 1, "Alice")           # positional
ud.exec("INSERT INTO t VALUES (?, ?)", (1, "Alice"))          # tuple
ud.exec("UPDATE t SET name=:n WHERE id=:id", {"n": "B", "id": 1})  # dict

ud.exec("DELETE FROM t WHERE id = ?", 1, commit=True)        # commit immediately
```

---

## Query

Rows are namedtuple — access via `row.col` attribute.

```python
rows = ud.fetch("SELECT * FROM t WHERE age > ?", 20)
for row in rows:
    print(row.id, row.name)
    print(row._fields)    # column name list

row = ud.one("SELECT * FROM t WHERE id = ?", 1)
if row:
    print(row.name)       # None-safe

# no results: fetch → [], one → None
```

---

## Batch / Script

```python
ud.many("INSERT INTO t VALUES (?, ?)", [(1, "A"), (2, "B")], commit=True)
ud.script("CREATE TABLE a (x INT); CREATE TABLE b (y TEXT);")
```

---

## Transaction

```python
ud.commit()
ud.rollback()

# tx context — commits on success, rolls back on exception
with ud.tx("data/table/db/base.db"):    # with path → opens and closes connection
    ud.exec("INSERT INTO t VALUES (?, ?)", 3, "Charlie")

ud.conn("data/table/db/base.db")
with ud.tx():                            # no path → reuses existing connection
    ud.exec("UPDATE t SET name = ? WHERE id = ?", "Dave", 1)
ud.close()
```

---

## CRUD Helpers

```python
ud.insert("t", {"id": 4, "name": "Eve"})                      # → lastrowid
ud.update("t", {"name": "Frank"}, "id = ?", (4,))             # → rowcount
ud.delete("t", "id = ?", (4,))                                 # → rowcount
ud.select("t", where="id > ?", params=(0,), order="name", limit=10)
```

---

## Utilities

```python
ud.tables()       # → ["t", "users", ...]
ud.cols("t")      # → ["id", "name"]
ud.has("t")       # → True / False
ud.count("t")     # → 42
ud.vacuum()       # optimize disk usage
```

---

## ud vs u.xsb

| | `ud.*` | `u.xsb()` |
|---|---|---|
| Connection management | manual (`conn` / `close`) | automatic |
| DB path | specified manually | auto `data/table/db/base.db` |
| SQL input | inline raw SQL | inline + file (`data/table/sql/`) |
| Returned rows | namedtuple (attribute access) | DotDict (attribute access) |
| Use case | low-level direct control | integrated with USEKIT path system |
