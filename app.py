"""
Smart Expense Tracker — main Streamlit app.

Three top-level tabs:
  - 📋 Track Expenses: add (SMS/manual) + recent list with delete
  - 📊 Dashboard: filtered analytics with charts and KPIs
  - 💰 Budgets: per-category monthly limits with alerts
"""
from seed_demo_data import seed_demo_data, clear_all_data, unmark_seeded
from datetime import date, timedelta, datetime

import streamlit as st
from db_corrections import add_correction, get_correction_count
from train_classifier import train as run_training
from classifier import invalidate_cache
from db_categories import get_all_categories
from db_expenses import add_expense, get_all_expenses, delete_expense
from db_budgets import set_budget, get_budget_status, delete_budget
from classifier import predict_category, predict_top_k, is_model_available
from sms_parser import parse_sms
from visualization import (
    build_category_pie,
    build_top_merchants,
    build_spending_trend,
)


# =====================================================================
# Helpers (module-level)
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


def _get_month_options(today: date, n_months: int = 12) -> list[str]:
    """Generate a list of 'YYYY-MM' strings for the current and past months."""
    months = []
    year, month = today.year, today.month
    for _ in range(n_months):
        months.append(f"{year:04d}-{month:02d}")
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    return months


def _format_month_label(month_iso: str) -> str:
    """'2026-05' → 'May 2026' — used for display."""
    year, month = month_iso.split("-")
    month_name = date(int(year), int(month), 1).strftime("%B")
    return f"{month_name} {year}"


# =====================================================================
# Header & sidebar
# =====================================================================

def render_header() -> None:
    st.title("💰 Smart Expense Tracker")
    st.caption(
        "Personal expense tracker — INR only · "
        "ML-powered categorization · SMS auto-import"
    )


def render_sidebar() -> None:
    """Sidebar: quick stats, budget alerts, ML status, retrain button."""
    with st.sidebar:
        st.header("📊 Quick Stats")

        expenses = get_all_expenses()

        # ----- Quick stats ---------------------------------------
        if not expenses:
            st.metric("Total Expenses", "₹0.00")
            st.caption("Add your first expense to see stats here.")
        else:
            today_iso = date.today().isoformat()
            today_total = sum(
                e["amount"] for e in expenses
                if e["expense_date"] == today_iso
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

        # ----- Budget alerts (current month) ---------------------
        current_month = date.today().strftime("%Y-%m")
        over_count = warn_count = safe_count = 0
        for cat in get_all_categories():
            status = get_budget_status(cat["id"], current_month)
            if status is None:
                continue
            if status["alert_level"] == "exceeded":
                over_count += 1
            elif status["alert_level"] == "warning":
                warn_count += 1
            else:
                safe_count += 1

        total_budgets = over_count + warn_count + safe_count
        if total_budgets > 0:
            st.divider()
            if over_count > 0:
                st.error(f"🔴 {over_count} budget(s) exceeded this month")
            elif warn_count > 0:
                st.warning(f"🟡 {warn_count} budget(s) near limit")
            else:
                st.caption("🟢 All budgets healthy this month")

        # ----- ML model status -----------------------------------
        st.divider()
        if is_model_available():
            st.caption("🤖 Auto-categorization: **active**")
        else:
            st.caption("⚠️ Train the model to enable auto-categorization")

        # ----- Correction-loop UI --------------------------------
        try:
            n_corrections = get_correction_count()
        except Exception:
            n_corrections = 0

        if n_corrections > 0:
            st.divider()
            st.caption(f"✏️ **{n_corrections}** correction(s) captured")
            if st.button(
                "🔄 Retrain model now",
                use_container_width=True,
                help="Re-fit the model with seed data + your corrections.",
            ):
                with st.spinner("Retraining…"):
                    metrics = run_training(verbose=False)
                    invalidate_cache()
                st.success(
                    f"✓ Retrained on **{metrics['total_examples']}** examples "
                    f"({metrics['n_seed']} seed + "
                    f"{metrics['n_corrections']} yours)  ·  "
                    f"Test accuracy: **{metrics['test_accuracy']:.0%}**"
                )
                st.rerun()
        
        # ----- Admin section ----------------------------------
        st.divider()
        with st.expander("⚙️ Settings", expanded=False):
            st.caption("Manage the data behind this app.")

            # Clear-all button
            if st.button(
                "🧹 Clear all data",
                use_container_width=True,
                help="Delete all expenses, budgets, and corrections.",
            ):
                st.session_state["_confirm_clear"] = True

            if st.session_state.get("_confirm_clear"):
                st.warning(
                    "⚠️ This will delete **all** expenses, budgets, "
                    "and corrections. Demo data won't auto-restore. "
                    "This cannot be undone."
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, delete", type="primary",
                                 use_container_width=True):
                        result = clear_all_data()
                        st.session_state["_confirm_clear"] = False
                        st.success(
                            f"✓ Cleared {result['expenses_deleted']} expenses, "
                            f"{result['budgets_deleted']} budgets, "
                            f"{result['corrections_deleted']} corrections."
                        )
                        st.rerun()
                with col_no:
                    if st.button("Cancel", use_container_width=True):
                        st.session_state["_confirm_clear"] = False
                        st.rerun()

            # Restore-demo button
            if st.button(
                "🔄 Restore demo data",
                use_container_width=True,
                help="Wipe current data and re-seed with the demo dataset.",
            ):
                clear_all_data()
                unmark_seeded()
                result = seed_demo_data(force=True)
                st.success(
                    f"✓ Restored {result['expenses_added']} demo expenses "
                    f"and {result['budgets_added']} budgets."
                )
                st.rerun()


# =====================================================================
# SMS import flow
# =====================================================================

def render_sms_import() -> None:
    """Paste bank SMS → auto-parse → preview → confirm → save."""

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

    # Category dropdown with state sync (so new predictions auto-fill)
    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }

    suggested_sms = cat_options[0]
    if prediction:
        predicted_label = (
            f"{prediction['category_icon']} {prediction['category_name']}"
        )
        if predicted_label in cat_options:
            suggested_sms = predicted_label

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
        # Detect SMS-flow category override
        if prediction:
            predicted_label_str = (
                f"{prediction['category_icon']} {prediction['category_name']}"
            )
            if category_label != predicted_label_str:
                add_correction(
                    description=result["merchant"],
                    category_id=cat_label_to_id[category_label],
                )
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
# Manual entry flow
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

    # ----- Live ML prediction display ------------------------------
    predicted_label: str | None = None

    if description.strip() and is_model_available():
        result = predict_category(description.strip())
        if result is not None:
            label = f"{result['category_icon']} {result['category_name']}"
            confidence = result["confidence"]
            predicted_label = label  # always auto-fill regardless of confidence

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
    elif description.strip() and not is_model_available():
        st.caption(
            "💡 Run `python train_classifier.py` to enable auto-categorization."
        )

    # ----- Form with the rest of the inputs ------------------------
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
            # Sync dropdown state when prediction changes
            suggested = (
                predicted_label
                if (predicted_label and predicted_label in cat_options)
                else cat_options[0]
            )
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
            # Detect a category override: if we had a prediction and the
            # user picked a different category, record it as training data.
            if predicted_label and category_label != predicted_label:
                add_correction(
                    description=description.strip(),
                    category_id=cat_label_to_id[category_label],
                )
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
# Recent expenses (with filter + delete buttons)
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

    with col_summary:
        st.write("")  # vertical spacer to align with the dropdown
        total = sum(e["amount"] for e in expenses)
        st.caption(
            f"📊 **{len(expenses)}** expenses · "
            f"**₹{total:,.2f}** total"
        )

    st.divider()

    # ----- Header row ---------------------------------------------
    cols = st.columns([2, 3, 4, 2, 1])
    cols[0].markdown("**Date**")
    cols[1].markdown("**Category**")
    cols[2].markdown("**Description**")
    cols[3].markdown("**Amount**")
    cols[4].markdown("")

    # ----- Data rows ----------------------------------------------
    visible = expenses[:30]

    for e in visible:
        cols = st.columns([2, 3, 4, 2, 1])

        cols[0].write(e["expense_date"])
        cols[1].write(f"{e['category_icon']} {e['category_name']}")

        desc = e["description"]
        merchant = e["merchant"]
        if merchant and merchant.lower() != desc.lower():
            desc = f"{desc}  ·  *{merchant}*"
        cols[2].write(desc)

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
# Dashboard
# =====================================================================

def render_dashboard() -> None:
    """Filtered analytics view with KPIs, pie, top merchants, daily trend."""
    st.subheader("📊 Spending Dashboard")

    all_expenses = get_all_expenses()

    if not all_expenses:
        st.info(
            "No expenses yet. Add some in the **📋 Track Expenses** tab "
            "to see your dashboard come alive."
        )
        return

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

    dates = sorted({e["expense_date"] for e in expenses})
    first_d = datetime.strptime(dates[0], "%Y-%m-%d").date()
    last_d = datetime.strptime(dates[-1], "%Y-%m-%d").date()
    days_span = max((last_d - first_d).days + 1, 1)
    avg_per_day = total_spent / days_span

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
# Budgets
# =====================================================================

def render_budgets() -> None:
    """Budget management: set per-category monthly caps and view status."""
    st.subheader("💰 Budgets")

    # ----- Month selector ----------------------------------------
    today = date.today()
    month_options = _get_month_options(today, n_months=12)

    selected_month = st.selectbox(
        "Month",
        options=month_options,
        format_func=_format_month_label,
        index=0,
        key="budget_month",
    )

    # ----- Pre-compute spend per category for this month ---------
    all_expenses = get_all_expenses()
    month_expenses = [
        e for e in all_expenses
        if e["expense_date"].startswith(selected_month)
    ]
    spent_by_cat: dict[int, float] = {}
    for e in month_expenses:
        cid = e["category_id"]
        spent_by_cat[cid] = spent_by_cat.get(cid, 0.0) + e["amount"]

    categories = get_all_categories()
    cat_options = [f"{c['icon']} {c['name']}" for c in categories]
    cat_label_to_id = {
        label: cat["id"] for label, cat in zip(cat_options, categories)
    }
    statuses: dict[int, dict | None] = {
        c["id"]: get_budget_status(c["id"], selected_month)
        for c in categories
    }

    # ----- Top KPI row --------------------------------------------
    total_spent_month = sum(spent_by_cat.values())
    total_budgeted = sum(
        s["limit_amount"] for s in statuses.values() if s is not None
    )
    n_over = sum(
        1 for s in statuses.values()
        if s is not None and s["alert_level"] == "exceeded"
    )
    n_set = sum(1 for s in statuses.values() if s is not None)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Budgeted", f"₹{total_budgeted:,.2f}")
    col2.metric("Total Spent", f"₹{total_spent_month:,.2f}")
    col3.metric("Budgets Set", f"{n_set} / {len(categories)}")
    col4.metric(
        "Over Budget",
        f"{n_over}",
        delta="⚠️ check below" if n_over > 0 else None,
        delta_color="off",
    )

    st.divider()

    # ----- Set / update form --------------------------------------
    st.markdown("### ➕ Set or update a budget")

    with st.form("budget_form"):
        col_cat, col_limit, col_alert = st.columns([2, 2, 2])

        with col_cat:
            category_label = st.selectbox("Category", options=cat_options)

        with col_limit:
            cat_id_preview = cat_label_to_id[category_label]
            existing = statuses.get(cat_id_preview)
            default_limit = (
                float(existing["limit_amount"]) if existing else 5000.0
            )
            limit_amount = st.number_input(
                "Monthly limit (₹)",
                min_value=0.0,
                step=500.0,
                format="%.2f",
                value=default_limit,
            )

        with col_alert:
            default_alert = (
                int(existing["alert_threshold"] * 100) if existing else 80
            )
            alert_pct = st.slider(
                "Warn me at",
                min_value=50,
                max_value=100,
                value=default_alert,
                step=5,
                format="%d%%",
            )

        if st.form_submit_button("💾 Save Budget", type="primary"):
            if limit_amount <= 0:
                st.error("Budget limit must be greater than 0.")
            else:
                cat_id = cat_label_to_id[category_label]
                set_budget(
                    category_id=cat_id,
                    month=selected_month,
                    limit_amount=limit_amount,
                    alert_threshold=alert_pct / 100.0,
                )
                st.success(
                    f"✓ Budget saved: {category_label} = "
                    f"₹{limit_amount:,.2f}/month  ·  alert at {alert_pct}%"
                )
                st.rerun()

    st.divider()

    # ----- Per-category status list -------------------------------
    st.markdown(f"### 📊 Status — {_format_month_label(selected_month)}")

    alert_emoji = {"safe": "🟢", "warning": "🟡", "exceeded": "🔴"}

    for cat in categories:
        cat_id = cat["id"]
        spent = spent_by_cat.get(cat_id, 0.0)
        status = statuses[cat_id]

        col_info, col_bar, col_action = st.columns([3, 6, 1])

        with col_info:
            st.markdown(f"{cat['icon']} **{cat['name']}**")

        with col_bar:
            if status is None:
                if spent > 0:
                    st.caption(
                        f"Spent ₹{spent:,.2f} this month  ·  *no budget set*"
                    )
                else:
                    st.caption("*No activity, no budget set*")
            else:
                pct = status["percentage_used"]
                alert = status["alert_level"]

                st.progress(min(pct, 1.0))

                if alert == "exceeded":
                    over = spent - status["limit_amount"]
                    st.caption(
                        f"{alert_emoji[alert]} "
                        f"₹{spent:,.2f} / ₹{status['limit_amount']:,.2f}  ·  "
                        f"**OVER BY ₹{over:,.2f}**  ({pct:.0%})"
                    )
                else:
                    st.caption(
                        f"{alert_emoji[alert]} "
                        f"₹{spent:,.2f} / ₹{status['limit_amount']:,.2f}  ·  "
                        f"₹{status['remaining']:,.2f} left  ({pct:.0%})"
                    )

        with col_action:
            if status is not None:
                if st.button(
                    "🗑️",
                    key=f"del_bgt_{cat_id}",
                    help=f"Delete {cat['name']} budget",
                ):
                    delete_budget(cat_id, selected_month)
                    st.rerun()


# =====================================================================
# Main entry point
# =====================================================================

def main() -> None:
    # On first deploy / fresh start, ensure database tables exist
    from init_db import init_database
    try:
        init_database()
    except Exception:
        pass  # tables already exist

    # Auto-seed demo data if the database is empty (deployment-friendly).
    # No-op for local users who already have data.
    seed_demo_data(force=False)

    st.set_page_config(
        page_title="Smart Expense Tracker",
        page_icon="💰",
        layout="wide",
    )

    render_header()
    render_sidebar()

    tab_track, tab_dashboard, tab_budgets = st.tabs([
        "📋 Track Expenses",
        "📊 Dashboard",
        "💰 Budgets",
    ])

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

    with tab_budgets:
        render_budgets()


if __name__ == "__main__":
    main()