"""
Category-related database functions.

Categories are seeded once by init_db.py and rarely change. This module
exposes read-only helpers to fetch them — used by dropdowns, charts,
and the ML classifier (to map predicted labels back to category IDs).
"""

from typing import Optional
import sqlite3

from database import get_connection


def get_all_categories() -> list[sqlite3.Row]:
    """
    Fetch all categories, ordered by id.

    Returns:
        list of sqlite3.Row objects. Each row has keys:
        'id', 'name', 'icon', 'color'.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, icon, color FROM categories ORDER BY id"
        )
        return cursor.fetchall()
    finally:
        conn.close()


def get_category_by_id(category_id: int) -> Optional[sqlite3.Row]:
    """
    Fetch one category by its id.

    Args:
        category_id: The category's primary key.

    Returns:
        sqlite3.Row if found, otherwise None.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, icon, color FROM categories WHERE id = ?",
            (category_id,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def get_category_by_name(name: str) -> Optional[sqlite3.Row]:
    """
    Fetch one category by its name (case-sensitive exact match).

    Useful for the ML classifier: predicted label → category row.

    Args:
        name: The exact category name (e.g. "Food & Dining").

    Returns:
        sqlite3.Row if found, otherwise None.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, name, icon, color FROM categories WHERE name = ?",
            (name,),
        )
        return cursor.fetchone()
    finally:
        conn.close()