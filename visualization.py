"""
Visualization module — builds Plotly charts from expense data.

Pure data → figure functions. No Streamlit, no database calls.
Each function takes a list of expense rows (from get_all_expenses)
and returns a Plotly Figure (or None if there's nothing to chart).
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# =====================================================================
# Helper: convert sqlite3.Row list → DataFrame
# =====================================================================

def _expenses_to_df(expenses: list) -> pd.DataFrame:
    """
    Turn a list of expense rows into a DataFrame ready for charting.

    Adds derived columns (a clean 'merchant_or_desc' and a parsed date)
    so charts don't have to handle missing values inline.
    """
    if not expenses:
        return pd.DataFrame()

    df = pd.DataFrame([
        {
            "date": e["expense_date"],
            "amount": e["amount"],
            "category": f"{e['category_icon']} {e['category_name']}",
            "category_color": e["category_color"],
            "description": e["description"],
            "merchant": e["merchant"] or e["description"][:40],
            "source": e["source"],
        }
        for e in expenses
    ])

    # Parse date strings to actual datetime for time-series charts
    df["date"] = pd.to_datetime(df["date"])
    return df


# =====================================================================
# Chart 1: Category breakdown (donut)
# =====================================================================

def build_category_pie(expenses: list) -> Optional[go.Figure]:
    """Donut chart of total spending split by category."""
    df = _expenses_to_df(expenses)
    if df.empty:
        return None

    # Group by category, sum amounts, keep the first color seen
    grouped = (
        df.groupby("category", as_index=False)
        .agg(total=("amount", "sum"), color=("category_color", "first"))
        .sort_values("total", ascending=False)
    )

    # Map each category label to its hex color
    color_map = dict(zip(grouped["category"], grouped["color"]))

    fig = px.pie(
        grouped,
        values="total",
        names="category",
        hole=0.5,                          # donut, not solid pie
        color="category",
        color_discrete_map=color_map,
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "₹%{value:,.2f}<br>"
            "%{percent}"
            "<extra></extra>"             # hides the "trace 0" hover label
        ),
    )

    fig.update_layout(
        title="Spending by Category",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, x=1.05),
    )

    return fig


# =====================================================================
# Chart 2: Top N merchants (horizontal bar)
# =====================================================================

def build_top_merchants(expenses: list, n: int = 10) -> Optional[go.Figure]:
    """Horizontal bar chart of top N merchants by total spend."""
    df = _expenses_to_df(expenses)
    if df.empty:
        return None

    grouped = (
        df.groupby("merchant", as_index=False)
        .agg(total=("amount", "sum"), count=("amount", "size"))
        .nlargest(n, "total")
        .sort_values("total", ascending=True)  # asc → largest at top in barh
    )

    fig = px.bar(
        grouped,
        x="total",
        y="merchant",
        orientation="h",
        text="total",
        custom_data=["count"],
    )

    fig.update_traces(
        marker_color="#4ECDC4",
        texttemplate="₹%{x:,.0f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Total: ₹%{x:,.2f}<br>"
            "%{customdata[0]} transactions"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title=f"Top {n} Merchants",
        xaxis_title="Total Spent (₹)",
        yaxis_title="",
        height=400,
        margin=dict(l=20, r=80, t=50, b=20),  # extra right margin for labels
    )

    return fig


# =====================================================================
# Chart 3: Daily spending trend (line + markers)
# =====================================================================

def build_spending_trend(expenses: list) -> Optional[go.Figure]:
    """Daily spending over time as a line chart."""
    df = _expenses_to_df(expenses)
    if df.empty:
        return None

    # Add a 'day' column (date stripped of time-of-day) so we can
    # group by it cleanly. Doing this BEFORE groupby avoids the
    # name-resolution quirks of grouping on a derived Series.
    df = df.copy()
    df["day"] = df["date"].dt.date

    daily = (
        df.groupby("day", as_index=False)
        .agg(total=("amount", "sum"), count=("amount", "size"))
        .sort_values("day")
    )

    fig = px.line(
        daily,
        x="day",
        y="total",
        custom_data=["count"],
        markers=True,
    )

    fig.update_traces(
        line=dict(color="#FF6B6B", width=2),
        marker=dict(size=8),
        hovertemplate=(
            "<b>%{x|%d %b %Y}</b><br>"
            "Total: ₹%{y:,.2f}<br>"
            "%{customdata[0]} transactions"
            "<extra></extra>"
        ),
    )

    fig.update_layout(
        title="Daily Spending Trend",
        xaxis_title="Date",
        yaxis_title="Amount (₹)",
        height=350,
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
    )

    return fig