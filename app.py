"""
SalesInsight — Streamlit dashboard.

Run generate_data.py first, then:
    streamlit run app.py
"""

import os

import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sales_data.csv")

st.set_page_config(page_title="SalesInsight Dashboard", layout="wide")


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    df["month"] = df["date"].dt.to_period("M").astype(str)
    return df


def main() -> None:
    st.title("SalesInsight — E-commerce Sales Dashboard")
    st.caption("Synthetic 2024 sales data · SQL + pandas analysis · Streamlit")

    if not os.path.exists(CSV_PATH):
        st.error("sales_data.csv not found. Run `python generate_data.py` first.")
        return

    df = load_data()

    # ---------- Sidebar filters ----------
    st.sidebar.header("Filters")
    regions = st.sidebar.multiselect(
        "Region", sorted(df["region"].unique()), default=sorted(df["region"].unique())
    )
    categories = st.sidebar.multiselect(
        "Category", sorted(df["category"].unique()), default=sorted(df["category"].unique())
    )
    date_range = st.sidebar.date_input(
        "Date range",
        value=(df["date"].min().date(), df["date"].max().date()),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
    )

    filtered = df[
        df["region"].isin(regions)
        & df["category"].isin(categories)
        & (df["date"].dt.date >= date_range[0])
        & (df["date"].dt.date <= date_range[1])
    ]

    if filtered.empty:
        st.warning("No orders match the current filters.")
        return

    # ---------- KPI row ----------
    total_revenue = filtered["revenue"].sum()
    total_orders = len(filtered)
    aov = filtered["revenue"].mean()
    unique_customers = filtered["customer_id"].nunique()
    repeat_rate = (
        filtered.groupby("customer_id").size().gt(1).mean() * 100
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Revenue", f"{total_revenue:,.0f}")
    col2.metric("Orders", f"{total_orders:,}")
    col3.metric("Avg Order Value", f"{aov:,.0f}")
    col4.metric("Unique Customers", f"{unique_customers:,}")
    col5.metric("Repeat Customer Rate", f"{repeat_rate:.1f}%")

    # ---------- Revenue trend ----------
    st.subheader("Monthly Revenue Trend")
    monthly = filtered.groupby("month", as_index=False)["revenue"].sum()
    st.line_chart(monthly, x="month", y="revenue")

    # ---------- Breakdowns ----------
    left, right = st.columns(2)

    with left:
        st.subheader("Revenue by Region")
        by_region = (
            filtered.groupby("region", as_index=False)["revenue"].sum()
            .sort_values("revenue", ascending=False)
        )
        st.bar_chart(by_region, x="region", y="revenue")
        st.dataframe(by_region, use_container_width=True, hide_index=True)

    with right:
        st.subheader("Revenue by Category")
        by_category = (
            filtered.groupby("category", as_index=False)["revenue"].sum()
            .sort_values("revenue", ascending=False)
        )
        st.bar_chart(by_category, x="category", y="revenue")
        st.dataframe(by_category, use_container_width=True, hide_index=True)

    # ---------- Top products ----------
    st.subheader("Top 10 Products by Revenue")
    top_products = (
        filtered.groupby(["product", "category"], as_index=False)
        .agg(orders=("order_id", "count"), units=("quantity", "sum"),
             revenue=("revenue", "sum"))
        .sort_values("revenue", ascending=False)
        .head(10)
    )
    st.dataframe(top_products, use_container_width=True, hide_index=True)

    st.caption(f"Showing {total_orders:,} of {len(df):,} total orders after filters.")


if __name__ == "__main__":
    main()
