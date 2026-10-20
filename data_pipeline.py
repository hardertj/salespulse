"""SalesPulse Domain Engine: Data Ingestion, Cleaning & Vectorized Analytics.

This module is completely decoupled from Streamlit. It uses Pandas to handle:
1. Data generation & schema validation
2. Vectorized feature engineering (profit margin %, date parsing)
3. Filtering and aggregation pipelines for KPI reporting
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class KPISummary:
    """Immutable data model representing executive scorecard metrics."""
    total_revenue: float
    total_orders: int
    avg_order_value: float
    total_profit: float
    avg_profit_margin: float
    # Period-over-period delta estimates for UI indicators
    revenue_growth_pct: float
    profit_growth_pct: float


def generate_sales_dataset(num_records: int = 1200, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic retail e-commerce transactions dataset.
    
    Includes seasonality, regional variation, product hierarchy, and margin variations.
    """
    np.random.seed(seed)

    start_date = datetime(2025, 1, 1)
    # Generate random dates over a 12-month window
    random_days = np.random.randint(0, 365, size=num_records)
    dates = [start_date + timedelta(days=int(d)) for d in random_days]

    regions = ["North", "South", "East", "West"]
    categories = {
        "Electronics": ["Laptops", "Smartphones", "Audio", "Accessories"],
        "Apparel": ["Men's Wear", "Women's Wear", "Footwear", "Activewear"],
        "Home & Kitchen": ["Cookware", "Bedding", "Furniture", "Lighting"],
        "Office Supplies": ["Paper", "Storage", "Writing Tools", "Chairs"],
    }
    customer_segments = ["Consumer", "Corporate", "Small Business"]

    records = []
    for i in range(num_records):
        order_date = dates[i]
        region = np.random.choice(regions, p=[0.25, 0.20, 0.35, 0.20])
        cat = np.random.choice(list(categories.keys()), p=[0.35, 0.25, 0.25, 0.15])
        sub_cat = np.random.choice(categories[cat])
        segment = np.random.choice(customer_segments, p=[0.50, 0.30, 0.20])

        # Baseline pricing per category
        base_price_map = {
            "Electronics": (80.0, 1200.0),
            "Apparel": (20.0, 180.0),
            "Home & Kitchen": (30.0, 450.0),
            "Office Supplies": (10.0, 120.0),
        }
        low, high = base_price_map[cat]
        unit_price = np.random.uniform(low, high)
        quantity = np.random.choice([1, 2, 3, 4, 5, 8], p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02])
        discount = np.random.choice([0.0, 0.05, 0.10, 0.15, 0.25], p=[0.50, 0.20, 0.15, 0.10, 0.05])

        sales = round(unit_price * quantity * (1.0 - discount), 2)
        # Margin varies by category (e.g., Office & Apparel have higher margin than Electronics)
        margin_map = {
            "Electronics": 0.18,
            "Apparel": 0.42,
            "Home & Kitchen": 0.32,
            "Office Supplies": 0.48,
        }
        margin_noise = np.random.uniform(-0.08, 0.08)
        cost = round(sales * (1.0 - (margin_map[cat] + margin_noise)), 2)
        profit = round(sales - cost, 2)

        records.append({
            "order_id": f"ORD-{10000 + i}",
            "order_date": order_date,
            "region": region,
            "category": cat,
            "sub_category": sub_cat,
            "customer_segment": segment,
            "sales": sales,
            "quantity": int(quantity),
            "discount_pct": round(discount * 100, 1),
            "profit": profit,
        })

    df = pd.DataFrame(records)
    # Sort chronologically
    df.sort_values(by="order_date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Vectorized calculated column: Profit Margin %
    df["profit_margin_pct"] = np.where(
        df["sales"] > 0,
        np.round((df["profit"] / df["sales"]) * 100, 2),
        0.0,
    )
    return df


def filter_sales_data(
    df: pd.DataFrame,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    regions: list[str] | None = None,
    categories: list[str] | None = None,
    segments: list[str] | None = None,
) -> pd.DataFrame:
    """Vectorized multi-dimensional filtering pipeline."""
    filtered = df.copy()

    if start_date is not None:
        filtered = filtered[filtered["order_date"] >= pd.Timestamp(start_date)]
    if end_date is not None:
        filtered = filtered[filtered["order_date"] <= pd.Timestamp(end_date)]
    if regions:
        filtered = filtered[filtered["region"].isin(regions)]
    if categories:
        filtered = filtered[filtered["category"].isin(categories)]
    if segments:
        filtered = filtered[filtered["customer_segment"].isin(segments)]

    return filtered


def compute_kpi_summary(df: pd.DataFrame) -> KPISummary:
    """Compute high-level executive summary metrics with simulated period growth."""
    if df.empty:
        return KPISummary(0.0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    total_revenue = float(df["sales"].sum())
    total_orders = int(df["order_id"].nunique())
    total_profit = float(df["profit"].sum())
    aov = float(total_revenue / total_orders) if total_orders > 0 else 0.0
    avg_margin = float(total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    # Split dataset in halves to compute authentic period-over-period growth
    mid_point = len(df) // 2
    if mid_point > 0:
        prev_half = df.iloc[:mid_point]
        curr_half = df.iloc[mid_point:]
        prev_rev = prev_half["sales"].sum()
        curr_rev = curr_half["sales"].sum()
        rev_growth = ((curr_rev - prev_rev) / prev_rev * 100) if prev_rev > 0 else 0.0

        prev_prof = prev_half["profit"].sum()
        curr_prof = curr_half["profit"].sum()
        prof_growth = ((curr_prof - prev_prof) / prev_prof * 100) if prev_prof > 0 else 0.0
    else:
        rev_growth, prof_growth = 0.0, 0.0

    return KPISummary(
        total_revenue=round(total_revenue, 2),
        total_orders=total_orders,
        avg_order_value=round(aov, 2),
        total_profit=round(total_profit, 2),
        avg_profit_margin=round(avg_margin, 2),
        revenue_growth_pct=round(rev_growth, 1),
        profit_growth_pct=round(prof_growth, 1),
    )


def aggregate_by_time(df: pd.DataFrame, freq: str = "W") -> pd.DataFrame:
    """Group sales and profit over time by Week ('W') or Month ('ME')."""
    if df.empty:
        return pd.DataFrame(columns=["date", "sales", "profit"])

    resampled = (
        df.set_index("order_date")
        .resample(freq)[["sales", "profit"]]
        .sum()
        .reset_index()
    )
    resampled.rename(columns={"order_date": "date"}, inplace=True)
    return resampled


def aggregate_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue, profit, and units by category."""
    if df.empty:
        return pd.DataFrame()

    agg = (
        df.groupby("category", as_index=False)
        .agg(
            total_sales=("sales", "sum"),
            total_profit=("profit", "sum"),
            total_quantity=("quantity", "sum"),
        )
        .sort_values(by="total_sales", ascending=False)
    )
    agg["margin_pct"] = np.round((agg["total_profit"] / agg["total_sales"]) * 100, 1)
    return agg


def aggregate_by_region(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate revenue and profit across geographic regions."""
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby("region", as_index=False)
        .agg(total_sales=("sales", "sum"), total_profit=("profit", "sum"))
        .sort_values(by="total_sales", ascending=True)
    )

def simulate_pricing_scenario(
        df: pd.DataFrame, 
        price_change_pct: float = 0.0,
        discount_change_pct: float = 0.0
) -> pd.DataFrame:
    """Simulate the financial impact of price and discount adjustments.
    
    Args:
        df: the filtered or master transactions DataFrame.
        price_change_pct: Percentage to increase/decrease base price (e.g., +5.0 for +5%).
        discount_change_pct: Percentage points to adjust discount (e.g., -2.0 to reduce discount by 2%).
        
    Returns:
        A new DataFrame with simulated columns: 'sim_sales', 'sim_profit', and 'sim_margin_pct'.
    """

    # 1. Start with a copy of the dataframe so we don't mutate the original! 
    sim_df = df.copy()

    # 2. Derive the original unit price betfore discount:
    # original sales = unit_price * quantity * (1 - discount_pct / 100)
    # Therefore: gross_sales = sales / (1 - discount_pct / 100)
    # Hint: Watch out for division by zero if discount is 100%!
    # Calculate the original gross sales or effective unit price
    sim_df["gross_sales"] = sim_df["sales"] / np.where(sim_df['discount_pct'] < 100, ( 1 - sim_df['discount_pct'] / 100), 1)

    # 3. Apply the price change:
    # new_gross_sales = gross_sales * (1 + price_change_pct / 100)
    sim_df["new_gross_sales"] = sim_df["gross_sales"] * (1 + price_change_pct / 100)    

    # 4. Calculate new discount percentage:
    # new_discount_pct = np.clip(sim_df['discount_pct'] + discount_change_pct, 0.0, 100.0)
    # TODO: Calculate new_discount_pct
    sim_df["new_discount_pct"] = np.clip(sim_df["discount_pct"] + discount_change_pct, 0.0, 100.0)

    # 5. Calculate simulated sales:
    # sim_sales = new_gross_sales * (1 - new_discount_pct / 100)
    sim_df["sim_sales"] = sim_df["new_gross_sales"] * ( 1 - sim_df["new_discount_pct"] / 100)

    # 6. Keep original product cost constant, then calculate simulated profit:
    # original_cost = sim_df['sales'] - sim_df['profit']
    # sim_df["sim_profit"] = sim_df["sim_sales"] - original_cost
    sim_df["sim_profit"] = sim_df["sim_sales"] - (sim_df["sales"] - sim_df["profit"])

    # 7. Calculate simulated profit margin %:
    # sim_df["sim_margin_pct"] = (sim_df["sim_profit"] / sim_df["sim_sales"]) * 100
    # TODO: Calculate sim_margin_pct
    sim_df["sim_margin_pct"] = np.where(
        sim_df["sim_sales"] > 0,
        (sim_df["sim_profit"] / sim_df["sim_sales"]) * 100, 0.0)

    return sim_df
