#!/usr/bin/env python3
"""
SQL CRUD and Variable Demo for USEKIT

This example demonstrates:

1. DROP TABLE
2. CREATE TABLE
3. INSERT rows from Python data
4. SELECT all rows
5. SELECT with Python filter variables
6. UPDATE with Python variables
7. DELETE with Python variables
8. Keep the demo table for SQL View inspection

Note:
    This demo uses simple string building for readability.

    For real user input, parameter binding is safer when available.
"""

from usekit import u, uw


TABLE_NAME = "users_sample"
DROP_AT_END = False


def log(message):
    """Print a log message."""
    uw.p(message)


def sql_text(value):
    """
    Minimal SQL string escaping for demo purposes.

    This keeps the example readable.
    For real user input, prefer parameter binding when available.
    """
    return str(value).replace("'", "''")


def print_rows(title, rows):
    """Print rows in a readable format."""
    uw.p("")
    uw.p(f"--- {title} ---")

    if not rows:
        uw.p("(no rows)")
        return

    for row in rows:
        uw.p(f"{row.id}: {row.name} ({row.age}, {row.city}) - {row.created_at}")


def make_values_sql(records):
    """Build SQL VALUES from Python records."""
    parts = []

    for name, age, city in records:
        parts.append(
            f"('{sql_text(name)}', {int(age)}, '{sql_text(city)}')"
        )

    return ",\n        ".join(parts)


def reset_table():
    """Drop the sample table if it already exists."""
    u.xdb(f"""
    DROP TABLE IF EXISTS {TABLE_NAME}
    """)

    log(f"[OK] Reset table: {TABLE_NAME}")


def create_table():
    """Create the sample table."""
    u.xdb(f"""
    CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        age INTEGER NOT NULL,
        city TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    log(f"[OK] Created table: {TABLE_NAME}")


def insert_sample_data(records):
    """Insert sample rows from Python data."""
    values_sql = make_values_sql(records)

    u.xsb(f"""
    INSERT INTO {TABLE_NAME} (name, age, city)
    VALUES
        {values_sql}
    """)

    log("[OK] Inserted sample data from Python variables")


def fetch_all_users():
    """Fetch all users."""
    return u.xsb(f"""
    SELECT id, name, age, city, created_at
    FROM {TABLE_NAME}
    ORDER BY id ASC
    """)


def fetch_users_by_min_age(min_age):
    """Fetch users with age >= min_age."""
    return u.xsb(f"""
    SELECT id, name, age, city, created_at
    FROM {TABLE_NAME}
    WHERE age >= {int(min_age)}
    ORDER BY age ASC, id ASC
    """)


def update_user_age(name, new_age):
    """Update a user's age."""
    u.xsb(f"""
    UPDATE {TABLE_NAME}
    SET age = {int(new_age)}
    WHERE name = '{sql_text(name)}'
    """)

    log(f"[OK] Updated age for {name} to {new_age}")


def delete_user(name):
    """Delete a user by name."""
    u.xsb(f"""
    DELETE FROM {TABLE_NAME}
    WHERE name = '{sql_text(name)}'
    """)

    log(f"[OK] Deleted user: {name}")


def cleanup_table():
    """Optionally drop the demo table."""
    if DROP_AT_END:
        u.xdb(f"""
        DROP TABLE IF EXISTS {TABLE_NAME}
        """)

        log(f"[OK] Dropped table: {TABLE_NAME}")
    else:
        log(f"[OK] Kept table for SQL View inspection: {TABLE_NAME}")


def main():
    """Run the SQL CRUD and variable demo."""
    sample_users = [
        ("Alice", 30, "Seoul"),
        ("Bob", 25, "Busan"),
        ("Charlie", 35, "Incheon"),
        ("Diana", 28, "Daegu"),
    ]

    min_age = 30
    target_name = "Alice"
    new_age = 31
    delete_name = "Bob"

    reset_table()
    create_table()

    insert_sample_data(sample_users)

    rows = fetch_all_users()
    print_rows("After insert", rows)

    rows = fetch_users_by_min_age(min_age)
    print_rows(f"Filtered rows: age >= {min_age}", rows)

    update_user_age(target_name, new_age)

    rows = fetch_all_users()
    print_rows("After update", rows)

    delete_user(delete_name)

    rows = fetch_all_users()
    print_rows("After delete", rows)

    cleanup_table()

    uw.p("")
    uw.ok("SQL CRUD and variable demo completed")


if __name__ == "__main__":
    main()
