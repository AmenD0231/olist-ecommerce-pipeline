# =============================================================================
# BUILD_DATABASE.PY
# =============================================================================
# Purpose:
# Build the SQLite relational database from the staging layer: create
# schema, load data in dependency order, validate PK/FK integrity, and
# create performance indexes. Ported from notebook Steps 29-32.
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import sqlite3
import pandas as pd
from config import (
    DATABASE_DIR, STAGING_DATA_DIR, RAW_DATA_DIR,
    EXPECTED_TABLES, DATE_COLUMNS, SQLITE_TABLE_MAPPING,
)

SQLITE_DB_PATH = DATABASE_DIR / "olist.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT NOT NULL,
    customer_zip_code_prefix INTEGER NOT NULL,
    customer_city TEXT NOT NULL,
    customer_state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix INTEGER NOT NULL,
    geolocation_lat REAL NOT NULL,
    geolocation_lng REAL NOT NULL,
    geolocation_city TEXT NOT NULL,
    geolocation_state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TEXT NOT NULL,
    order_approved_at TEXT,
    order_delivered_carrier_date TEXT,
    order_delivered_customer_date TEXT,
    order_estimated_delivery_date TEXT NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght REAL,
    product_description_lenght REAL,
    product_photos_qty REAL,
    product_weight_g REAL,
    product_length_cm REAL,
    product_height_cm REAL,
    product_width_cm REAL
);

CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix INTEGER NOT NULL,
    seller_city TEXT NOT NULL,
    seller_state TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    seller_id TEXT NOT NULL,
    shipping_limit_date TEXT NOT NULL,
    price REAL NOT NULL,
    freight_value REAL NOT NULL,
    PRIMARY KEY (order_id, order_item_id),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    FOREIGN KEY (seller_id) REFERENCES sellers(seller_id)
);

CREATE TABLE IF NOT EXISTS payments (
    order_id TEXT NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type TEXT NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value REAL NOT NULL,
    PRIMARY KEY (order_id, payment_sequential),
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS reviews (
    review_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    review_score INTEGER NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TEXT NOT NULL,
    review_answer_timestamp TEXT NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);

CREATE TABLE IF NOT EXISTS category_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT NOT NULL
);
"""

LOAD_ORDER = [
    "customers", "products", "sellers", "category_translation",
    "geolocation", "orders", "order_items", "payments", "reviews",
]

PRIMARY_KEY_DEFINITIONS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
    "category_translation": ["product_category_name"],
    "order_items": ["order_id", "order_item_id"],
    "payments": ["order_id", "payment_sequential"],
    "reviews": ["review_record_id"],
}

FOREIGN_KEY_RELATIONSHIPS = [
    ("orders", "customer_id", "customers", "customer_id"),
    ("order_items", "order_id", "orders", "order_id"),
    ("order_items", "product_id", "products", "product_id"),
    ("order_items", "seller_id", "sellers", "seller_id"),
    ("payments", "order_id", "orders", "order_id"),
    ("reviews", "order_id", "orders", "order_id"),
]

INDEX_DEFINITIONS = {
    "idx_orders_customer_id": "CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);",
    "idx_orders_status": "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status);",
    "idx_orders_purchase_timestamp": "CREATE INDEX IF NOT EXISTS idx_orders_purchase_timestamp ON orders(order_purchase_timestamp);",
    "idx_order_items_product_id": "CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);",
    "idx_order_items_seller_id": "CREATE INDEX IF NOT EXISTS idx_order_items_seller_id ON order_items(seller_id);",
    "idx_order_items_order_id": "CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);",
    "idx_payments_order_id": "CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);",
    "idx_payments_type": "CREATE INDEX IF NOT EXISTS idx_payments_type ON payments(payment_type);",
    "idx_reviews_order_id": "CREATE INDEX IF NOT EXISTS idx_reviews_order_id ON reviews(order_id);",
    "idx_reviews_score": "CREATE INDEX IF NOT EXISTS idx_reviews_score ON reviews(review_score);",
    "idx_products_category": "CREATE INDEX IF NOT EXISTS idx_products_category ON products(product_category_name);",
    "idx_geolocation_zip": "CREATE INDEX IF NOT EXISTS idx_geolocation_zip ON geolocation(geolocation_zip_code_prefix);",
}


def load_staging_tables() -> dict:
    tables = {}
    for table_name in EXPECTED_TABLES:
        path = STAGING_DATA_DIR / table_name
        df = pd.read_csv(path)
        # Re-parse date columns — CSV round-tripping loses datetime dtype.
        if table_name in DATE_COLUMNS:
            for col in DATE_COLUMNS[table_name]:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        tables[table_name] = df
    return tables


def prepare_for_sqlite(staging_tables: dict) -> dict:
    """Convert datetimes to ISO strings and add the review surrogate key."""
    sqlite_tables = {}
    for table_name, df in staging_tables.items():
        sdf = df.copy()
        if table_name in DATE_COLUMNS:
            for col in DATE_COLUMNS[table_name]:
                sdf[col] = sdf[col].apply(
                    lambda v: v.isoformat(sep=" ") if pd.notna(v) else None
                )
        sqlite_tables[table_name] = sdf

    reviews_key = "olist_order_reviews_dataset.csv"
    reviews_df = sqlite_tables[reviews_key].copy()
    reviews_df.insert(0, "review_record_id", range(1, len(reviews_df) + 1))
    sqlite_tables[reviews_key] = reviews_df

    return sqlite_tables


def build_database():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(SQLITE_DB_PATH)
    connection.execute("PRAGMA foreign_keys = ON;")

    print("=" * 80)
    print("CREATING SCHEMA")
    print("=" * 80)
    connection.executescript(SCHEMA_SQL)
    connection.commit()
    print(f"Database ready at: {SQLITE_DB_PATH}")

    print("\n" + "=" * 80)
    print("LOADING STAGING DATA")
    print("=" * 80)
    staging_tables = load_staging_tables()
    sqlite_tables = prepare_for_sqlite(staging_tables)

    source_by_sqlite_table = {v: k for k, v in SQLITE_TABLE_MAPPING.items()}
    BATCH_SIZE = 1_000

    # Delete children before parents so FK constraints are never violated,
    # regardless of whether tables are empty or hold data from a prior run.
    for sqlite_table in reversed(LOAD_ORDER):
        connection.execute(f"DELETE FROM {sqlite_table};")
    connection.commit()

    for sqlite_table in LOAD_ORDER:
        source_table = source_by_sqlite_table[sqlite_table]
        df = sqlite_tables[source_table]
        for start in range(0, len(df), BATCH_SIZE):
            batch = df.iloc[start:start + BATCH_SIZE]
            batch.to_sql(sqlite_table, connection, if_exists="append", index=False)
        connection.commit()
        count = connection.execute(f"SELECT COUNT(*) FROM {sqlite_table};").fetchone()[0]
        print(f"{sqlite_table:<25}{count:>12,} rows loaded")

    # --- Row-count reconciliation: RAW -> STAGING -> SQLITE ---
    print("\n" + "=" * 80)
    print("ROW-COUNT RECONCILIATION (RAW -> STAGING -> SQLITE)")
    print("=" * 80)
    for source_table, sqlite_table in SQLITE_TABLE_MAPPING.items():
        raw_count = len(pd.read_csv(RAW_DATA_DIR / source_table))
        staging_count = len(staging_tables[source_table])
        sqlite_count = connection.execute(f"SELECT COUNT(*) FROM {sqlite_table};").fetchone()[0]
        match = "OK" if staging_count == sqlite_count else "MISMATCH"
        print(f"{sqlite_table:<22} raw={raw_count:>9,}  staging={staging_count:>9,}  "
              f"sqlite={sqlite_count:>9,}  [{match}]")

    # --- Primary-key integrity ---
    print("\n" + "=" * 80)
    print("PRIMARY-KEY INTEGRITY")
    print("=" * 80)
    for table, keys in PRIMARY_KEY_DEFINITIONS.items():
        key_expr = ", ".join(keys)
        total = connection.execute(f"SELECT COUNT(*) FROM {table};").fetchone()[0]
        distinct = connection.execute(
            f"SELECT COUNT(*) FROM (SELECT {key_expr} FROM {table} GROUP BY {key_expr});"
        ).fetchone()[0]
        status = "VALID" if total == distinct else "REVIEW REQUIRED"
        print(f"{table:<22}{status:<18}(total={total:,}, distinct={distinct:,})")

    # --- Foreign-key integrity ---
    print("\n" + "=" * 80)
    print("FOREIGN-KEY INTEGRITY")
    print("=" * 80)
    for child_table, child_col, parent_table, parent_col in FOREIGN_KEY_RELATIONSHIPS:
        orphans = connection.execute(f"""
            SELECT COUNT(*) FROM (
                SELECT DISTINCT c.{child_col} FROM {child_table} AS c
                LEFT JOIN {parent_table} AS p ON c.{child_col} = p.{parent_col}
                WHERE p.{parent_col} IS NULL
            );
        """).fetchone()[0]
        status = "VALID" if orphans == 0 else "REVIEW REQUIRED"
        print(f"{child_table}.{child_col:<20} -> {parent_table}.{parent_col:<20} [{status}] orphans={orphans}")

    violations = pd.read_sql_query("PRAGMA foreign_key_check;", connection)
    print(f"\nSQLite native foreign_key_check violations: {len(violations)}")

    # --- Indexes ---
    print("\n" + "=" * 80)
    print("CREATING INDEXES")
    print("=" * 80)
    for name, sql in INDEX_DEFINITIONS.items():
        connection.execute(sql)
    connection.commit()
    index_count = connection.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%';"
    ).fetchone()[0]
    print(f"Indexes created/verified: {index_count}")

    connection.close()
    print("\n" + "=" * 80)
    print("DATABASE BUILD COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    build_database()