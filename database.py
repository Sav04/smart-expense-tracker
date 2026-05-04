"""
Database connection module.

Provides a single function `get_connection()` that other modules use
to talk to the SQLite database. Centralizing this means the database
location and connection settings live in exactly one place.
"""

import sqlite3
from pathlib import Path

# Resolve the database path relative to THIS file's location, not the
# current working directory. This matters because Streamlit might run
# from anywhere on the filesystem.
DB_PATH = Path(__file__).parent / "data" / "expenses.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a connection to the expenses database.

    Returns:
        sqlite3.Connection: A live database connection. Caller is
        responsible for closing it (or using a `with` block).
    """
    # Make sure the parent folder exists. If someone clones the repo
    # fresh, the data/ folder might not be there yet (it's gitignored).
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Connect. If the .db file doesn't exist, SQLite creates it.
    conn = sqlite3.connect(DB_PATH)

    # Enable foreign-key enforcement. SQLite has it OFF by default
    # (historical reasons). We MUST turn it on for our FOREIGN KEY
    # constraints to actually do anything.
    conn.execute("PRAGMA foreign_keys = ON")

    # Make query results accessible by column name (row["amount"])
    # instead of just by index (row[1]). Way more readable.
    conn.row_factory = sqlite3.Row

    return conn