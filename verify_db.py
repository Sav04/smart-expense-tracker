"""Quick database verification script. Run after init_db.py to confirm tables and seed data."""

from database import get_connection


def verify() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    print("=" * 50)
    print("Tables in database:")
    print("=" * 50)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    for row in cursor.fetchall():
        print(f"  • {row['name']}")

    print("\n" + "=" * 50)
    print("Seeded categories:")
    print("=" * 50)
    cursor.execute("SELECT id, name, icon FROM categories ORDER BY id")
    for row in cursor.fetchall():
        print(f"  {row['id']}: {row['icon']} {row['name']}")

    conn.close()


if __name__ == "__main__":
    verify()