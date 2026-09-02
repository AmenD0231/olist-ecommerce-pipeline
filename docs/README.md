# Olist E-Commerce Analytics Pipeline

An end-to-end data engineering pipeline for the Olist Brazilian
E-Commerce dataset: ingestion, staging/cleaning, relational storage,
data quality validation, feature engineering, customer segmentation,
BI visualization, orchestration design, and data versioning.

## Architecture

```
Kaggle API
    |
    v
[1] Ingestion --------------> data/raw/*.csv (9 tables)
    |
    v
[2] Staging & Cleaning ------> data/staging/*.csv
    |
    v
[3] SQLite Database Build ---> database/olist.db (9 tables, indexed, FK-enforced)
    |
    v
[4] Great Expectations ------> outputs/reports/validation_summary.csv
    |                          outputs/reports/*_data_quality_findings.csv
    v
[5] Feature Engineering -----> data/features/customer_features.parquet
    |
    v
[6] KMeans Segmentation -----> data/features/customer_segments.parquet
    |                          outputs/reports/cluster_profiles.csv
    v
[7] BI Visualization --------> outputs/figures/*.png
```

Orchestration (Airflow) and versioning (DVC) wrap around all seven
stages — see below.

## Key engineering decisions

These are documented here rather than only in code comments, since
they materially affect how the project should be read:

| Decision | Reason |
|---|---|
| Dropped PySpark, used pandas throughout | The original design referenced PySpark, but it was never actually used to process data (`spark.read`, `.toPandas()` never appear) — only pandas did real work. Kept as-is locally; PySpark would add JVM overhead unsuited to this hardware. |
| Grouping features by `customer_unique_id`, not `customer_id` | Olist assigns a fresh `customer_id` per order. Grouping by it makes every customer look like a one-time buyer by definition. `customer_unique_id` identifies the actual person. |
| `polars-lts-cpu` instead of standard `polars` | The development CPU (Intel Celeron N3350) predates the AVX2/FMA instruction sets the standard Polars build requires; the standard build would crash on real computation, not just warn. |
| Airflow designed but not executed | Apache Airflow has no native Windows support (calls `os.register_at_fork()`, a POSIX-only function, at import time — see [apache/airflow#10388](https://github.com/apache/airflow/issues/10388)). Full justification, DAG code, and a simulated Graph View diagram are in `docs/orchestration_decision.md`. `run_all.bat` provides equivalent local sequencing. |
| Great Expectations payments anomaly kept as a documented finding, not silently fixed | 2 of 103,886 `credit_card` payments have `payment_installments = 0`, which has no valid business interpretation. The expectation was kept strict and the affected rows exported to `outputs/reports/payments_data_quality_findings.csv` rather than loosening the rule to force a pass. |

## Project structure

```
olist-pipeline/
├── data/
│   ├── raw/              # DVC-tracked: original Kaggle CSVs
│   ├── staging/          # Cleaned, date-standardized CSVs
│   └── features/         # DVC-tracked: RFM features + cluster assignments
├── database/
│   └── olist.db          # DVC-tracked: SQLite relational database
├── src/
│   ├── config.py          # Central path/constant configuration
│   ├── ingestion/          # Kaggle auth + download
│   ├── transformation/     # Staging/cleaning logic
│   ├── storage/            # SQLite schema, load, integrity checks
│   ├── validation/         # Great Expectations suite
│   ├── feature_engineering/ # RFM features + KMeans segmentation
│   └── visualization/      # BI chart generation
├── airflow/dags/           # Airflow DAG (designed, not executed — see docs/)
├── outputs/
│   ├── figures/            # Generated PNG charts
│   └── reports/            # Validation summaries, cluster profiles, findings
├── docs/
│   ├── orchestration_decision.md
│   └── dag_graph_view_simulated.png
├── notebooks/               # Original exploratory notebook (Steps 1-32)
├── 01_ingest.bat  ...  07_build_charts.bat   # Individual stage runners
├── run_all.bat                                # Full pipeline, one command
├── requirements.txt          # Main pipeline dependencies
└── requirements-airflow.txt  # Isolated Airflow environment dependencies
```

## Setup and reproduction

**Requirements:** Python 3.13, a Kaggle account (for API credentials),
Windows with PowerShell.

```
git clone <repository-url>
cd olist-pipeline
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Get Kaggle API credentials from https://www.kaggle.com/settings, then
run the full pipeline:

```
.\run_all.bat
```

This runs all seven stages in dependency order, prompting once for
Kaggle credentials at the start. To run stages individually instead
(useful for debugging one stage), use `01_ingest.bat` through
`07_build_charts.bat` in order.

### Restoring versioned data without re-running the pipeline

Since raw data, the database, and feature outputs are DVC-tracked:

```
pip install dvc
dvc pull
```

retrieves the exact data used to produce the results in this
repository, without needing to re-download from Kaggle or
re-run any processing.

### Airflow (designed, not executed on Windows)

See `docs/orchestration_decision.md` for the full explanation.
The DAG can be reviewed at `airflow/dags/olist_pipeline_dag.py` and
would run correctly on Linux or WSL2 with:

```
pip install -r requirements-airflow.txt
airflow db migrate
airflow dags test olist_ecommerce_pipeline 2024-01-01
```

## Results summary

- **9 source tables**, ~1.5M rows total, loaded into a foreign-key-enforced SQLite database with zero integrity violations.
- **Data quality**: 6 tables validated against 15 expectations; 1 genuine anomaly found and documented (not hidden).
- **Segmentation**: 4 customer segments identified via KMeans (silhouette score 0.395), revealing a 2.98% repeat-purchase rate — a meaningfully low but real figure once customers are grouped correctly.
- **Reproducibility**: full pipeline runs end-to-end via a single command (`run_all.bat`) on commodity low-spec hardware (Intel Celeron N3350, 4GB RAM).
