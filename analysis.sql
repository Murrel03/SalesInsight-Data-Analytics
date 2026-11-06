-- SalesInsight — business analysis queries
-- Table: sales (loaded from sales_data.csv by analysis.py)
-- Dialect: standard SQL, SQLite-compatible.
-- Columns: order_id, date (YYYY-MM-DD), region, category, product,
--          quantity, unit_price, revenue, customer_id

-- Q1. Total revenue, orders and average order value (headline KPIs)
SELECT
    COUNT(*)                  AS total_orders,
    ROUND(SUM(revenue), 2)    AS total_revenue,
    ROUND(AVG(revenue), 2)    AS avg_order_value,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM sales;

-- Q2. Monthly revenue trend
SELECT
    strftime('%Y-%m', date) AS month,
    COUNT(*)                AS orders,
    ROUND(SUM(revenue), 2)  AS revenue
FROM sales
GROUP BY month
ORDER BY month;

-- Q3. Month-over-month revenue growth (window function)
SELECT
    month,
    revenue,
    ROUND(
        100.0 * (revenue - LAG(revenue) OVER (ORDER BY month))
        / LAG(revenue) OVER (ORDER BY month), 2
    ) AS mom_growth_pct
FROM (
    SELECT strftime('%Y-%m', date) AS month, SUM(revenue) AS revenue
    FROM sales
    GROUP BY month
)
ORDER BY month;

-- Q4. Revenue by region
SELECT
    region,
    COUNT(*)                        AS orders,
    ROUND(SUM(revenue), 2)          AS revenue,
    ROUND(100.0 * SUM(revenue) / (SELECT SUM(revenue) FROM sales), 2) AS revenue_share_pct
FROM sales
GROUP BY region
ORDER BY revenue DESC;

-- Q5. Revenue by category
SELECT
    category,
    COUNT(*)               AS orders,
    SUM(quantity)          AS units_sold,
    ROUND(SUM(revenue), 2) AS revenue,
    ROUND(AVG(revenue), 2) AS avg_order_value
FROM sales
GROUP BY category
ORDER BY revenue DESC;

-- Q6. Top 10 products by revenue
SELECT
    product,
    category,
    COUNT(*)               AS orders,
    SUM(quantity)          AS units_sold,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY product, category
ORDER BY revenue DESC
LIMIT 10;

-- Q7. Top 10 products by units sold (volume leaders can differ from revenue leaders)
SELECT
    product,
    category,
    SUM(quantity)          AS units_sold,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY product, category
ORDER BY units_sold DESC
LIMIT 10;

-- Q8. Repeat vs one-time customers
SELECT
    CASE WHEN order_count > 1 THEN 'Repeat' ELSE 'One-time' END AS customer_type,
    COUNT(*)              AS customers,
    SUM(order_count)      AS orders,
    ROUND(SUM(spend), 2)  AS revenue
FROM (
    SELECT customer_id, COUNT(*) AS order_count, SUM(revenue) AS spend
    FROM sales
    GROUP BY customer_id
)
GROUP BY customer_type;

-- Q9. Top 10 customers by lifetime spend
SELECT
    customer_id,
    COUNT(*)               AS orders,
    ROUND(SUM(revenue), 2) AS lifetime_spend,
    MIN(date)              AS first_order,
    MAX(date)              AS last_order
FROM sales
GROUP BY customer_id
ORDER BY lifetime_spend DESC
LIMIT 10;

-- Q10. Average order value by region
SELECT
    region,
    ROUND(AVG(revenue), 2) AS avg_order_value,
    ROUND(AVG(quantity), 2) AS avg_items_per_order
FROM sales
GROUP BY region
ORDER BY avg_order_value DESC;

-- Q11. Revenue by category within each region (pivot-style breakdown)
SELECT
    region,
    category,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY region, category
ORDER BY region, revenue DESC;

-- Q12. Best single sales day and quarterly summary
SELECT
    strftime('%Y', date) || '-Q' || ((CAST(strftime('%m', date) AS INTEGER) - 1) / 3 + 1) AS quarter,
    COUNT(*)               AS orders,
    ROUND(SUM(revenue), 2) AS revenue
FROM sales
GROUP BY quarter
ORDER BY quarter;
