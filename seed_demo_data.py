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


# Format: (days_ago, description, merchant, amount, category_name, source)
DEMO_EXPENSES = [
    # ----- Today -----
    (0, "Swiggy lunch order", "SWIGGY*BANGALORE", 320.00, "Food & Dining", "sms"),
    (0, "Auto rickshaw to lab", None, 60.00, "Transport", "manual"),

    # ----- Last week -----
    (1, "Coffee with friends at Starbucks", "STARBUCKS", 450.00, "Food & Dining", "sms"),
    (1, "Uber to college", "UBER INDIA", 145.00, "Transport", "sms"),
    (2, "Books for school", None, 850.00, "Education", "manual"),
    (2, "Mobile recharge", "AIRTEL", 199.00, "Bills & Utilities", "sms"),
    (3, "Dominos pizza dinner", "DOMINOS", 480.00, "Food & Dining", "sms"),
    (3, "Petrol fill bike", "HP PETROL PUMP", 350.00, "Transport", "sms"),
    (4, "BookMyShow movie ticket", "BOOKMYSHOW", 280.00, "Entertainment", "sms"),
    (4, "Popcorn and drinks at cinema", None, 350.00, "Food & Dining", "manual"),
    (5, "Mess fees monthly", None, 3500.00, "Food & Dining", "manual"),
    (5, "Stationery for project", None, 280.00, "Education", "manual"),
    (6, "Chayos tea delivery", "CHAYOS", 220.00, "Food & Dining", "sms"),
    (7, "Amazon order headphones", "AMAZON IN", 1299.00, "Shopping", "sms"),
    (7, "Doctor consultation fee", None, 500.00, "Health & Medical", "manual"),

    # ----- 1-2 weeks ago -----
    (8, "Zomato dinner order", "ZOMATO", 380.00, "Food & Dining", "sms"),
    (9, "Spotify premium monthly", "SPOTIFY", 119.00, "Entertainment", "sms"),
    (10, "Coursera course subscription", "COURSERA", 999.00, "Education", "sms"),
    (10, "Uber ride to mall", "UBER INDIA", 200.00, "Transport", "sms"),
    (11, "Lunch at Hyderabadi Biryani", None, 280.00, "Food & Dining", "manual"),
    (12, "Electricity bill", "BSES", 1450.00, "Bills & Utilities", "sms"),
    (13, "Gym membership monthly", "CULT FIT", 1499.00, "Health & Medical", "sms"),
    (14, "Engineering drawing kit", None, 350.00, "Education", "manual"),
    (15, "Flipkart phone case", "FLIPKART", 499.00, "Shopping", "sms"),

    # ----- 2-4 weeks ago -----
    (16, "McDonald's burger meal", "MCDONALDS", 280.00, "Food & Dining", "sms"),
    (17, "Auto rickshaw return", None, 80.00, "Transport", "manual"),
    (18, "Internet bill monthly", "JIO FIBER", 799.00, "Bills & Utilities", "sms"),
    (19, "Engineering textbook", "AMAZON IN", 650.00, "Education", "sms"),
    (20, "Birthday gift for friend", None, 800.00, "Miscellaneous", "manual"),
    (22, "Swiggy weekend order", "SWIGGY*BANGALORE", 520.00, "Food & Dining", "sms"),
    (23, "Petrol fill bike", "INDIAN OIL", 400.00, "Transport", "sms"),
    (24, "Netflix monthly subscription", "NETFLIX", 199.00, "Entertainment", "sms"),
    (25, "Medicine pharmacy", "APOLLO PHARMACY", 245.00, "Health & Medical", "sms"),
    (26, "Lunch with classmates", None, 380.00, "Food & Dining", "manual"),
    (27, "Amazon shopping order", "AMAZON IN", 1250.00, "Shopping", "sms"),
    (28, "Mobile recharge Jio", "JIO", 399.00, "Bills & Utilities", "sms"),
    (29, "Tea and samosa", None, 50.00, "Food & Dining", "manual"),
    (30, "Ola cab to station", "OLA", 450.00, "Transport", "sms"),

    # ----- Last month -----
    (32, "IRCTC train ticket home", "IRCTC", 720.00, "Transport", "sms"),
    (34, "Restaurant dinner with family", "BARBEQUE NATION", 1250.00, "Food & Dining", "sms"),
    (36, "Coursera specialization", "COURSERA", 1499.00, "Education", "sms"),
    (38, "Movie ticket weekend", "BOOKMYSHOW", 320.00, "Entertainment", "sms"),
    (40, "Clothes shopping mall", None, 1800.00, "Shopping", "manual"),
    (42, "Auto rickshaw", None, 90.00, "Transport", "manual"),
    (44, "Mess fees monthly", None, 3500.00, "Food & Dining", "manual"),
    (46, "Lab manual purchase", None, 220.00, "Education", "manual"),
    (48, "Electricity bill", "BSES", 1380.00, "Bills & Utilities", "sms"),

    # ----- 2 months ago -----
    (52, "Swiggy late night order", "SWIGGY", 180.00, "Food & Dining", "sms"),
    (55, "Dental cleanup appointment", None, 1500.00, "Health & Medical", "manual"),
    (58, "Festival celebration", None, 1200.00, "Miscellaneous", "manual"),
    (62, "Gift for parents anniversary", None, 2000.00, "Miscellaneous", "manual"),
    (65, "Concert tickets BookMyShow", "BOOKMYSHOW", 1500.00, "Entertainment", "sms"),
    (70, "Engineering kit purchase", None, 450.00, "Education", "manual"),
]


# Format: (category_name, monthly_limit, alert_threshold)
DEMO_BUDGETS = [
    ("Food & Dining", 8000.00, 0.80),
    ("Transport", 3000.00, 0.80),
    ("Education", 5000.00, 0.75),
    ("Bills & Utilities", 2500.00, 0.80),
    ("Shopping", 4000.00, 0.85),
    ("Entertainment", 1500.00, 0.80),
]


# ----- Seed tracking via a meta table -----------------------------

def _ensure_meta_table() -> None:
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