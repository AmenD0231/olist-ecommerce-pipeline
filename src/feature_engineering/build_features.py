# =============================================================================
# BUILD_FEATURES.PY
# =============================================================================
# Purpose:
# Build customer-level RFM (Recency, Frequency, Monetary) features from
# the SQLite database, grouped by customer_unique_id — the actual person,
# not customer_id, which Olist assigns fresh per order.
#
# New work: your original notebook never reached feature engineering.
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import sqlite3
import pandas as pd
from config import DATABASE_DIR, FEATURES_DATA_DIR

SQLITE_DB_PATH = DATABASE_DIR / "olist.db"

# Pre-aggregate payments and reviews to one row per order_id BEFORE joining
# to orders. Joining the raw (un-aggregated) tables directly would fan out
# rows for orders with multiple payment installments, silently inflating
# averages for customers who happened to pay in installments.
FEATURE_QUERY = """
WITH order_payments AS (
    SELECT order_id, SUM(payment_value) AS order_total_payment
    FROM payments
    GROUP BY order_id
),
order_reviews AS (
    SELECT order_id, AVG(review_score) AS order_review_score
    FROM reviews
    GROUP BY order_id
)
SELECT
    c.customer_unique_id,
    c.customer_state,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(op.order_total_payment) AS total_spent,
    AVG(op.order_total_payment) AS avg_order_value,
    AVG(orv.order_review_score) AS avg_review_score,
    MAX(o.order_purchase_timestamp) AS last_purchase_date,
    MIN(o.order_purchase_timestamp) AS first_purchase_date
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN order_payments op ON o.order_id = op.order_id
LEFT JOIN order_reviews orv ON o.order_id = orv.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_unique_id, c.customer_state;
"""


def build_customer_features():
    FEATURES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SQLITE_DB_PATH)

    print("=" * 80)
    print("BUILDING CUSTOMER-LEVEL RFM FEATURES")
    print("=" * 80)

    df = pd.read_sql_query(FEATURE_QUERY, connection)
    connection.close()

    df["last_purchase_date"] = pd.to_datetime(df["last_purchase_date"])
    df["first_purchase_date"] = pd.to_datetime(df["first_purchase_date"])

    # Recency uses the dataset's own most recent order as the reference
    # point ("snapshot date"), not today's real-world date — this is
    # historical data (2016-2018), so recency relative to today would be
    # meaningless for segmentation.
    snapshot_date = df["last_purchase_date"].max()
    df["recency_days"] = (snapshot_date - df["last_purchase_date"]).dt.days

    df = df.rename(columns={"total_orders": "purchase_frequency"})

    print(f"Snapshot date used for recency: {snapshot_date.date()}")
    print(f"Unique customers: {len(df):,}")
    print(f"\nPurchase frequency distribution:")
    print(df["purchase_frequency"].value_counts().sort_index().to_string())

    repeat_customers = (df["purchase_frequency"] > 1).sum()
    repeat_pct = repeat_customers / len(df) * 100
    print(f"\nCustomers with more than 1 order: {repeat_customers:,} "
          f"({repeat_pct:.2f}% of {len(df):,})")

    output_path = FEATURES_DATA_DIR / "customer_features.parquet"
    df.to_parquet(output_path, index=False)
    print(f"\nFeatures saved to: {output_path}")

    return df


if __name__ == "__main__":
    build_customer_features()