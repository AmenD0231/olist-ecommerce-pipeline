# Olist E-Commerce Analytics Pipeline

An end-to-end data engineering pipeline for the Olist Brazilian
E-Commerce dataset: ingestion, staging/cleaning, relational storage,
data quality validation, feature engineering, customer segmentation,
BI visualization, orchestration, and data versioning.

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

Orchestration (Airflow) and versioning (DVC) wrap around all seven stages.

## Key engineering decisions

| Decision | Reason |
|---|---|
| Dropped PySpark, used pandas throughout | PySpark was never actually used to process data in the original design — only pandas did real work. Kept as-is; PySpark's JVM overhead is unsuited to this hardware. |
| Grouping features by `customer_unique_id`, not `customer_id` | Olist assigns a fresh `customer_id` per order, so grouping by it makes every customer look like a one-time buyer by definition. |
| `polars-lts-cpu` instead of standard `polars` | The dev CPU (Intel Celeron N3350) predates the AVX2/FMA instructions the standard Polars build requires. |
| Airflow executed on GitHub Codespaces, not locally | Airflow has no native Windows support (`os.register_at_fork()` is POSIX-only — see [apache/airflow#10388](https://github.com/apache/airflow/issues/10388)). The DAG was deployed and run end-to-end on GitHub Codespaces with a real Airflow 3.3.1 scheduler. See `docs/orchestration_decision.md` for execution evidence. `run_all.bat` remains available as a local, scheduler-free equivalent for Windows. |
| Payments anomaly documented, not silently fixed | 2 of 103,886 `credit_card` payments have `payment_installments = 0`. Kept as a strict, exported finding (`outputs/reports/payments_data_quality_findings.csv`) rather than loosening the rule to force a pass. |

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
├── airflow/dags/           # Airflow DAG — executed on GitHub Codespaces (see docs/)
├── outputs/
│   ├── figures/            # Generated PNG charts
│   └── reports/            # Validation summaries, cluster profiles, findings
├── docs/
│   ├── orchestration_decision.md
│   └── dag_graph_view_simulated.png
├── notebooks/               # Original exploratory notebook (Steps 1-32)
├── 01_ingest.bat  ...  07_build_charts.bat   # Individual stage runners
├── run_all.bat                                # Full pipeline, one command (Windows, no scheduler)
├── requirements.txt          # Main pipeline dependencies
└── requirements-airflow.txt  # Isolated Airflow environment dependencies
```

## Setup and reproduction

**Requirements:** Python 3.13, a Kaggle account, Windows with PowerShell.

```
git clone <repository-url>
cd olist-pipeline
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Get Kaggle API credentials from https://www.kaggle.com/settings, then run:

```
.\run_all.bat
```

Runs all seven stages in order, prompting once for Kaggle credentials.
To debug one stage at a time, use `01_ingest.bat` through
`07_build_charts.bat` individually.

### Restoring versioned data without re-running the pipeline

```
pip install dvc
dvc pull
```

### Airflow (executed on GitHub Codespaces)

Airflow can't run natively on Windows, so orchestration runs on
[GitHub Codespaces](https://github.com/features/codespaces) instead.
Full details and execution results in `docs/orchestration_decision.md`.

To reproduce:

```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements-airflow.txt --constraint https://raw.githubusercontent.com/apache/airflow/constraints-3.3.1/constraints-3.12.txt

export KAGGLE_USERNAME=<your-username>
export KAGGLE_KEY=<your-api-key>
export AIRFLOW_HOME=~/airflow
airflow standalone

mkdir -p ~/airflow/dags
cp airflow/dags/olist_pipeline_dag.py ~/airflow/dags/
```

Open the forwarded port-8080 URL, log in with `admin` and the
password from `~/airflow/simple_auth_manager_passwords.json.generated`,
un-pause `olist_ecommerce_pipeline`, and trigger it.

> **Note:** Kaggle credentials must be set as environment variables
> *before* starting Airflow — its task subprocesses have no interactive
> stdin, so the credential prompt will hang indefinitely otherwise.

## Results summary

- **9 source tables**, ~1.5M rows, loaded into a foreign-key-enforced SQLite database with zero integrity violations.
- **Data quality**: 6 tables validated against 15 expectations; 1 genuine anomaly found and documented.
- **Segmentation**: 4 customer segments via KMeans (silhouette score 0.395); 2.98% repeat-purchase rate once customers are grouped correctly.
- **Orchestration**: 7-task Airflow DAG executed end-to-end on a real Airflow 3.3.1 scheduler on GitHub Codespaces, all tasks succeeding (2 required one dependency-driven retry each).
- **Reproducibility**: full pipeline runs via a single command (`run_all.bat`) on commodity hardware (Intel Celeron N3350, 4GB RAM); orchestration reproduces on any machine via Codespaces.
