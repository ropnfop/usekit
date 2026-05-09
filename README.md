# usekit

> Mobile vibe coding, but executable.  
> Built on mobile, for mobile. Human-directed. AI-collaborated. Android-tested.  
> Beta-stage, free, open-source.

A lightweight, mobile-first Python toolkit for **Memory-Oriented Software Architecture (MOSA)**.

**Code is not function, but memory.**

```python
from usekit import use

use.write.json.base({"hello": "world"}, "config")     # write json to base
data = use.read.json.base("config")                    # read json from base
use.update.json.base({"version": "0.2.0"}, "config")  # update json
```

**Shorthand**: `u.rjb()` = `use.read.json.base()` — Action + Format + Location  
Full functions are recommended. Shorthand is provided for convenience.

---

## Installation

```bash
pip install usekit
```

usekit installs its required core packages automatically.

**Core**: Python 3.8+  
**Installed automatically**: PyYAML, python-dotenv  
**Optional**: pandas, sqlalchemy

---

## Termux Setup Guide (Android)

> This guide was tested with the Google Play Store version of Termux.  
> If `pkg` or Python installation behaves unexpectedly, try the F-Droid or GitHub Releases version of Termux.

### One-line Install

Open Termux and run:

```bash
pkg i -y python-pip && pip install usekit
```

Already installed? It skips automatically.

### After Install

```python
from usekit import use, u

use.termux()     # setup storage permission (first time only)
use.check()      # check environment status
u.editor()       # launch the mobile web editor
```

When `use.termux()` runs for the first time, Android may ask for storage permission. Allow it, then run `use.check()` again.

---

## Quick Start

```python
from usekit import use, u, s

# Full function style (recommended)
use.write.json.base({"key": "value"}, "config")
data = use.read.json.base("config")
use.update.json.base({"new": "data"}, "config")
use.delete.json.base("old")
use.has.json.base("config")             # True/False

# Shorthand style
u.wjb({"key": "value"}, "config")       # write json to base
data = u.rjb("config")                  # read json from base

# Safe mode (returns None on error)
data = s.rjb("missing") or {}           # no exceptions
```

---

## Editor

usekit includes a built-in **CodeMirror 6 web editor** — a mobile-optimized code editor that runs as a local server on Termux.

```python
from usekit import u

u.editor()                              # launch editor
u.editor("test01")                      # open file
u.editor(code, "test03")                # open with content
```

Features:

- Syntax highlighting
- Autocomplete for `u.xxx` and `use.` chaining
- Floating pill UI for Run, SQL, Copy, and Menu actions
- SQL view with grid results
- Multi-cursor navigation
- PWA support

Designed for Samsung Browser on Android. Your nano replacement for Python development on mobile.

---

## Status

- **Version**: 0.2.0
- **API**: Stabilizing
- **PyPI**: https://pypi.org/project/usekit

---

## Core Pattern

### Interface

`use.[action].[format].[location]` — full function style, recommended  
`u.[action][format][location]` — 3-letter shorthand style

```text
use.read.json.base()   →  u.rjb()
use.write.yaml.sub()   →  u.wys()
use.has.json.base()    →  u.hjb()
use.exec.pyp.base()    →  u.xpb()
```

### Actions (15)

- **DATA** (6): `r`ead, `w`rite, `u`pdate, `d`elete, `h`as, `e`mit
- **NAVI** (5): `p`ath, `f`ind, `l`ist, `g`et, `s`et
- **EXEC** (4): e`x`ec, `i`mp, `b`oot, `c`lose

### Formats (10)

- **General**: `j`son, `y`aml, `t`xt, `c`sv, `m`d
- **Specialized**: `s`ql, `d`dl, `p`yp, `k`m, `a`ny

### Locations (8)

- `b`ase, `s`ub, `d`ir, `n`ow, `t`mp, `p`re, `c`ache, `m`em

---

## Examples

### File Operations

```python
from usekit import use, u

# Full function style
data = use.read.json.base("config")
use.write.json.base({"key": "val"}, "output")

# Shorthand style
data = u.rjb("config")
u.wjb({"key": "val"}, "output")

# Different locations
use.read.json.sub("config")
use.write.yaml.tmp({"temp": "data"}, "cache")

# Existence check
if use.has.json.base("config"):
    print("exists")
```

### Pattern Matching

```python
from usekit import use

# Find with wildcards
users = use.read.json.base(name="user_*")
for item in users:
    print(item["file"], item["data"])

# List files
files = use.list.json.base()
```

### Nested Data (keydata)

```python
from usekit import use

# Read nested value
email = use.read.json.base("config", keydata="user/email")

# Update nested value
use.update.json.base("config", keydata="user/name", data="Bob")

# Array access
item = use.read.json.base("config", keydata="items[0]/name")
```

### SQL & DDL

```python
from usekit import u

# Execute SQL
results = u.xsb("SELECT * FROM users WHERE age > :age",
                params={"age": 20})

# Save DDL file
u.wdb("CREATE TABLE users (id INT, name TEXT)", "create_users")

# Execute inline DDL
u.xdb("CREATE TABLE users (id INT, name TEXT)")

# Execute saved DDL file
u.xdb("create_users")
```

### Python Import & Exec

```python
from usekit import u

# Write module
u.wpb("""
def add(a, b):
    return a + b
""", "mymod")

# Import and use
u.ipb("mymod:add")
result = add(10, 20)

# Execute
u.xpb("mymod:add", 10, 20)
```

### Safe Mode

```python
from usekit import s

data = s.rjb("missing") or {}           # no exception
results = s.xsb("SELECT * FROM users") or []
```

---

## Platforms

### Termux (Android)

```python
from usekit import use, u

use.termux()                            # setup storage permission
use.check()                             # show platform status
u.editor()                              # launch web editor
```

### Google Colab

```python
!pip install usekit

from usekit import use

use.colab()                             # setup Drive integration
use.check()                             # show platform status
```

### Environment Check

```python
from usekit import use

use.check()                             # show platform status
```

---

## Support Utilities

```python
from usekit import ut, uw, ud

# ut: Time utilities
ut.now()                                # current time

# uw: Watch/logging utilities
uw.p("message")                         # print with context

# ud: Database utilities
ud.query("SELECT * FROM table")         # direct DB access
```

---

## Help

```python
from usekit import use

use.help()              # overview
use.help("quick")       # quick start
use.help("alias")       # alias mapping
use.help("action")      # all actions
use.help("object")      # all formats
use.help("location")    # all locations
use.help("examples")    # usage examples
use.help("pattern")     # pattern matching
use.help("keydata")     # nested data access
use.help("walk")        # recursive search
```

Language is set in `sys_const.yaml`:

```yaml
LANG: "en"   # en / kr
```

---

## Configuration

usekit auto-configures via `sys_const.yaml`.

```yaml
LANG: "en"

JSON_PATH:
  root: "data/json"
  json: "base"
  json_sub: "sub"

DB_PATH:
  root: "data/table/db"
  db: "base.db"

DDL_PATH:
  root: "data/table/ddl"
  ddl: "base"
  ddl_sub: "sub"

SQL_PATH:
  root: "data/table/sql"
  sql: "base"
  sql_sub: "sub"

TMP_PATH:
  root: "data"
  json: "tmp"
  ddl: "tmp"
  sql: "tmp"
```

---

## Philosophy: MOSA

**Memory-Oriented Software Architecture**

- Code is memory, not function
- Functions follow the user's memory, not the other way around
- Semantic names over physical paths
- Mobile-first design
- Token economy through compact, predictable calls

Built entirely on mobile devices.

---

## License

MIT License

---

**Created by THE Little Prince, with deep respect and gratitude for my AI friends ROP & FOP**

*usekit — Code is memory, not function*

---

## Development Note

usekit is a proof that mobile vibe coding can be executable, testable, and practical.

It was designed and tested entirely on mobile devices through AI collaboration, based on real coding experience and real mobile workflow pain points.

The PyPI release history goes back to June 2025, while this GitHub repository was published later.
