# Data Dictionary

## Source tables (SQLite database: `database/olist.db`)

### customers
| Column | Type | Description |
|---|---|---|
| customer_id | TEXT (PK) | Per-order identifier assigned by Olist — NOT a stable person identifier |
| customer_unique_id | TEXT | Stable identifier for the actual customer across multiple orders |
| customer_zip_code_prefix | INTEGER | First 5 digits of customer postal code |
| customer_city | TEXT | Customer city |
| customer_state | TEXT | Customer state (2-letter Brazilian state code) |

### orders
| Column | Type | Description |
|---|---|---|
| order_id | TEXT (PK) | Unique order identifier |
| customer_id | TEXT (FK -> customers) | Links to the per-order customer record |
| order_status | TEXT | One of: delivered, shipped, canceled, unavailable, invoiced, processing, created, approved |
| order_purchase_timestamp | TEXT (ISO datetime) | When the order was placed |
| order_approved_at | TEXT (ISO datetime, nullable) | When payment was approved |
| order_delivered_carrier_date | TEXT (ISO datetime, nullable) | When handed to the logistics partner |
| order_delivered_customer_date | TEXT (ISO datetime, nullable) | When the customer received the order |
| order_estimated_delivery_date | TEXT (ISO datetime) | Estimated delivery date shown to the customer |

### order_items
| Column | Type | Description |
|---|---|---|
| order_id | TEXT (PK part, FK -> orders) | Order this line item belongs to |
| order_item_id | INTEGER (PK part) | Sequence number within the order |
| product_id | TEXT (FK -> products) | Product purchased |
| seller_id | TEXT (FK -> sellers) | Seller fulfilling this item |
| shipping_limit_date | TEXT (ISO datetime) | Seller's shipping deadline |
| price | REAL | Item price (excludes freight) |
| freight_value | REAL | Shipping cost for this item |

### payments
| Column | Type | Description |
|---|---|---|
| order_id | TEXT (PK part, FK -> orders) | Order this payment applies to |
| payment_sequential | INTEGER (PK part) | Sequence if an order used multiple payment methods |
| payment_type | TEXT | credit_card, boleto, voucher, debit_card, or not_defined |
| payment_installments | INTEGER | Number of installments (expected >= 1; see data quality findings) |
| payment_value | REAL | Amount paid via this payment record |

### reviews
| Column | Type | Description |
|---|---|---|
| review_record_id | INTEGER (PK, surrogate) | Added during loading — the source `review_id` is not unique per row |
| review_id | TEXT | Original Olist review identifier |
| order_id | TEXT (FK -> orders) | Order being reviewed |
| review_score | INTEGER | 1-5 star rating |
| review_comment_title | TEXT (nullable) | Optional review title |
| review_comment_message | TEXT (nullable) | Optional review text |
| review_creation_date | TEXT (ISO datetime) | When the review was submitted |
| review_answer_timestamp | TEXT (ISO datetime) | When Olist's survey response was recorded |

### products
| Column | Type | Description |
|---|---|---|
| product_id | TEXT (PK) | Unique product identifier |
| product_category_name | TEXT (nullable) | Category in Portuguese |
| product_name_lenght | REAL (nullable) | Character count of product name |
| product_description_lenght | REAL (nullable) | Character count of product description |
| product_photos_qty | REAL (nullable) | Number of product photos |
| product_weight_g | REAL (nullable) | Product weight in grams |
| product_length_cm / product_height_cm / product_width_cm | REAL (nullable) | Package dimensions |

### sellers
| Column | Type | Description |
|---|---|---|
| seller_id | TEXT (PK) | Unique seller identifier |
| seller_zip_code_prefix | INTEGER | First 5 digits of seller postal code |
| seller_city | TEXT | Seller city |
| seller_state | TEXT | Seller state |

### geolocation
| Column | Type | Description |
|---|---|---|
| geolocation_zip_code_prefix | INTEGER | Postal code prefix (many-to-many with lat/lng — multiple valid coordinates per prefix are legitimate, not duplicates) |
| geolocation_lat / geolocation_lng | REAL | Coordinates |
| geolocation_city / geolocation_state | TEXT | Location names |

### category_translation
| Column | Type | Description |
|---|---|---|
| product_category_name | TEXT (PK) | Category name in Portuguese |
| product_category_name_english | TEXT | English translation |

## Derived features (`data/features/customer_features.parquet`)

Grouped by `customer_unique_id` — the actual person, not the per-order `customer_id`.

| Column | Description |
|---|---|
| customer_unique_id | Stable customer identifier |
| customer_state | Customer's state |
| purchase_frequency | Count of distinct delivered orders |
| total_spent | Sum of all payment amounts across the customer's orders |
| avg_order_value | Average payment amount per order |
| avg_review_score | Mean review score across the customer's orders (nullable if unreviewed) |
| last_purchase_date / first_purchase_date | Order timestamp bounds |
| recency_days | Days between this customer's last order and the dataset's most recent order (2018-08-29) — recency is relative to the dataset, not the real-world current date, since this is historical 2016-2018 data |

## Derived segmentation (`data/features/customer_segments.parquet`)

Adds a `cluster` column (0-3) from KMeans (k=4, `random_state=42`) fit
on standardized `recency_days`, `purchase_frequency`, `total_spent`,
and `avg_review_score`. See `outputs/reports/cluster_profiles.csv`
for per-cluster means; cluster interpretation and naming is discussed
in the main report's Results section.
