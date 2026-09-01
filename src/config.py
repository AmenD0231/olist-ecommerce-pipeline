# =============================================================================
# CONFIG.PY
# =============================================================================
# Purpose:
# Single source of truth for every path used across the pipeline.
# Every other script imports PROJECT_ROOT and the folder constants from
# here instead of hard-coding paths — this is the local replacement for
# the original Colab config.py, which pointed at Google Drive.
# =============================================================================

from pathlib import Path

# This file lives at src/config.py, so going up one level lands on the
# project root (C:\Projects\olist-pipeline).
PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
STAGING_DATA_DIR = DATA_DIR / "staging"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
FEATURES_DATA_DIR = DATA_DIR / "features"

DATABASE_DIR = PROJECT_ROOT / "database"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
REPORTS_DIR = OUTPUT_DIR / "reports"

LOG_DIR = PROJECT_ROOT / "logs"
AIRFLOW_DIR = PROJECT_ROOT / "airflow"
TESTS_DIR = PROJECT_ROOT / "tests"
DOCS_DIR = PROJECT_ROOT / "docs"

# Kaggle dataset identifier, carried over from Step 18 of the notebook.
KAGGLE_DATASET = "olistbr/brazilian-ecommerce"

# ---------------------------------------------------------------------------
# Expected Olist source tables (from notebook Step 20)
# ---------------------------------------------------------------------------
EXPECTED_TABLES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

# Date/time columns requiring conversion (from notebook Step 28.1)
DATE_COLUMNS = {
    "olist_orders_dataset.csv": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "olist_order_items_dataset.csv": [
        "shipping_limit_date",
    ],
    "olist_order_reviews_dataset.csv": [
        "review_creation_date",
        "review_answer_timestamp",
    ],
}
# ---------------------------------------------------------------------------
# Source CSV -> SQLite table mapping (from notebook Step 30.2)
# ---------------------------------------------------------------------------
SQLITE_TABLE_MAPPING = {
    "olist_customers_dataset.csv": "customers",
    "olist_geolocation_dataset.csv": "geolocation",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "payments",
    "olist_order_reviews_dataset.csv": "reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "product_category_name_translation.csv": "category_translation",
}