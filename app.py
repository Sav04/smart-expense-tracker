"""
Smart Expense Tracker — main Streamlit app.

Top-level tabs:
  - 📋 Track Expenses: add (SMS/manual) + recent list
  - 📊 Dashboard: filtered analytics with charts and KPIs
"""

from datetime import date, timedelta, datetime

import streamlit as st

from db_categories import get_all_categories
from db_expenses import add_expense, get_all_expenses, delete_expense
from classifier import predict_category, predict_top_k, is_model_available
from sms_parser import parse_sms
from visualization import (
    build_category_pie,
    build_top_merchants,
    build_spending_trend,
)


# =====================================================================
# Header & sidebar (unchanged)
# =====================================================================

def render_header() -> None:
    st.title("💰 Smart Expense Tracker")
    st.caption(
        "Personal expense tracker — INR only · "
        "ML-powered categorization · SMS auto-import"
    )


def render_sidebar() -> None:
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
            sms_imported = sum(1 for e in expenses if e["source"] == "sms")

            st.metric("Today", f"₹{today_total:,.2f}")
            st.metric("All-Time Total", f"₹{all_time_total:,.2f}")
            st.metric("Number of Expenses", f"{len(expenses):,}")
            st.caption(
                f"📱 {sms_imported} from SMS  ·  "
                f"✍️ {len(expenses) - sms_imported} manual"
            )

        st.divider()
        if is_model_available():
            st.caption("🤖 Auto-categorization: **active**")
        else:
            st.caption("⚠️ Train the model to enable auto-categorization")


# =====================================================================
# SMS import flow (unchanged)
# =====================================================================

def render_sms_import() -> None:
    if st.session_state.get("_should_clear_sms"):
        st.session_state["sms_text_input"] = ""
        st.session_state["_should_clear_sms"] = False

    st.markdown(
        "Paste an Indian bank or UPI SMS below. The app will auto-extract "
        "amount, merchant, date, and suggest a category."
    )

    sms_text = st.text_area(
        "Bank/UPI SMS",
        placeholder=(
            "Example:\nRs.450.00 has been debited from your a/c XX1234 "
            "on 28-Apr-26 at SWIGGY*BANGALORE. Avbl bal: Rs.12,340.00"
        ),
        height=130,
        key="sms_text_input",
        label_visibility="collapsed",
    )

    if not sms_text.strip():
        st.caption(
            "💡 Tip: Forward your bank's transaction SMS to yourself, "
            "then copy-paste here for instant logging."
        )
        return

    result = parse_sms(sms_text)

    if result is None:
        st.error(
            "⚠️ Couldn't parse this SMS format. "
            "Try the **✍️ Manual Entry** tab, or check that the SMS is "
            "a real transaction (not OTP, balance check, etc.)."
        )
        return

    prediction = (
        predict_category(result["merchant"]) if is_model_available() else None
    )

    st.divider()
    st.markdown("### 📋 Detected from SMS")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Amount", f"₹{result['amount']:,.2f}")
    with col2:
        st.metric("Date", result["date"].strftime("%d %b %Y"))
    with col3:
        if prediction:
            confidence_emoji = (
                "🟢" if prediction["confidence"] >= 0.60
                else "🟡" if prediction["confidence"] >= 0.30
                else "🔴"
            )
            st.metric(
                "Suggested category",
                f"{prediction['category_icon']} {prediction['category_name']}",
                delta=f"{confidence_emoji} {prediction['confidence']:.0%}",
                delta_color="off",
            )
        else:
            st.metric("Category", "Pick below")

    st.markdown(f"**Merchant:** `{result['merchant']}`")

    with st.expander("View original SMS"):
        st.code(result["raw_sms"], language=None)

    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }

    # Decide what the dropdown SHOULD show.
    suggested_sms = cat_options[0]
    if prediction:
        predicted_label = (
            f"{prediction['category_icon']} {prediction['category_name']}"
        )
        if predicted_label in cat_options:
            suggested_sms = predicted_label

    # Sync widget state when prediction changes (different SMS → different
    # merchant → different prediction). User overrides persist until the
    # prediction changes again.
    last_sms_suggestion = st.session_state.get("_last_sms_suggestion")
    if suggested_sms != last_sms_suggestion:
        st.session_state["sms_category_select"] = suggested_sms
        st.session_state["_last_sms_suggestion"] = suggested_sms

    category_label = st.selectbox(
        "Confirm category (override if wrong)",
        options=cat_options,
        key="sms_category_select",
    )

    if st.button("✅ Add to Expenses", type="primary", key="sms_add_btn"):
        expense_id = add_expense(
            amount=result["amount"],
            description=result["merchant"],
            category_id=cat_label_to_id[category_label],
            expense_date=result["date"],
            merchant=result["merchant"],
            source="sms",
            raw_sms=result["raw_sms"],
        )
        st.success(
            f"✓ Added expense #{expense_id}: "
            f"{result['merchant']} (₹{result['amount']:,.2f})"
        )
        st.session_state["_should_clear_sms"] = True
        st.rerun()


# =====================================================================
# Manual entry flow (unchanged)
# =====================================================================

def render_add_expense_form() -> None:
    if st.session_state.get("_should_clear_description"):
        st.session_state["expense_description"] = ""
        st.session_state["_should_clear_description"] = False

    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }

    description = st.text_input(
        "Description",
        placeholder="e.g. Lunch at Swiggy, Uber to college",
        key="expense_description",
        help="Type a description and we'll auto-suggest the category.",
    )

    predicted_label: str | None = None

    if description.strip() and is_model_available():
        result = predict_category(description.strip())
        if result is not None:
            label = f"{result['category_icon']} {result['category_name']}"
            confidence = result["confidence"]
            # Always auto-fill the dropdown with the top prediction, regardless
            # of confidence. The confidence indicator below tells the user how
            # trustworthy it is; the dropdown is one click away from override.
            predicted_label = label
            
            if confidence >= 0.60:
                st.success(f"🤖 **{label}**  ·  {confidence:.0%} confident")
            elif confidence >= 0.30:
                st.info(
                    f"🤔 Best guess: **{label}**  ·  "
                    f"{confidence:.0%} sure — please confirm"
                )
            else:
                top3 = predict_top_k(description.strip(), k=3)
                chips = "  ·  ".join(
                    f"{r['category_icon']} **{r['category_name']}** "
                    f"({r['confidence']:.0%})"
                    for r in top3
                )
                st.warning(f"🎯 Not sure — top guesses: {chips}")

    with st.form("add_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input(
                "Amount (₹)", min_value=0.0, step=10.0, format="%.2f",
            )
            merchant = st.text_input(
                "Merchant (optional)",
                placeholder="e.g. Swiggy, Uber, BSNL",
            )
        with col2:
            # Decide what the dropdown SHOULD show right now.
            suggested = (
                predicted_label
                if (predicted_label and predicted_label in cat_options)
                else cat_options[0]
            )

            # If the suggestion changed since the last render, sync the
            # widget's stored value. This makes new predictions auto-fill the
            # dropdown — Streamlit ignores `index=` once the widget has state.
            last_suggestion = st.session_state.get("_last_manual_suggestion")
            if suggested != last_suggestion:
                st.session_state["manual_cat_select"] = suggested
                st.session_state["_last_manual_suggestion"] = suggested

            category_label = st.selectbox(
                "Category",
                options=cat_options,
                key="manual_cat_select",
                help="Auto-filled from ML prediction; override anytime.",
            )
            expense_date = st.date_input(
                "Date", value=date.today(), max_value=date.today(),
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


# =====================================================================
# Recent expenses (unchanged)
# =====================================================================

def render_recent_expenses() -> None:
    """Recent expenses with period filter and per-row delete buttons."""
    st.subheader("📋 Recent Expenses")

    all_expenses = get_all_expenses()

    if not all_expenses:
        st.info("No expenses yet. Add one above to get started.")
        return

    # ----- Filter row ---------------------------------------------
    col_filter, col_summary = st.columns([1, 3])
    with col_filter:
        period = st.selectbox(
            "Show",
            ["All Time", "This Month", "Last 30 Days", "Last 90 Days"],
            key="recent_period",
        )

    expenses = _filter_expenses_by_period(all_expenses, period)

    if not expenses:
        st.warning(f"No expenses in **{period}**.")
        return

    # Summary inline next to the filter
    with col_summary:
        st.write("")  # vertical spacer to align with the dropdown
        total = sum(e["amount"] for e in expenses)
        st.caption(
            f"📊 **{len(expenses)}** expenses · "
            f"**₹{total:,.2f}** total"
        )

    st.divider()

    # ----- Header row ---------------------------------------------
    # Column proportions: Date | Category | Description | Amount | Action
    cols = st.columns([2, 3, 4, 2, 1])
    cols[0].markdown("**Date**")
    cols[1].markdown("**Category**")
    cols[2].markdown("**Description**")
    cols[3].markdown("**Amount**")
    cols[4].markdown("")  # blank for delete column

    # ----- Data rows ----------------------------------------------
    visible = expenses[:30]  # cap to keep the page snappy

    for e in visible:
        cols = st.columns([2, 3, 4, 2, 1])

        cols[0].write(e["expense_date"])
        cols[1].write(f"{e['category_icon']} {e['category_name']}")

        # Show description; if merchant differs, append it as italic
        desc = e["description"]
        merchant = e["merchant"]
        if merchant and merchant.lower() != desc.lower():
            desc = f"{desc}  ·  *{merchant}*"
        cols[2].write(desc)

        # Combine source icon with amount in one cell
        source_icon = "📱" if e["source"] == "sms" else "✍️"
        cols[3].write(f"{source_icon} ₹{e['amount']:,.2f}")

        with cols[4]:
            if st.button(
                "🗑️",
                key=f"del_{e['id']}",
                help=f"Delete expense #{e['id']}",
            ):
                delete_expense(e["id"])
                st.rerun()

    if len(expenses) > 30:
        st.caption(f"Showing 30 of {len(expenses):,} expenses.")

# =====================================================================
# Dashboard (NEW)
# =====================================================================

def _filter_expenses_by_period(expenses: list, period: str) -> list:
    """Filter expenses based on the selected time period."""
    if period == "All Time" or not expenses:
        return expenses

    today = date.today()
    if period == "This Month":
        cutoff = today.replace(day=1)
    elif period == "Last 30 Days":
        cutoff = today - timedelta(days=30)
    elif period == "Last 90 Days":
        cutoff = today - timedelta(days=90)
    else:
        return expenses

    cutoff_iso = cutoff.isoformat()
    return [e for e in expenses if e["expense_date"] >= cutoff_iso]


def render_dashboard() -> None:
    st.subheader("📊 Spending Dashboard")

    all_expenses = get_all_expenses()

    if not all_expenses:
        st.info(
            "No expenses yet. Add some in the **📋 Track Expenses** tab "
            "to see your dashboard come alive."
        )
        return

    # ----- Period filter ------------------------------------------
    period = st.selectbox(
        "Period",
        ["This Month", "Last 30 Days", "Last 90 Days", "All Time"],
        index=0,
    )
    expenses = _filter_expenses_by_period(all_expenses, period)

    if not expenses:
        st.warning(
            f"No expenses in **{period}**. "
            f"Try a wider range, or add some expenses."
        )
        return

    # ----- KPI row ------------------------------------------------
    total_spent = sum(e["amount"] for e in expenses)
    n_transactions = len(expenses)

    # Date span for "average per day"
    dates = sorted({e["expense_date"] for e in expenses})
    first_d = datetime.strptime(dates[0], "%Y-%m-%d").date()
    last_d = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    days_span = max((last_d - first_d).days + 1, 1)
    avg_per_day = total_spent / days_span

    # Top category
    cat_totals: dict[str, float] = {}
    for e in expenses:
        key = f"{e['category_icon']} {e['category_name']}"
        cat_totals[key] = cat_totals.get(key, 0) + e["amount"]
    top_cat_label, top_cat_amount = max(cat_totals.items(), key=lambda x: x[1])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Spent", f"₹{total_spent:,.2f}")
    with col2:
        st.metric("Transactions", f"{n_transactions:,}")
    with col3:
        st.metric("Avg / day", f"₹{avg_per_day:,.2f}")
    with col4:
        st.metric(
            "Top Category",
            top_cat_label,
            delta=f"₹{top_cat_amount:,.2f}",
            delta_color="off",
        )

    st.divider()

    # ----- Charts row 1: pie + top merchants ----------------------
    col_left, col_right = st.columns([2, 3])
    with col_left:
        fig = build_category_pie(expenses)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
    with col_right:
        fig = build_top_merchants(expenses, n=10)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)

    # ----- Chart row 2: trend line --------------------------------
    fig = build_spending_trend(expenses)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True)


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

    tab_track, tab_dashboard = st.tabs(["📋 Track Expenses", "📊 Dashboard"])

    with tab_track:
        st.subheader("➕ Add Expense")
        tab_sms, tab_manual = st.tabs(["📱 Paste Bank SMS", "✍️ Manual Entry"])
        with tab_sms:
            render_sms_import()
        with tab_manual:
            render_add_expense_form()
        st.divider()
        render_recent_expenses()

    with tab_dashboard:
        render_dashboard()


if __name__ == "__main__":
    main()