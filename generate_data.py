"""
SalesInsight — synthetic e-commerce sales data generator.

Creates sales_data.csv with realistic patterns:
- Seasonal demand (Nov-Dec spike, summer bump for some categories)
- Regional price/quantity differences
- Repeat customers (a customer pool, so some customers order many times)
- Product catalogue with sensible price ranges per category

Seeded RNG (seed=42) so the dataset is reproducible — anyone who clones
the repo and runs this script gets the exact same file.
"""

import csv
import random
from datetime import date, timedelta

random.seed(42)

NUM_ORDERS = 5000
START_DATE = date(2024, 1, 1)
END_DATE = date(2024, 12, 31)
NUM_CUSTOMERS = 1200

REGIONS = ["North", "South", "East", "West", "Central"]
REGION_WEIGHTS = [0.26, 0.24, 0.19, 0.21, 0.10]

CATALOGUE = {
    "Electronics": [
        ("Wireless Headphones", 2499, 8999),
        ("Bluetooth Speaker", 1799, 5999),
        ("Smart Watch", 4999, 14999),
        ("Laptop Stand", 1299, 3499),
        ("USB-C Hub", 1499, 3999),
        ("Mechanical Keyboard", 2999, 7999),
    ],
    "Fashion": [
        ("Cotton T-Shirt", 499, 1499),
        ("Denim Jeans", 1299, 2999),
        ("Running Shoes", 1999, 5999),
        ("Sunglasses", 799, 2499),
        ("Leather Wallet", 999, 2999),
    ],
    "Home & Kitchen": [
        ("Air Fryer", 3999, 9999),
        ("Mixer Grinder", 2499, 6999),
        ("Dinner Set (16 pc)", 1999, 4999),
        ("LED Table Lamp", 899, 2499),
        ("Storage Organizer", 599, 1799),
    ],
    "Beauty": [
        ("Face Serum", 599, 1999),
        ("Matte Lipstick", 349, 999),
        ("Hair Dryer", 1499, 3999),
        ("Sunscreen SPF 50", 399, 899),
    ],
    "Sports": [
        ("Yoga Mat", 699, 1799),
        ("Dumbbell Set 5kg", 1299, 3499),
        ("Cricket Bat", 1999, 6999),
        ("Badminton Racket", 999, 2999),
        ("Cycling Helmet", 1199, 2999),
    ],
    "Books": [
        ("Fiction Novel", 299, 799),
        ("Data Science Handbook", 899, 1999),
        ("Cookbook", 499, 1299),
        ("Exam Prep Guide", 599, 1499),
    ],
}
CATEGORY_WEIGHTS = {
    "Electronics": 0.24,
    "Fashion": 0.22,
    "Home & Kitchen": 0.18,
    "Beauty": 0.12,
    "Sports": 0.12,
    "Books": 0.12,
}


def seasonal_factor(d: date, category: str) -> float:
    """Demand multiplier by month — festive spike, category quirks."""
    m = d.month
    factor = 1.0
    if m in (10, 11):
        factor = 1.45  # festive season
    elif m == 12:
        factor = 1.25
    elif m in (6, 7):
        factor = 0.85  # monsoon dip
    if category == "Sports" and m in (1, 2):
        factor *= 1.3  # new-year fitness
    if category == "Fashion" and m in (10, 11):
        factor *= 1.2
    if category == "Books" and m in (5, 6):
        factor *= 1.25  # exam season
    return factor


def pick_date(category: str) -> date:
    """Rejection-sample a date so seasonal categories cluster correctly."""
    while True:
        delta = random.randint(0, (END_DATE - START_DATE).days)
        d = START_DATE + timedelta(days=delta)
        if random.random() < seasonal_factor(d, category) / 1.6:
            return d


def main() -> None:
    categories = list(CATALOGUE.keys())
    weights = [CATEGORY_WEIGHTS[c] for c in categories]
    # Zipf-like customer activity: some customers order far more often.
    customer_weights = [1 / (i + 1) ** 0.55 for i in range(NUM_CUSTOMERS)]

    rows = []
    for order_num in range(1, NUM_ORDERS + 1):
        category = random.choices(categories, weights=weights)[0]
        product, low, high = random.choice(CATALOGUE[category])
        region = random.choices(REGIONS, weights=REGION_WEIGHTS)[0]
        customer_id = random.choices(
            range(1, NUM_CUSTOMERS + 1), weights=customer_weights
        )[0]
        order_date = pick_date(category)

        base_price = random.uniform(low, high)
        if region in ("West", "North"):
            base_price *= random.uniform(1.0, 1.08)
        unit_price = round(base_price, 2)

        quantity = random.choices([1, 2, 3, 4, 5], weights=[62, 22, 9, 4, 3])[0]
        revenue = round(quantity * unit_price, 2)

        rows.append(
            {
                "order_id": f"ORD{order_num:05d}",
                "date": order_date.isoformat(),
                "region": region,
                "category": category,
                "product": product,
                "quantity": quantity,
                "unit_price": unit_price,
                "revenue": revenue,
                "customer_id": f"CUST{customer_id:04d}",
            }
        )

    rows.sort(key=lambda r: (r["date"], r["order_id"]))

    out_path = "sales_data.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    total_revenue = sum(r["revenue"] for r in rows)
    print(f"Wrote {len(rows)} orders to {out_path}")
    print(f"Date range: {rows[0]['date']} to {rows[-1]['date']}")
    print(f"Total revenue: {total_revenue:,.2f}")


if __name__ == "__main__":
    main()
