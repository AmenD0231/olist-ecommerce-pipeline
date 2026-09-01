# =============================================================================
# SETUP_STRUCTURE.PY
# =============================================================================
# Purpose:
# Recreate the exact project folder structure originally defined in the
# Colab notebook (Step 3), but rooted locally instead of on Google Drive.
#
# Run this once: python setup_structure.py
# =============================================================================

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent

DIRECTORIES = [
    "data/raw",
    "data/staging",
    "data/processed",
    "data/features",
    "database",
    "src/ingestion",
    "src/transformation",
    "src/feature_engineering",
    "src/validation",
    "airflow/dags",
    "great_expectations",
    "notebooks",
    "outputs/figures",
    "outputs/reports",
    "tests",
    "docs",
    "logs",
]

for directory in DIRECTORIES:
    (PROJECT_ROOT / directory).mkdir(parents=True, exist_ok=True)

print(f"Project structure created successfully at:\n{PROJECT_ROOT}")