"""
Smart Expense Tracker — main Streamlit app.

Two ways to add expenses, both writing to the same database:
  - 📱 Paste Bank SMS: regex parser extracts fields, classifier suggests category
  - ✍️ Manual Entry: classifier suggests category as you type description
"""

from datetime import date

import streamlit as st

from db_categories import get_all_categories
from db_expenses import add_expense, get_all_expenses
from classifier import predict_category, predict_top_k, is_model_available
from sms_parser import parse_sms


# =====================================================================
# UI helpers
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
            st.caption(f"📱 {sms_imported} from SMS  ·  ✍️ {len(expenses) - sms_imported} manual")

        st.divider()
        if is_model_available():
            st.caption("🤖 Auto-categorization: **active**")
        else:
            st.caption("⚠️ Train the model to enable auto-categorization")


# =====================================================================
# SMS import flow
# =====================================================================

def render_sms_import() -> None:
    """Paste bank SMS → auto-parse → preview → confirm → save."""

    # If a previous submission requested clearing, reset before widget creation.
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

    # ----- Auto-parse on every rerun -------------------------------
    result = parse_sms(sms_text)

    if result is None:
        st.error(
            "⚠️ Couldn't parse this SMS format. "
            "Try the **✍️ Manual Entry** tab, or check that the SMS is "
            "a real transaction (not OTP, balance check, etc.)."
        )
        return

    # ----- Successfully parsed: classify and show preview ----------
    prediction = (
        predict_category(result["merchant"])
        if is_model_available()
        else None
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

    # ----- Category override + confirm -----------------------------
    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }

    default_index = 0
    if prediction:
        predicted_label = (
            f"{prediction['category_icon']} {prediction['category_name']}"
        )
        if predicted_label in cat_options:
            default_index = cat_options.index(predicted_label)

    category_label = st.selectbox(
        "Confirm category (override if wrong)",
        options=cat_options,
        index=default_index,
        key="sms_category_select",
    )

    if st.button("✅ Add to Expenses", type="primary", key="sms_add_btn"):
        expense_id = add_expense(
            amount=result["amount"],
            description=result["merchant"],   # use merchant as description
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

        # Schedule clearing the textarea on the next rerun
        st.session_state["_should_clear_sms"] = True
        st.rerun()


# =====================================================================
# Manual entry flow (unchanged from Phase 3.5)
# =====================================================================

def render_add_expense_form() -> None:
    """Manual entry form with live ML classification."""
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
            if confidence >= 0.60:
                st.success(f"🤖 **{label}**  ·  {confidence:.0%} confident")
                predicted_label = label
            elif confidence >= 0.30:
                st.info(
                    f"🤔 Best guess: **{label}**  ·  "
                    f"{confidence:.0%} sure — please confirm"
                )
                predicted_label = label
            else:
                top3 = predict_top_k(description.strip(), k=3)
                chips = "  ·  ".join(
                    f"{r['category_icon']} **{r['category_name']}** "
                    f"({r['confidence']:.0%})"
                    for r in top3
                )
                st.warning(f"🎯 Not sure — top guesses: {chips}")
    elif description.strip() and not is_model_available():
        st.caption(
            "💡 Run `python train_classifier.py` to enable auto-categorization."
        )

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
# Recent expenses
# =====================================================================

def render_recent_expenses() -> None:
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

    st.subheader("➕ Add Expense")

    tab_sms, tab_manual = st.tabs(["📱 Paste Bank SMS", "✍️ Manual Entry"])
    with tab_sms:
        render_sms_import()
    with tab_manual:
        render_add_expense_form()

    st.divider()
    render_recent_expenses()


if __name__ == "__main__":
    main()