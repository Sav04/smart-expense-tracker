"""
Demo data seeder + database admin utilities.

Seeds demo expenses/budgets on first run, then never again — so once
the user clears everything to start fresh, demo data doesn't come back.
Use clear_all_data() to wipe and seed_demo_data(force=True) to reset.
"""

import sqlite3
from datetime import date, timedelta

from database import get_connection
from db_expenses import add_expense, get_all_expenses
from db_categories import get_all_categories
from db_budgets import set_budget


# (Keep your existing DEMO_EXPENSES and DEMO_BUDGETS lists exactly as they are —
# just paste them in here. I'm omitting them for brevity.)
DEMO_EXPENSES = [
    # ... your existing list of ~50 tuples ...
]

DEMO_BUDGETS = [
    # ... your existing list of 6 budget tuples ...
]


# ----- Seed tracking via a meta table -----------------------------

def _ensure_meta_table() -> None:
    """Create meta table if not exists. Idempotent."""
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()


def has_been_seeded() -> bool:
    """Check if the database has ever been auto-seeded."""
    _ensure_meta_table()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "SELECT value FROM meta WHERE key = 'seeded'"
        )
        return cursor.fetchone() is not None
    finally:
        conn.close()


def mark_as_seeded() -> None:
    """Record that the database has been seeded with demo data."""
    _ensure_meta_table()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO meta (key, value) VALUES ('seeded', '1')"
        )
        conn.commit()
    finally:
        conn.close()


def unmark_seeded() -> None:
    """Reset the seeded flag, so the next empty-DB load re-seeds."""
    _ensure_meta_table()
    conn = get_connection()
    try:
        conn.execute("DELETE FROM meta WHERE key = 'seeded'")
        conn.commit()
    finally:
        conn.close()


# ----- Helpers -----------------------------------------------------

def is_database_empty() -> bool:
    return len(get_all_expenses()) == 0


# ----- Seed function ----------------------------------------------

def seed_demo_data(force: bool = False) -> dict:
    """
    Populate DB with demo expenses + budgets.

    Skips if (a) DB already has data, or (b) has been seeded before.
    Pass force=True to bypass both checks.
    """
    if not force:
        if has_been_seeded():
            return {"seeded": False, "reason": "already seeded once"}
        if not is_database_empty():
            return {"seeded": False, "reason": "database not empty"}

    today = date.today()
    categories = get_all_categories()
    cat_name_to_id = {c["name"]: c["id"] for c in categories}

    n_added = 0
    for days_ago, desc, merchant, amount, cat_name, source in DEMO_EXPENSES:
        cat_id = cat_name_to_id.get(cat_name)
        if cat_id is None:
            continue
        add_expense(
            amount=amount,
            description=desc,
            category_id=cat_id,
            expense_date=today - timedelta(days=days_ago),
            merchant=merchant,
            source=source,
        )
        n_added += 1

    current_month = today.strftime("%Y-%m")
    n_budgets = 0
    for cat_name, limit, alert in DEMO_BUDGETS:
        cat_id = cat_name_to_id.get(cat_name)
        if cat_id is None:
            continue
        set_budget(
            category_id=cat_id,
            month=current_month,
            limit_amount=limit,
            alert_threshold=alert,
        )
        n_budgets += 1

    mark_as_seeded()

    return {
        "seeded": True,
        "expenses_added": n_added,
        "budgets_added": n_budgets,
    }


# ----- Admin: clear all data --------------------------------------

def clear_all_data() -> dict:
    """
    Delete all expenses, budgets, and corrections. Keeps the 'seeded'
    flag so demo data doesn't auto-restore. Use this when starting
    fresh with your own data.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM expenses")
        n_exp = cursor.fetchone()[0]
        cursor.execute("DELETE FROM expenses")

        cursor.execute("SELECT COUNT(*) FROM budgets")
        n_bud = cursor.fetchone()[0]
        cursor.execute("DELETE FROM budgets")

        try:
            cursor.execute("SELECT COUNT(*) FROM corrections")
            n_cor = cursor.fetchone()[0]
            cursor.execute("DELETE FROM corrections")
        except sqlite3.OperationalError:
            n_cor = 0

        conn.commit()
        return {
            "expenses_deleted": n_exp,
            "budgets_deleted": n_bud,
            "corrections_deleted": n_cor,
        }
    finally:
        conn.close()


if __name__ == "__main__":
    result = seed_demo_data(force=False)
    if result["seeded"]:
        print(f"✅ Seeded {result['expenses_added']} expenses "
              f"and {result['budgets_added']} budgets.")
    else:
        print(f"⏭️  Skipped: {result['reason']}")