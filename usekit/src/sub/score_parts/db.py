from usekit import u

def reset():
    u.xdb("DROP TABLE IF EXISTS scores")
    u.xdb("""
    CREATE TABLE scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        score INTEGER
    )
    """)

def insert(name, score):
    u.xsb(f"INSERT INTO scores (name, score) VALUES ('{name}', {score})")

def fetch_all():
    return u.xsb("SELECT * FROM scores ORDER BY score DESC")
