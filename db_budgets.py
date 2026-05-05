"""
Budget-related database functions.

Budgets are per-category, per-month caps with configurable alert
thresholds. The headline function here is get_budget_status(), which
computes spent vs. limit and assigns an alert level.
"""

from typing import Optional
from datetime import date
import sqlite3

from database import get_connection


# ---------------------------------------------------------------------
# CREATE / UPDATE (combined — "upsert")
# ---------------------------------------------------------------------

def set_budget(
    category_id: int,
    month: str,
    limit_amount: float,
    alert_threshold: float = 0.8,
) -> int:
    """
    Create or update a budget for a (category, month) pair.

    If a budget already exists for that pair, it gets overwritten
    (the UNIQUE constraint guarantees only one budget per pair).

    Args:
        category_id: FK to categories.
        month: "YYYY-MM" string, e.g. "2026-04".
        limit_amount: Rupee cap.
        alert_threshold: Fraction (0.0–1.0) at which to warn.

    Returns:
        The id of the budget row (new or existing).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        # ON CONFLICT lets us "upsert" — insert or update.
        # We tell SQLite: if (category_id, month) collides, update
        # the limit and threshold instead of erroring.
        cursor.execute(
            """
            INSERT INTO budgets (category_id, month, limit_amount, alert_threshold)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(category_id, month) DO UPDATE SET
                limit_amount = excluded.limit_amount,
                alert_threshold = excluded.alert_threshold
            """,
            (category_id, month, limit_amount, alert_threshold),
        )
        conn.commit()

        # Get the row's id (whether inserted or updated)
        cursor.execute(
            "SELECT id FROM budgets WHERE category_id = ? AND month = ?",
            (category_id, month),
        )
        return cursor.fetchone()["id"]
    finally:
        conn.close()


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------

def get_budget(category_id: int, month: str) -> Optional[sqlite3.Row]:
    """Fetch a single budget by (category, month). None if not set."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, category_id, month, limit_amount, alert_threshold
            FROM budgets
            WHERE category_id = ? AND month = ?
            """,
            (category_id, month),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_all_budgets_for_month(month: str) -> list[sqlite3.Row]:
    """
    Fetch every budget set for a given month, joined with category info.

    Args:
        month: "YYYY-MM" string.

    Returns:
        list of sqlite3.Row with budget + category fields.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                b.id, b.category_id, b.month, b.limit_amount, b.alert_threshold,
                c.name AS category_name,
                c.icon AS category_icon,
                c.color AS category_color
            FROM budgets b
            JOIN categories c ON b.category_id = c.id
            WHERE b.month = ?
            ORDER BY c.id
            """,
            (month,),
        )
        return cursor.fetchall()
    finally:
        conn.close()


# ---------------------------------------------------------------------
# THE HEADLINE FUNCTION — budget status with alert level
# ---------------------------------------------------------------------

def get_budget_status(category_id: int, month: str) -> Optional[dict]:
    """
    Compute the live status of a budget: spent, remaining, percentage,
    and alert level.

    Args:
        category_id: FK to categories.
        month: "YYYY-MM" string.

    Returns:
        dict with keys:
          - 'limit_amount'     : the budget cap (float)
          - 'spent'            : sum of expenses in this category+month
          - 'remaining'        : limit_amount - spent (can be negative)
          - 'percentage_used'  : spent / limit_amount, as 0.0–1.0+
          - 'alert_threshold'  : the warn-at threshold (0.0–1.0)
          - 'alert_level'      : 'safe' | 'warning' | 'exceeded'
        Returns None if no budget is set for that (category, month).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # Step 1: fetch the budget row
        cursor.execute(
            """
            SELECT limit_amount, alert_threshold
            FROM budgets
            WHERE category_id = ? AND month = ?
            """,
            (category_id, month),
        )
        budget = cursor.fetchone()
        if budget is None:
            return None

        limit_amount = budget["limit_amount"]
        alert_threshold = budget["alert_threshold"]

        # Step 2: sum the expenses in that category+month
        # SQLite's strftime('%Y-%m', date) extracts the YYYY-MM part,
        # so we can match it against the budget's `month` column.
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total_spent
            FROM expenses
            WHERE category_id = ?
              AND strftime('%Y-%m', expense_date) = ?
            """,
            (category_id, month),
        )
        spent = cursor.fetchone()["total_spent"]

        # Step 3: compute derived values
        remaining = limit_amount - spent
        percentage_used = spent / limit_amount  # safe: limit > 0 guaranteed by CHECK

        # Step 4: assign an alert level
        if percentage_used >= 1.0:
            alert_level = "exceeded"
        elif percentage_used >= alert_threshold:
            alert_level = "warning"
        else:
            alert_level = "safe"

        return {
            "limit_amount": limit_amount,
            "spent": spent,
            "remaining": remaining,
            "percentage_used": percentage_used,
            "alert_threshold": alert_threshold,
            "alert_level": alert_level,
        }
    finally:
        conn.close()


# ---------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------

def delete_budget(category_id: int, month: str) -> bool:
    """Delete a budget. Returns True if a row was deleted."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM budgets WHERE category_id = ? AND month = ?",
            (category_id, month),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()