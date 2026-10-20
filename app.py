"""SalesPulse: E-Commerce & Retail Intelligence Dashboard.

Demonstrates:
1. High-Performance Caching with @st.cache_data
2. Separation of Concerns (UI Presentation vs Pure Data Pipeline)
3. Dynamic Vectorized Filtering
4. Interactive Plotly Visualizations & KPI Scorecards
"""

from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import our decoupled domain engine
from data_pipeline import (
    aggregate_by_category,
    aggregate_by_region,
    aggregate_by_time,
    compute_kpi_summary,
    filter_sales_data,
    generate_sales_dataset,
)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="SalesPulse: Retail Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- 2. HIGH-PERFORMANCE DATA CACHING (Software Design) ---
@st.cache_data
def get_master_dataset() -> pd.DataFrame:
    """Load and cache the master dataset in RAM.
    
    @st.cache_data memoizes the output. On reactive re-runs, Streamlit fetches
    the pre-computed DataFrame instantly from memory instead of regenerating it.
    """
    return generate_sales_dataset(num_records=1500, seed=42)


# Load dataset once via cache
df_master = get_master_dataset()


# --- 3. SIDEBAR: DYNAMIC FILTER PANEL (UI/UX Design) ---
with st.sidebar:
    st.title("🎛️ Filter Panel")
    st.caption("Slice and dice business metrics across dimensions.")

    # Date Range Filter
    min_date = df_master["order_date"].min().date()
    max_date = df_master["order_date"].max().date()

    selected_dates = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    # Multi-Select Filters
    all_regions = sorted(df_master["region"].unique())
    selected_regions = st.multiselect(
        "Geographic Regions",
        options=all_regions,
        default=all_regions,
    )

    all_categories = sorted(df_master["category"].unique())
    selected_categories = st.multiselect(
        "Product Categories",
        options=all_categories,
        default=all_categories,
    )

    all_segments = sorted(df_master["customer_segment"].unique())
    selected_segments = st.multiselect(
        "Customer Segments",
        options=all_segments,
        default=all_segments,
    )

    st.divider()

    # Time Granularity Toggle
    time_granularity = st.radio(
        "Trend Granularity:",
        options=["Weekly ('W')", "Monthly ('ME')"],
        horizontal=True,
    )
    freq_code = "W" if "Weekly" in time_granularity else "ME"


# --- 4. APPLY PIPELINE FILTERING ---
# Convert date input tuple safely
if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
    start_dt, end_dt = selected_dates
else:
    start_dt, end_dt = min_date, max_date

df_filtered = filter_sales_data(
    df=df_master,
    start_date=datetime.combine(start_dt, datetime.min.time()),
    end_date=datetime.combine(end_dt, datetime.max.time()),
    regions=selected_regions,
    categories=selected_categories,
    segments=selected_segments,
)


# --- 5. MAIN PRESENTATION VIEW ---
st.title("📈 SalesPulse: E-Commerce Intelligence Dashboard")
st.caption(
    f"Active Slice: **{len(df_filtered):,}** orders matching criteria out of **{len(df_master):,}** master transactions."
)

if df_filtered.empty:
    st.warning("⚠️ No transactions match your selected filter criteria. Please broaden your filters in the sidebar.")
    st.stop()

# --- ROW 1: EXECUTIVE KPI SCORECARDS ---
kpi = compute_kpi_summary(df_filtered)

kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric(
    label="Total Revenue",
    value=f"${kpi.total_revenue:,.2f}",
    delta=f"{kpi.revenue_growth_pct:+.1f}% vs H1",
)
kpi2.metric(
    label="Total Orders",
    value=f"{kpi.total_orders:,}",
)
kpi3.metric(
    label="Average Order Value (AOV)",
    value=f"${kpi.avg_order_value:.2f}",
)
kpi4.metric(
    label="Net Profit Margin",
    value=f"{kpi.avg_profit_margin:.1f}%",
    delta=f"{kpi.profit_growth_pct:+.1f}% vs H1",
)

st.divider()

# --- ROW 2: TIME-SERIES TRENDS & REGIONAL BREAKDOWN ---
col_trend, col_region = st.columns([2, 1])

with col_trend:
    st.markdown("### 📊 Revenue & Profit Trajectory")
    df_trend = aggregate_by_time(df_filtered, freq=freq_code)

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=df_trend["date"],
            y=df_trend["sales"],
            name="Revenue",
            mode="lines+markers",
            line=dict(color="#1f77b4", width=3),
        )
    )
    fig_trend.add_trace(
        go.Scatter(
            x=df_trend["date"],
            y=df_trend["profit"],
            name="Profit",
            mode="lines+markers",
            line=dict(color="#2ca02c", width=2, dash="dot"),
        )
    )
    fig_trend.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=340,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with col_region:
    st.markdown("### 🗺️ Revenue by Region")
    df_reg = aggregate_by_region(df_filtered)

    fig_reg = px.bar(
        df_reg,
        x="total_sales",
        y="region",
        orientation="h",
        color="total_profit",
        color_continuous_scale="Viridis",
        labels={"total_sales": "Sales ($)", "region": "Region", "total_profit": "Profit ($)"},
    )
    fig_reg.update_layout(
        margin=dict(l=20, r=20, t=30, b=20),
        height=340,
    )
    st.plotly_chart(fig_reg, use_container_width=True)

st.divider()

# --- ROW 3: CATEGORY PROFITABILITY & SEGMENT DISTRIBUTION ---
col_cat, col_seg = st.columns([1, 1])

with col_cat:
    st.markdown("### 🏷️ Category Performance & Margins")
    df_cat = aggregate_by_category(df_filtered)

    fig_cat = px.bar(
        df_cat,
        x="category",
        y="total_sales",
        text_auto=".2s",
        color="margin_pct",
        color_continuous_scale="Blues",
        labels={"total_sales": "Sales ($)", "category": "Category", "margin_pct": "Margin %"},
    )
    fig_cat.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_seg:
    st.markdown("### 👥 Customer Segment Breakdown")
    fig_seg = px.pie(
        df_filtered,
        names="customer_segment",
        values="sales",
        hole=0.45,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_seg.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=300)
    st.plotly_chart(fig_seg, use_container_width=True)

st.divider()

# --- ROW 4: DATA EXPLORER & CSV EXPORT ---
with st.expander("🔍 View Raw Transactions & Export", expanded=False):
    st.dataframe(
        df_filtered[[
            "order_id",
            "order_date",
            "region",
            "category",
            "sub_category",
            "customer_segment",
            "sales",
            "profit",
            "profit_margin_pct",
        ]],
        use_container_width=True,
        hide_index=True,
    )

    csv_data = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Slice as CSV",
        data=csv_data,
        file_name="salespulse_filtered_orders.csv",
        mime="text/csv",
    )
