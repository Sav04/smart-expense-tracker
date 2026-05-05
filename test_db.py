"""
Manual smoke test for the database layer.

Runs through add → read → update → budget → status → delete.
Prints clear ✓ / ✗ markers so you can spot any failure at a glance.

Usage:
    python test_db.py
"""

from datetime import date

from db_categories import get_all_categories, get_category_by_name
from db_expenses import (
    add_expense,
    get_all_expenses,
    get_expense_by_id,
    update_expense,
    delete_expense,
)
from db_budgets import (
    set_budget,
    get_budget,
    get_budget_status,
    delete_budget,
)


def section(title: str) -> None:
    """Print a visual separator."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def main() -> None:
    # -----------------------------------------------------------------
    section("1. Categories")
    # -----------------------------------------------------------------
    cats = get_all_categories()
    print(f"✓ Found {len(cats)} categories")

    food = get_category_by_name("Food & Dining")
    assert food is not None, "Food & Dining should exist"
    print(f"✓ Looked up '{food['name']}' → id={food['id']}")
    food_id = food["id"]

    transport = get_category_by_name("Transport")
    transport_id = transport["id"]

    # -----------------------------------------------------------------
    section("2. Add expenses")
    # -----------------------------------------------------------------
    today = date.today()
    e1 = add_expense(
        amount=450.0,
        description="Lunch at Swiggy",
        category_id=food_id,
        expense_date=today,
        merchant="Swiggy",
        source="manual",
    )
    print(f"✓ Inserted expense #{e1} (Lunch at Swiggy)")

    e2 = add_expense(
        amount=120.0,
        description="Uber to college",
        category_id=transport_id,
        expense_date=today,
        merchant="Uber",
        source="sms",
        raw_sms="Rs.120 debited from a/c XX1234 for UBER",
    )
    print(f"✓ Inserted expense #{e2} (Uber to college, sms-sourced)")

    e3 = add_expense(
        amount=1500.0,
        description="Groceries",
        category_id=food_id,
        expense_date=today,
        source="manual",
    )
    print(f"✓ Inserted expense #{e3} (Groceries, no merchant)")

    # -----------------------------------------------------------------
    section("3. Read expenses")
    # -----------------------------------------------------------------
    all_exp = get_all_expenses()
    print(f"✓ get_all_expenses() returned {len(all_exp)} rows")
    for row in all_exp[:3]:
        print(f"   • #{row['id']} ₹{row['amount']:>7.2f}  {row['category_icon']} "
              f"{row['category_name']:<18} — {row['description']}")

    food_only = get_all_expenses(category_id=food_id)
    print(f"✓ Filtered by Food category → {len(food_only)} rows")

    one = get_expense_by_id(e1)
    assert one is not None
    print(f"✓ get_expense_by_id({e1}) → {one['description']}")

    # -----------------------------------------------------------------
    section("4. Update expense")
    # -----------------------------------------------------------------
    updated = update_expense(e1, amount=475.0, description="Lunch at Swiggy (with tip)")
    assert updated is True
    refetched = get_expense_by_id(e1)
    print(f"✓ Updated #{e1}: ₹{refetched['amount']} — {refetched['description']}")

    # -----------------------------------------------------------------
    section("5. Budgets")
    # -----------------------------------------------------------------
    current_month = today.strftime("%Y-%m")
    print(f"  (current month: {current_month})")

    b1 = set_budget(
        category_id=food_id,
        month=current_month,
        limit_amount=5000.0,
        alert_threshold=0.8,
    )
    print(f"✓ Set Food budget for {current_month}: ₹5000 (warn at 80%)")

    b2 = set_budget(
        category_id=transport_id,
        month=current_month,
        limit_amount=200.0,  # tiny, to trigger 'exceeded' if any transport spend
        alert_threshold=0.8,
    )
    print(f"✓ Set Transport budget for {current_month}: ₹200 (warn at 80%)")

    # Test upsert: set the same budget again with a different limit
    b1_again = set_budget(
        category_id=food_id,
        month=current_month,
        limit_amount=6000.0,  # increased
        alert_threshold=0.9,
    )
    assert b1 == b1_again, "Upsert should return the same row id"
    print(f"✓ Upsert worked: Food budget updated to ₹6000 (same row id)")

    fetched = get_budget(food_id, current_month)
    assert fetched["limit_amount"] == 6000.0
    print(f"✓ get_budget() reflects the upsert: ₹{fetched['limit_amount']}")

    # -----------------------------------------------------------------
    section("6. Budget status (the headline feature)")
    # -----------------------------------------------------------------
    food_status = get_budget_status(food_id, current_month)
    print(f"  Food:")
    print(f"    spent     : ₹{food_status['spent']:.2f}")
    print(f"    limit     : ₹{food_status['limit_amount']:.2f}")
    print(f"    remaining : ₹{food_status['remaining']:.2f}")
    print(f"    used      : {food_status['percentage_used']*100:.1f}%")
    print(f"    alert     : {food_status['alert_level'].upper()}")

    transport_status = get_budget_status(transport_id, current_month)
    print(f"  Transport:")
    print(f"    spent     : ₹{transport_status['spent']:.2f}")
    print(f"    limit     : ₹{transport_status['limit_amount']:.2f}")
    print(f"    remaining : ₹{transport_status['remaining']:.2f}")
    print(f"    used      : {transport_status['percentage_used']*100:.1f}%")
    print(f"    alert     : {transport_status['alert_level'].upper()}")

    # -----------------------------------------------------------------
    section("7. Cleanup (delete test rows)")
    # -----------------------------------------------------------------
    for eid in (e1, e2, e3):
        deleted = delete_expense(eid)
        assert deleted is True
    print(f"✓ Deleted 3 test expenses")

    delete_budget(food_id, current_month)
    delete_budget(transport_id, current_month)
    print(f"✓ Deleted 2 test budgets")

    # -----------------------------------------------------------------
    print("\n🎉 All database operations passed.\n")


if __name__ == "__main__":
    main()