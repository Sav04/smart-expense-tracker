"""
User category corrections — captures cases where the user overrode
the classifier's prediction. These get merged with the seed training
data on retraining, creating an active-learning feedback loop.
"""

from typing import Optional
import sqlite3

from database import get_connection


def add_correction(description: str, category_id: int) -> int:
    """
    Record a user override as a labeled training example.

    Args:
        description: The text the user typed (or merchant from SMS).
        category_id: The category they ultimately picked.

    Returns:
        id of the new correction row, or -1 if description was empty.
    """
    if not description or not description.strip():
        return -1

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO corrections (description, category_id) "
            "VALUES (?, ?)",
            (description.strip(), category_id),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_corrections() -> list[sqlite3.Row]:
    """Fetch all corrections joined with category names, newest first."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT c.id, c.description, c.category_id, c.created_at,
                   cat.name AS category_name
            FROM corrections c
            JOIN categories cat ON c.category_id = cat.id
            ORDER BY c.created_at DESC
            """
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_correction_count() -> int:
    """Total corrections recorded so far."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM corrections")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def clear_all_corrections() -> int:
    """Delete ALL corrections. Returns count deleted."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM corrections")
        n = cursor.fetchone()[0]
        cursor.execute("DELETE FROM corrections")
        conn.commit()
        return n
    finally:
        conn.close()