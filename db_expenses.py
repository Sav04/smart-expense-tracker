"""
Expense-related database functions.

This is the data layer for the core 'expenses' table. All inserts,
updates, deletes, and reads on expenses go through here.
"""

from typing import Optional
from datetime import date
import sqlite3

from database import get_connection


# ---------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------

def add_expense(
    amount: float,
    description: str,
    category_id: int,
    expense_date: date,
    merchant: Optional[str] = None,
    source: str = "manual",
    raw_sms: Optional[str] = None,
) -> int:
    """
    Insert a new expense row.

    Args:
        amount: Rupee value, must be > 0.
        description: Human-readable expense description (used by ML).
        category_id: FK to categories table.
        expense_date: When the expense actually happened.
        merchant: Optional cleaner merchant name (e.g., "Swiggy").
        source: Either 'manual' or 'sms'.
        raw_sms: Original SMS text if source='sms', else None.

    Returns:
        The id of the newly inserted expense row.

    Raises:
        sqlite3.IntegrityError: If a CHECK or FOREIGN KEY fails
        (e.g., negative amount, invalid category_id, invalid source).
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO expenses
                (amount, description, category_id, expense_date,
                 merchant, source, raw_sms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                amount,
                description,
                category_id,
                expense_date.isoformat(),  # convert date to "YYYY-MM-DD"
                merchant,
                source,
                raw_sms,
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


# ---------------------------------------------------------------------
# READ
# ---------------------------------------------------------------------

def get_all_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
) -> list[sqlite3.Row]:
    """
    Fetch expenses, optionally filtered by date range and/or category.

    Each returned row joins category info, so you get category name,
    icon, and color directly without a second query.

    Args:
        start_date: Inclusive lower bound on expense_date.
        end_date:   Inclusive upper bound on expense_date.
        category_id: Filter to a single category.

    Returns:
        list of sqlite3.Row, ordered by expense_date DESC then id DESC
        (most recent first). Empty list if no matches.
    """
    # Build the query dynamically based on which filters were given.
    query = """
        SELECT
            e.id, e.amount, e.description, e.category_id,
            e.expense_date, e.merchant, e.source, e.raw_sms,
            e.created_at,
            c.name AS category_name,
            c.icon AS category_icon,
            c.color AS category_color
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE 1=1
    """
    params: list = []

    if start_date is not None:
        query += " AND e.expense_date >= ?"
        params.append(start_date.isoformat())

    if end_date is not None:
        query += " AND e.expense_date <= ?"
        params.append(end_date.isoformat())

    if category_id is not None:
        query += " AND e.category_id = ?"
        params.append(category_id)

    query += " ORDER BY e.expense_date DESC, e.id DESC"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        conn.close()


def get_expense_by_id(expense_id: int) -> Optional[sqlite3.Row]:
    """Fetch one expense by its id, with category info joined in."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id, e.amount, e.description, e.category_id,
                e.expense_date, e.merchant, e.source, e.raw_sms,
                e.created_at,
                c.name AS category_name,
                c.icon AS category_icon,
                c.color AS category_color
            FROM expenses e
            JOIN categories c ON e.category_id = c.id
            WHERE e.id = ?
            """,
            (expense_id,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


# ---------------------------------------------------------------------
# UPDATE
# ---------------------------------------------------------------------

def update_expense(
    expense_id: int,
    amount: Optional[float] = None,
    description: Optional[str] = None,
    category_id: Optional[int] = None,
    expense_date: Optional[date] = None,
    merchant: Optional[str] = None,
) -> bool:
    """
    Update specific fields of an existing expense. Only the fields
    you pass (non-None) will be updated; others stay as-is.

    Returns:
        True if a row was updated, False if no expense with that id.
    """
    # Collect only the fields the caller actually wants to change.
    updates: list[str] = []
    params: list = []

    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    if description is not None:
        updates.append("description = ?")
        params.append(description)
    if category_id is not None:
        updates.append("category_id = ?")
        params.append(category_id)
    if expense_date is not None:
        updates.append("expense_date = ?")
        params.append(expense_date.isoformat())
    if merchant is not None:
        updates.append("merchant = ?")
        params.append(merchant)

    # If nothing was passed, nothing to do.
    if not updates:
        return False

    params.append(expense_id)  # for the WHERE clause
    query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


# ---------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------

def delete_expense(expense_id: int) -> bool:
    """
    Delete an expense by id.

    Returns:
        True if a row was deleted, False if no match.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()