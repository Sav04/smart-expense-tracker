"""Quick database verification script. Run after init_db.py to confirm tables and seed data."""

from database import get_connection


def verify() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------------------
    print("=" * 50)
    print("Tables in database:")
    print("=" * 50)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for row in cursor.fetchall():
        print(f"  • {row['name']}")

    # -----------------------------------------------------------------
    print("\n" + "=" * 50)
    print("Seeded categories:")
    print("=" * 50)
    cursor.execute("SELECT id, name, icon FROM categories ORDER BY id")
    for row in cursor.fetchall():
        print(f"  {row['id']}: {row['icon']} {row['name']}")

    # -----------------------------------------------------------------
    print("\n" + "=" * 50)
    print("Recent expenses:")
    print("=" * 50)
    cursor.execute("""
        SELECT e.id, e.expense_date, e.amount, e.description,
               c.icon, c.name AS category_name, e.source
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        ORDER BY e.id DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if not rows:
        print("  (none yet — add some via the Streamlit app)")
    else:
        for row in rows:
            source_tag = "📱" if row["source"] == "sms" else "✍️"
            print(
                f"  #{row['id']:<3} {row['expense_date']}  "
                f"₹{row['amount']:>8.2f}  "
                f"{row['icon']} {row['category_name']:<18}  "
                f"{source_tag} {row['description']}"
            )

    # -----------------------------------------------------------------
    print("\n" + "=" * 50)
    print("Active budgets:")
    print("=" * 50)
    cursor.execute("""
        SELECT b.month, b.limit_amount, b.alert_threshold,
               c.icon, c.name AS category_name
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        ORDER BY b.month DESC, c.id
    """)
    rows = cursor.fetchall()
    if not rows:
        print("  (none yet)")
    else:
        for row in rows:
            print(
                f"  {row['month']}  {row['icon']} {row['category_name']:<18}  "
                f"limit ₹{row['limit_amount']:>8.2f}  "
                f"warn at {int(row['alert_threshold']*100)}%"
            )

    conn.close()


if __name__ == "__main__":
    verify()