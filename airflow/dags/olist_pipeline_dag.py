# =============================================================================
# OLIST_PIPELINE_DAG.PY
# =============================================================================
# STATUS: Designed and code-reviewed on Windows; executed successfully on
# GitHub Codespaces (Linux).
#
# Apache Airflow has no native Windows support: it calls
# os.register_at_fork() unconditionally at import time, a POSIX-only
# function absent from Windows' os module in every Python version.
# See https://github.com/apache/airflow/issues/10388 (open since 2020).
# Given this project's hardware (Intel Celeron N3350, 4GB RAM), running
# Airflow locally via WSL2 was assessed as disproportionate setup risk
# relative to the marks available. The DAG was therefore first
# demonstrated as validated, code-reviewed code plus a local equivalent,
# run_all.bat, performing the same task sequencing and dependency
# ordering without the Airflow scheduler/webserver.
#
# To provide a genuine execution trace rather than a static artifact,
# this same DAG (unmodified apart from OS-appropriate paths below) was
# subsequently deployed and run end-to-end on GitHub Codespaces, a
# cloud-hosted Linux environment. This sidesteps the Windows
# incompatibility entirely and avoids the local machine's RAM
# constraint, since execution happens on Codespaces' own compute rather
# than the Celeron N3350.
#
# Each task shells out to the pipeline's main virtual environment
# (venv, NOT a separate Airflow venv) via subprocess. Airflow's own
# environment deliberately does not carry pandas/scikit-learn/Great
# Expectations - keeping its dependency footprint minimal was itself a
# resource decision suited to this hardware.
# =============================================================================

import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from airflow.sdk import dag, task

PROJECT_ROOT = Path("/workspaces/olist-ecommerce-pipeline")
VENV_PYTHON = str(PROJECT_ROOT / "venv" / "bin" / "python")


def run_stage(script_relative_path: str) -> None:
    """Run one pipeline stage using the main venv's Python interpreter.
    Raises on non-zero exit so Airflow marks the task failed and applies
    the retry policy below before alerting."""
    script_path = str(PROJECT_ROOT / script_relative_path)
    result = subprocess.run(
        [VENV_PYTHON, script_path],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError(
            f"{script_relative_path} failed with exit code {result.returncode}"
        )


@dag(
    dag_id="olist_ecommerce_pipeline",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args={
        "retries": 2,        # Retry transient failures (e.g. Kaggle API
                              # timeouts) twice before alerting.
        "retry_delay": timedelta(minutes=5),
    },
    tags=["olist", "e-commerce", "data-engineering"],
)
def olist_ecommerce_pipeline():

    @task
    def ingest():
        run_stage("src/ingestion/download_dataset.py")

    @task
    def build_staging():
        run_stage("src/transformation/build_staging.py")

    @task
    def build_database():
        run_stage("src/storage/build_database.py")

    @task
    def validate_data():
        run_stage("src/validation/validate_database.py")

    @task
    def build_features():
        run_stage("src/feature_engineering/build_features.py")

    @task
    def build_segmentation():
        run_stage("src/feature_engineering/build_segmentation.py")

    @task
    def build_charts():
        run_stage("src/visualization/build_charts.py")

    # Linear dependency chain, matching the real data dependencies:
    # each stage reads the previous stage's output.
    (
        ingest()
        >> build_staging()
        >> build_database()
        >> validate_data()
        >> build_features()
        >> build_segmentation()
        >> build_charts()
    )


olist_ecommerce_pipeline()
