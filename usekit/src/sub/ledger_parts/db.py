from usekit import u

def reset():
    u.xdb("DROP TABLE IF EXISTS ledger")
    u.xdb("""
    CREATE TABLE ledger (
        id      INTEGER PRIMARY KEY AUTOINCREMENT,
        date    TEXT,
        type    TEXT,
        category TEXT,
        amount  INTEGER,
        memo    TEXT
    )
    """)

def insert(date, type_, category, amount, memo=""):
    u.xsb(f"""
    INSERT INTO ledger (date, type, category, amount, memo)
    VALUES ('{date}', '{type_}', '{category}', {amount}, '{memo}')
    """)

def fetch_all():
    return u.xsb("SELECT * FROM ledger ORDER BY date, id")

def fetch_summary():
    return u.xsb("""
    SELECT type, category, SUM(amount) as total
    FROM ledger
    GROUP BY type, category
    ORDER BY type, total DESC
    """)

def balance():
    rows = u.xsb("""
    SELECT
        SUM(CASE WHEN type='수입' THEN amount ELSE 0 END) as income,
        SUM(CASE WHEN type='지출' THEN amount ELSE 0 END) as expense
    FROM ledger
    """)
    r = rows[0]
    return r.income, r.expense, r.income - r.expense
