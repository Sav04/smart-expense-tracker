"""
Smart Expense Tracker — main Streamlit app.

This is intentionally a single-file UI for now. As the project grows
(SMS parser, charts, budgets), we'll split it into modules.
"""

from datetime import date

import streamlit as st

from db_categories import get_all_categories
from db_expenses import add_expense, get_all_expenses
from classifier import predict_category, predict_top_k, is_model_available


# =====================================================================
# UI helpers
# =====================================================================

def render_header() -> None:
    """Page title and tagline."""
    st.title("💰 Smart Expense Tracker")
    st.caption("Personal expense tracker — INR only · ML-powered categorization")


def render_sidebar() -> None:
    """Sidebar with quick stats. Re-computed on every rerun."""
    with st.sidebar:
        st.header("📊 Quick Stats")

        expenses = get_all_expenses()

        if not expenses:
            st.metric("Total Expenses", "₹0.00")
            st.caption("Add your first expense to see stats here.")
        else:
            today_iso = date.today().isoformat()
            today_total = sum(
                e["amount"] for e in expenses if e["expense_date"] == today_iso
            )
            all_time_total = sum(e["amount"] for e in expenses)

            st.metric("Today", f"₹{today_total:,.2f}")
            st.metric("All-Time Total", f"₹{all_time_total:,.2f}")
            st.metric("Number of Expenses", f"{len(expenses):,}")

        # ML model status indicator
        st.divider()
        if is_model_available():
            st.caption("🤖 Auto-categorization: **active**")
        else:
            st.caption("⚠️ Train the model to enable auto-categorization")


def render_add_expense_form() -> None:
    """
    Add Expense form with live ML categorization.

    Architecture note:
      - Description input lives OUTSIDE the form so we can run a
        prediction on every rerun (description change → rerun → predict).
      - The rest of the fields live INSIDE st.form for clean batching
        and clear-on-submit behavior.
    """
    st.subheader("➕ Add Expense")

    # Pull categories for the dropdown.
    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }

    # ----- Description (outside form, enables live prediction) -----
    description = st.text_input(
        "Description",
        placeholder="e.g. Lunch at Swiggy, Uber to college",
        key="expense_description",
        help="Type a description and we'll auto-suggest the category.",
    )

    # ----- Live ML prediction display ------------------------------
    predicted_label: str | None = None  # used to pre-select the dropdown

    if description.strip() and is_model_available():
        result = predict_category(description.strip())
        if result is not None:
            label = f"{result['category_icon']} {result['category_name']}"
            confidence = result["confidence"]

            if confidence >= 0.60:
                # High confidence: auto-fill silently with green tag
                st.success(
                    f"🤖 **{label}**  ·  {confidence:.0%} confident"
                )
                predicted_label = label

            elif confidence >= 0.30:
                # Medium confidence: auto-fill with a "please confirm" nudge
                st.info(
                    f"🤔 Best guess: **{label}**  ·  "
                    f"{confidence:.0%} sure — please confirm"
                )
                predicted_label = label

            else:
                # Low confidence: DON'T auto-fill; show top-3 alternatives
                top3 = predict_top_k(description.strip(), k=3)
                chips = "  ·  ".join(
                    f"{r['category_icon']} **{r['category_name']}** "
                    f"({r['confidence']:.0%})"
                    for r in top3
                )
                st.warning(f"🎯 Not sure — top guesses: {chips}")
                # predicted_label stays None → dropdown defaults to first

    elif description.strip() and not is_model_available():
        st.caption(
            "💡 Run `python train_classifier.py` to enable auto-categorization."
        )

    # ----- The rest of the fields (inside form) --------------------
    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            amount = st.number_input(
                "Amount (₹)",
                min_value=0.0,
                step=10.0,
                format="%.2f",
            )
            merchant = st.text_input(
                "Merchant (optional)",
                placeholder="e.g. Swiggy, Uber, BSNL",
            )

        with col2:
            # Pre-select the predicted category if confidence was high enough.
            default_index = 0
            if predicted_label and predicted_label in cat_options:
                default_index = cat_options.index(predicted_label)

            category_label = st.selectbox(
                "Category",
                options=cat_options,
                index=default_index,
                help="Auto-filled from ML prediction; override anytime.",
            )
            expense_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
            )

        submitted = st.form_submit_button("Add Expense", type="primary")

        if submitted:
            if amount <= 0:
                st.error("Amount must be greater than 0.")
                return
            if not description.strip():
                st.error("Please enter a description above.")
                return

            expense_id = add_expense(
                amount=amount,
                description=description.strip(),
                category_id=cat_label_to_id[category_label],
                expense_date=expense_date,
                merchant=merchant.strip() if merchant.strip() else None,
                source="manual",
            )
            st.success(
                f"✓ Added expense #{expense_id}: {description.strip()}  "
                f"({category_label}, ₹{amount:,.2f})"
            )


def render_recent_expenses() -> None:
    """Show the 20 most recent expenses in a table."""
    st.subheader("📋 Recent Expenses")

    expenses = get_all_expenses()

    if not expenses:
        st.info("No expenses yet. Add one above to get started.")
        return

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