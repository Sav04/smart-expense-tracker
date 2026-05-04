"""
One-time database initialization script.

Creates the three tables (categories, expenses, budgets) and seeds
the 8 default categories. Safe to run multiple times — uses
"CREATE TABLE IF NOT EXISTS" and "INSERT OR IGNORE" patterns.

Usage:
    python init_db.py
"""

from database import get_connection


# ---------------------------------------------------------------------
# SQL: schema definitions
# ---------------------------------------------------------------------

CREATE_CATEGORIES_TABLE = """
CREATE TABLE IF NOT EXISTS categories (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    name  TEXT NOT NULL UNIQUE,
    icon  TEXT NOT NULL,
    color TEXT NOT NULL
);
"""

CREATE_EXPENSES_TABLE = """
CREATE TABLE IF NOT EXISTS expenses (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    amount       REAL    NOT NULL CHECK (amount > 0),
    description  TEXT    NOT NULL,
    category_id  INTEGER NOT NULL,
    expense_date DATE    NOT NULL,
    merchant     TEXT,
    source       TEXT    NOT NULL CHECK (source IN ('manual', 'sms')),
    raw_sms      TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);
"""

CREATE_BUDGETS_TABLE = """
CREATE TABLE IF NOT EXISTS budgets (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id      INTEGER NOT NULL,
    month            TEXT    NOT NULL,
    limit_amount     REAL    NOT NULL CHECK (limit_amount > 0),
    alert_threshold  REAL    NOT NULL DEFAULT 0.8,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    UNIQUE (category_id, month)
);
"""


# ---------------------------------------------------------------------
# Seed data: the 8 default categories
# ---------------------------------------------------------------------

DEFAULT_CATEGORIES = [
    ("Food & Dining",     "🍔", "#FF6B6B"),
    ("Transport",         "🚗", "#4ECDC4"),
    ("Bills & Utilities", "💡", "#FFD93D"),
    ("Shopping",          "🛒", "#95E1D3"),
    ("Entertainment",     "🎬", "#C77DFF"),
    ("Health & Medical",  "🏥", "#06FFA5"),
    ("Education",         "📚", "#4D96FF"),
    ("Miscellaneous",     "📦", "#B8B8B8"),
]


def init_database() -> None:
    """Create all tables and seed default categories. Idempotent."""
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Create tables (no-op if they already exist)
        print("Creating tables...")
        cursor.execute(CREATE_CATEGORIES_TABLE)
        cursor.execute(CREATE_EXPENSES_TABLE)
        cursor.execute(CREATE_BUDGETS_TABLE)
        print("  ✓ categories")
        print("  ✓ expenses")
        print("  ✓ budgets")

        # Seed the default categories. INSERT OR IGNORE means: if a
        # category with this name already exists, skip silently.
        # That's why running this script multiple times is safe.
        print("\nSeeding default categories...")
        cursor.executemany(
            "INSERT OR IGNORE INTO categories (name, icon, color) VALUES (?, ?, ?)",
            DEFAULT_CATEGORIES,
        )
        print(f"  ✓ {cursor.rowcount} new categories inserted")

        # Commit the changes. Without this, nothing gets saved!
        conn.commit()
        print("\n✅ Database initialized successfully.")

    finally:
        # Always close the connection, even if an error occurred above.
        conn.close()


if __name__ == "__main__":
    init_database()