# Ledger App Example

A personal expense tracker built with USEKIT.

This example demonstrates a location-based workflow:

- the entry point lives in `base`
- reusable modules live in `sub`
- data is saved as JSON and CSV
- SQLite tables are created and queried
- a Markdown-formatted report is generated
- generated files remain as real project files

The important point is that `main.py` and its helper modules are **not in the same folder**.

USEKIT connects them by **location**.

---

## Quick Start

Open `examples/ledger_app_builder.py` in USEKIT Editor and press **RUN**.

Or run it with USEKIT:

```python
from usekit import use

use.exec.pyp.base("examples.ledger_app_builder")

After the builder creates the app files, the app is executed with:

use.exec.pyp.base("examples.ledger_app.main")


---

Location Layout

This example intentionally separates the entry point and reusable parts.

<project>/
├── src/
│   ├── base/
│   │   └── examples/
│   │       └── ledger_app/
│   │           ├── __init__.py
│   │           └── main.py
│   │
│   └── sub/
│       └── ledger_parts/
│           ├── __init__.py
│           ├── data.py
│           ├── db.py
│           └── report.py

main.py is in base.

src/base/examples/ledger_app/main.py

The reusable modules are in sub.

src/sub/ledger_parts/data.py
src/sub/ledger_parts/db.py
src/sub/ledger_parts/report.py

They are different USEKIT locations.


---

Run the App

from usekit import use

use.exec.pyp.base("examples.ledger_app.main")

This runs:

src/base/examples/ledger_app/main.py


---

Key Highlight

In standard Python, loading modules from a separate project area often requires package setup, current working directory control, or sys.path manipulation.

USEKIT uses explicit locations instead.

use.imp.pyp.sub("ledger_parts.data : get_records, get_budgets")
use.imp.pyp.sub("ledger_parts.db : reset_tables, insert_records, insert_budgets")
use.imp.pyp.sub("ledger_parts.report : make_report")

These calls mean:

import from src/sub/ledger_parts/data.py

import from src/sub/ledger_parts/db.py

import from src/sub/ledger_parts/report.py


No sys.path.append.

No main-relative import.

No need for ledger_parts to live beside main.py.

The command itself carries the location context.


---

What This Example Demonstrates

Feature	USEKIT Call	Purpose

Create entry module	use.write.pyp.base()	Write main.py to base
Create reusable modules	use.write.pyp.sub()	Write data.py, db.py, report.py to sub
Import reusable modules	use.imp.pyp.sub()	Load modules from sub
Run entry point	use.exec.pyp.base()	Execute main.py from base
Read / Write JSON	use.read.json.base() / use.write.json.base()	Store and reload data
Write CSV	use.write.csv.base()	Export table-like data
Write text report	use.write.txt.base()	Save the generated report
Create tables	use.exec.ddl.base()	Run SQLite DDL
Run SQL	use.exec.sql.base()	Insert and query data



---

Why This Matters

USEKIT is location-relative, not main-relative.

Standard Python often asks:

Where is this file relative to main.py?

Is the current working directory correct?

Do I need to patch sys.path?


USEKIT asks:

Which location does this object belong to?


Examples:

use.exec.pyp.base("examples.ledger_app.main")
use.imp.pyp.sub("ledger_parts.data : get_records")

The entry point is resolved from base.

The reusable parts are resolved from sub.

The two locations do not need to be physically nested together.


---

Generated Result

After running ledger_app_builder.py, USEKIT creates a project structure like this:

projects/pj01/
├── src/
│   ├── base/
│   │   └── examples/
│   │       └── ledger_app/
│   │           ├── __init__.py
│   │           └── main.py
│   │
│   └── sub/
│       └── ledger_parts/
│           ├── __init__.py
│           ├── data.py
│           ├── db.py
│           └── report.py
│
└── data/
    ├── json/
    │   └── base/
    │       ├── ledger_records.json
    │       ├── ledger_budgets.json
    │       ├── ledger_category_summary.json
    │       ├── ledger_daily_summary.json
    │       └── ledger_budget_summary.json
    │
    ├── common/
    │   ├── csv/
    │   │   └── base/
    │   │       ├── ledger_records.csv
    │   │       └── ledger_budget_summary.csv
    │   │
    │   └── txt/
    │       └── base/
    │           └── ledger_report.txt
    │
    └── table/
        ├── db/
        │   └── base.db
        └── ddl/
            └── base/
                ├── ledger.sql
                └── budget.sql

The generated files are real project files, not temporary notebook-only output.

They can be opened from:

USEKIT Editor

Android file manager

Termux

Google Drive

Git



---

Output

Category Summary

Category	Total	Count

food	37,000	3
book	25,000	1
shopping	9,000	1
coffee	4,500	1
transport	1,500	1


Daily Summary

Date	Total

2026-05-01	16,500
2026-05-02	19,500
2026-05-03	41,000


Budget Check

Category	Used	Budget	Remaining	Status

food	37,000	30,000	-7,000	OVER
book	25,000	20,000	-5,000	OVER
shopping	9,000	0	-9,000	NO BUDGET
coffee	4,500	10,000	5,500	OK
transport	1,500	10,000	8,500	OK



---

SQL Inspection

The example also creates SQLite tables.

You can inspect them in USEKIT Editor SQL View:

select * from ledger;

Expected tables:

Table	Description

ledger	expense records
budget	category budgets


The ledger table contains 7 rows.

The budget table contains 4 rows.


---

Reproducibility

This example is reproducible.

Even if src/ and data/ are removed, running ledger_app_builder.py recreates:

app source files

reusable modules

SQLite tables

JSON outputs

CSV outputs

text report


This makes the example useful for mobile Colab, Termux, and other environments where project files may need to be rebuilt.


---

Summary

This example shows the core USEKIT workflow:

write modules by location

import modules by location

execute modules by location

save results by location

inspect results in the same project workspace


The app is split across base and sub, but it runs as one workflow.

That is the role of use.imp: connecting project parts by location, without making them depend on main.py. 