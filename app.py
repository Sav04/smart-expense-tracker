"""
Smart Expense Tracker — main Streamlit app.

This is intentionally a single-file UI for now. As the project grows
(SMS parser, ML classifier, charts, budgets), we'll split it into
modules. Premature splitting is worse than a 200-line file.
"""

from datetime import date

import streamlit as st

from db_categories import get_all_categories
from db_expenses import add_expense, get_all_expenses


# =====================================================================
# UI helpers — each function renders one part of the page.
# Streamlit reruns the whole script on every interaction, so these
# functions are called fresh every time. No state to manage.
# =====================================================================

def render_header() -> None:
    """Page title and tagline."""
    st.title("💰 Smart Expense Tracker")
    st.caption("Personal expense tracker — INR only")


def render_sidebar() -> None:
    """Sidebar with quick stats. Re-computed on every rerun."""
    with st.sidebar:
        st.header("📊 Quick Stats")

        expenses = get_all_expenses()

        if not expenses:
            st.metric("Total Expenses", "₹0.00")
            st.caption("Add your first expense to see stats here.")
            return

        today_iso = date.today().isoformat()
        today_total = sum(e["amount"] for e in expenses if e["expense_date"] == today_iso)
        all_time_total = sum(e["amount"] for e in expenses)

        st.metric("Today", f"₹{today_total:,.2f}")
        st.metric("All-Time Total", f"₹{all_time_total:,.2f}")
        st.metric("Number of Expenses", f"{len(expenses):,}")


def render_add_expense_form() -> None:
    """The 'Add Expense' form. Submitting inserts a row and reruns."""
    st.subheader("➕ Add Expense")

    # Pull categories so we can show them in the dropdown.
    # Map "🍔 Food & Dining" → id, so we can recover the id post-submit.
    categories = get_all_categories()
    category_label_to_id = {
        f"{c['icon']} {c['name']}": c["id"] for c in categories
    }

    with st.form("add_expense_form", clear_on_submit=True):
        # Two-column layout for the main inputs
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
            )
            description = st.text_input(
                "Description",
                placeholder="e.g. Lunch at Swiggy",
            )

        with col2:
            category_label = st.selectbox(
                "Category",
                options=list(category_label_to_id.keys()),
            )
            expense_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),  # disallow future dates
            )

        merchant = st.text_input(
            "Merchant (optional)",
            placeholder="e.g. Swiggy, Uber, BSNL",
        )

        submitted = st.form_submit_button("Add Expense", type="primary")

        if submitted:
            # Validation — fail loudly with helpful messages
            if amount <= 0:
                st.error("Amount must be greater than 0.")
                return
            if not description.strip():
                st.error("Please enter a description.")
                return

            # All good — insert and confirm
            expense_id = add_expense(
                amount=amount,
                description=description.strip(),
                category_id=category_label_to_id[category_label],
                expense_date=expense_date,
                merchant=merchant.strip() if merchant.strip() else None,
                source="manual",
            )
            st.success(f"✓ Added expense #{expense_id}: {description.strip()}")


def render_recent_expenses() -> None:
    """Show the 20 most recent expenses in a table."""
    st.subheader("📋 Recent Expenses")

    expenses = get_all_expenses()

    if not expenses:
        st.info("No expenses yet. Add one above to get started.")
        return

    # Reshape Row objects into a list of dicts that st.dataframe likes
    display_rows = [
        {
            "Date": e["expense_date"],
            "Category": f"{e['category_icon']} {e['category_name']}",
            "Description": e["description"],
            "Merchant": e["merchant"] or "—",
            "Amount": f"₹{e['amount']:,.2f}",
            "Source": "📱 SMS" if e["source"] == "sms" else "✍️ Manual",
        }
        for e in expenses[:20]
    ]

    st.dataframe(display_rows, hide_index=True, use_container_width=True)

    if len(expenses) > 20:
        st.caption(f"Showing 20 of {len(expenses):,} expenses.")


# =====================================================================
# Main entry point
# =====================================================================

def main() -> None:
    st.set_page_config(
        page_title="Smart Expense Tracker",
        page_icon="💰",
        layout="wide",
    )

    render_header()
    render_sidebar()
    render_add_expense_form()
    st.divider()
    render_recent_expenses()


if __name__ == "__main__":
    main()