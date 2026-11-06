"""
SalesInsight — analysis pipeline.

Loads sales_data.csv into an in-memory SQLite database, runs the key
business queries (the same logic as analysis.sql), prints a summary to
the console, and saves each result table as a CSV in outputs/.

Run generate_data.py first, then:  python analysis.py
"""

import os
import sqlite3

import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, "sales_data.csv")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

QUERIES = {
    "monthly_revenue": """
        SELECT strftime('%Y-%m', date) AS month,
               COUNT(*) AS orders,
               ROUND(SUM(revenue), 2) AS revenue
        FROM sales GROUP BY month ORDER BY month
    """,
    "mom_growth": """
        SELECT month, revenue,
               ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
                     / LAG(revenue) OVER (ORDER BY month), 2) AS mom_growth_pct
        FROM (SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS revenue
              FROM sales GROUP BY month)
        ORDER BY month
    """,
    "revenue_by_region": """
        SELECT region, COUNT(*) AS orders, ROUND(SUM(revenue), 2) AS revenue,
               ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM sales), 2)
                   AS revenue_share_pct
        FROM sales GROUP BY region ORDER BY revenue DESC
    """,
    "revenue_by_category": """
        SELECT category, COUNT(*) AS orders, SUM(quantity) AS units_sold,
               ROUND(SUM(revenue), 2) AS revenue, ROUND(AVG(revenue), 2) AS avg_order_value
        FROM sales GROUP BY category ORDER BY revenue DESC
    """,
    "top_products": """
        SELECT product, category, COUNT(*) AS orders, SUM(quantity) AS units_sold,
               ROUND(SUM(revenue), 2) AS revenue
        FROM sales GROUP BY product, category ORDER BY revenue DESC LIMIT 10
    """,
    "repeat_customers": """
        SELECT CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
               COUNT(*) AS customers, SUM(order_count) AS orders,
               ROUND(SUM(spend), 2) AS revenue
        FROM (SELECT customer_id, COUNT(*) AS order_count, SUM(revenue) AS spend
              FROM sales GROUP BY customer_id)
        GROUP BY customer_type
    """,
    "top_customers": """
        SELECT customer_id, COUNT(*) AS orders,
               ROUND(SUM(revenue), 2) AS lifetime_spend,
               MIN(date) AS first_order, MAX(date) AS last_order
        FROM sales GROUP BY customer_id ORDER BY lifetime_spend DESC LIMIT 10
    """,
    "aov_by_region": """
        SELECT region, ROUND(AVG(revenue), 2) AS avg_order_value,
               ROUND(AVG(quantity), 2) AS avg_items_per_order
        FROM sales GROUP BY region ORDER BY avg_order_value DESC
    """,
}


def main() -> None:
    if not os.path.exists(CSV_PATH):
        raise SystemExit("sales_data.csv not found — run generate_data.py first.")

    df = pd.read_csv(CSV_PATH, parse_dates=["date"])
    print(f"Loaded {len(df):,} rows from sales_data.csv")
    print(f"Nulls per column:\n{df.isna().sum().to_string()}")
    print(f"Date range: {df['date'].min().date()} to {df['date'].max().date()}\n")

    conn = sqlite3.connect(":memory:")
    df_sql = df.copy()
    df_sql["date"] = df_sql["date"].dt.strftime("%Y-%m-%d")
    df_sql.to_sql("sales", conn, index=False)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = {}
    for name, sql in QUERIES.items():
        table = pd.read_sql_query(sql, conn)
        results[name] = table
        table.to_csv(os.path.join(OUTPUT_DIR, f"{name}.csv"), index=False)

    conn.close()

    # ---------- Headline summary ----------
    total_revenue = df["revenue"].sum()
    total_orders = len(df)
    aov = df["revenue"].mean()
    unique_customers = df["customer_id"].nunique()

    print("=" * 60)
    print("SALESINSIGHT — HEADLINE SUMMARY")
    print("=" * 60)
    print(f"Total orders:        {total_orders:,}")
    print(f"Total revenue:       {total_revenue:,.2f}")
    print(f"Average order value: {aov:,.2f}")
    print(f"Unique customers:    {unique_customers:,}")

    print("\nRevenue by category:")
    print(results["revenue_by_category"].to_string(index=False))

    print("\nRevenue by region:")
    print(results["revenue_by_region"].to_string(index=False))

    print("\nTop 5 products by revenue:")
    print(results["top_products"].head(5).to_string(index=False))

    print("\nRepeat vs one-time customers:")
    print(results["repeat_customers"].to_string(index=False))

    monthly = results["monthly_revenue"]
    best = monthly.loc[monthly["revenue"].idxmax()]
    worst = monthly.loc[monthly["revenue"].idxmin()]
    print(f"\nBest month:  {best['month']} ({best['revenue']:,.2f})")
    print(f"Worst month: {worst['month']} ({worst['revenue']:,.2f})")

    print(f"\nSaved {len(results)} result tables to outputs/")


if __name__ == "__main__":
    main()
