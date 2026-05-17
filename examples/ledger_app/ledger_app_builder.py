from usekit import use, uw

MAIN_DIR = "examples/ledger_app"
PARTS_DIR = "ledger_parts"


use.write.pyp.base(r'''
# Ledger app package
''', "__init__", "examples")


use.write.pyp.base(r'''
# Ledger app package
''', "__init__", MAIN_DIR)


use.write.pyp.sub(r'''
# Ledger parts package
''', "__init__", PARTS_DIR)


use.write.pyp.sub(r'''
def get_records():
    """Return sample ledger records."""
    return [
        {"date": "2026-05-01", "category": "food", "memo": "lunch", "amount": 12000},
        {"date": "2026-05-01", "category": "coffee", "memo": "latte", "amount": 4500},
        {"date": "2026-05-02", "category": "transport", "memo": "bus", "amount": 1500},
        {"date": "2026-05-02", "category": "food", "memo": "dinner", "amount": 18000},
        {"date": "2026-05-03", "category": "book", "memo": "python book", "amount": 25000},
        {"date": "2026-05-03", "category": "food", "memo": "snack", "amount": 7000},
        {"date": "2026-05-03", "category": "shopping", "memo": "notebook", "amount": 9000},
    ]


def get_budgets():
    """Return sample category budgets."""
    return [
        {"category": "food", "budget_amount": 30000},
        {"category": "coffee", "budget_amount": 10000},
        {"category": "transport", "budget_amount": 10000},
        {"category": "book", "budget_amount": 20000},
    ]
''', "data", PARTS_DIR)


use.write.pyp.sub(r'''
from usekit import use


def _sql_text(value):
    """Escape text for a simple SQL literal."""
    return str(value).replace("'", "''")


def _rows_to_dicts(rows):
    """Convert row-like objects to plain dicts."""
    result = []
    for row in rows or []:
        try:
            result.append(dict(row))
        except Exception:
            result.append(row)
    return result


def reset_tables():
    """Reset ledger and budget tables."""
    use.exec.ddl.base("DROP TABLE IF EXISTS ledger")
    use.exec.ddl.base("DROP TABLE IF EXISTS budget")

    use.exec.ddl.base("""
    CREATE TABLE ledger (
        date TEXT,
        category TEXT,
        memo TEXT,
        amount INTEGER
    )
    """)

    use.exec.ddl.base("""
    CREATE TABLE budget (
        category TEXT PRIMARY KEY,
        budget_amount INTEGER
    )
    """)


def insert_records(records):
    """Insert ledger records."""
    for row in records:
        use.exec.sql.base(f"""
        INSERT INTO ledger (date, category, memo, amount)
        VALUES (
            '{_sql_text(row["date"])}',
            '{_sql_text(row["category"])}',
            '{_sql_text(row["memo"])}',
            {int(row["amount"])}
        )
        """)


def insert_budgets(budgets):
    """Insert category budgets."""
    for row in budgets:
        use.exec.sql.base(f"""
        INSERT INTO budget (category, budget_amount)
        VALUES (
            '{_sql_text(row["category"])}',
            {int(row["budget_amount"])}
        )
        """)


def get_category_summary():
    """Return expense summary by category."""
    return _rows_to_dicts(use.exec.sql.base("""
    SELECT
        category,
        SUM(amount) AS total_amount,
        COUNT(*) AS count
    FROM ledger
    GROUP BY category
    ORDER BY total_amount DESC
    """))


def get_daily_summary():
    """Return expense summary by date."""
    return _rows_to_dicts(use.exec.sql.base("""
    SELECT
        date,
        SUM(amount) AS total_amount
    FROM ledger
    GROUP BY date
    ORDER BY date
    """))


def get_budget_summary():
    """Return budget check summary without missing unbudgeted categories."""
    return _rows_to_dicts(use.exec.sql.base("""
    WITH all_categories AS (
        SELECT category FROM ledger
        UNION
        SELECT category FROM budget
    ),
    ledger_summary AS (
        SELECT
            category,
            SUM(amount) AS used_amount,
            COUNT(*) AS count
        FROM ledger
        GROUP BY category
    )
    SELECT
        c.category,
        COALESCE(l.used_amount, 0) AS used_amount,
        COALESCE(l.count, 0) AS count,
        COALESCE(b.budget_amount, 0) AS budget_amount,
        COALESCE(b.budget_amount, 0) - COALESCE(l.used_amount, 0) AS remaining_amount
    FROM all_categories c
    LEFT JOIN ledger_summary l
        ON c.category = l.category
    LEFT JOIN budget b
        ON c.category = b.category
    ORDER BY used_amount DESC
    """))
''', "db", PARTS_DIR)


use.write.pyp.sub(r'''
def _money(value):
    """Format integer money value with commas."""
    return f"{int(value):,}"


def make_report(category_summary, daily_summary, budget_summary):
    """Build a Markdown ledger report."""
    lines = []

    lines.append("# Ledger Report")
    lines.append("")

    lines.append("## Category Summary")
    lines.append("")
    lines.append("| Category | Total | Count |")
    lines.append("|---|---:|---:|")

    for row in category_summary:
        lines.append(
            f"| {row['category']} | {_money(row['total_amount'])} | {row['count']} |"
        )

    lines.append("")
    lines.append("## Daily Summary")
    lines.append("")
    lines.append("| Date | Total |")
    lines.append("|---|---:|")

    for row in daily_summary:
        lines.append(f"| {row['date']} | {_money(row['total_amount'])} |")

    lines.append("")
    lines.append("## Budget Check")
    lines.append("")
    lines.append("| Category | Used | Budget | Remaining | Status |")
    lines.append("|---|---:|---:|---:|---|")

    for row in budget_summary:
        used = row["used_amount"]
        budget = row["budget_amount"]
        remaining = row["remaining_amount"]

        if budget <= 0:
            status = "NO BUDGET"
        elif used > budget:
            status = "OVER"
        else:
            status = "OK"

        lines.append(
            f"| {row['category']} | {_money(used)} | {_money(budget)} | "
            f"{_money(remaining)} | {status} |"
        )

    return "\n".join(lines)
''', "report", PARTS_DIR)


use.write.pyp.base(r'''
from usekit import use, uw

use.imp.pyp.sub("ledger_parts.data : get_records, get_budgets")

use.imp.pyp.sub(
    "ledger_parts.db : reset_tables, insert_records, insert_budgets, "
    "get_category_summary, get_daily_summary, get_budget_summary"
)

use.imp.pyp.sub("ledger_parts.report : make_report")


def main():
    records = get_records()
    budgets = get_budgets()

    use.write.json.base(records, "ledger_records")
    use.write.json.base(budgets, "ledger_budgets")
    use.write.csv.base(records, "ledger_records")

    loaded_records = use.read.json.base("ledger_records")
    loaded_budgets = use.read.json.base("ledger_budgets")

    uw.p("Saved JSON and CSV source files")

    reset_tables()
    insert_records(loaded_records)
    insert_budgets(loaded_budgets)

    uw.p("Inserted ledger and budget data into SQLite")

    category_summary = get_category_summary()
    daily_summary = get_daily_summary()
    budget_summary = get_budget_summary()

    use.write.json.base(category_summary, "ledger_category_summary")
    use.write.json.base(daily_summary, "ledger_daily_summary")
    use.write.json.base(budget_summary, "ledger_budget_summary")
    use.write.csv.base(budget_summary, "ledger_budget_summary")

    report = make_report(category_summary, daily_summary, budget_summary)
    use.write.txt.base(report, "ledger_report")

    uw.p("")
    uw.p(report)
    uw.ok("Ledger app completed")


if __name__ == "__main__":
    main()
''', "main", MAIN_DIR)


uw.ok("Ledger app files created")

use.exec.pyp.base("examples.ledger_app.main")