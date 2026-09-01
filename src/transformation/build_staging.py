# =============================================================================
# BUILD_STAGING.PY
# =============================================================================
# Purpose:
# Load raw Olist tables, apply the approved structural cleaning rules
# (Step 27), standardize date/time columns (Step 28), and write the
# result to data/staging. Raw data is never modified.
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import pandas as pd
from config import RAW_DATA_DIR, STAGING_DATA_DIR, EXPECTED_TABLES, DATE_COLUMNS


def load_raw_tables() -> dict:
    """Load every expected Olist CSV from data/raw into a dict of DataFrames."""
    tables = {}
    for table_name in EXPECTED_TABLES:
        table_path = RAW_DATA_DIR / table_name
        tables[table_name] = pd.read_csv(table_path)
    return tables


def prepare_staging_table(table_name: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Apply approved structural cleaning rules for one table.
    No statistical imputation — missing values are preserved unless a
    specific structural transformation has already been justified.
    """
    staging_df = dataframe.copy()

    # Geolocation has 261,831 exact duplicate rows; multiple coordinates
    # per postal-code prefix are legitimate, so only true duplicates go.
    if table_name == "olist_geolocation_dataset.csv":
        staging_df = staging_df.drop_duplicates().reset_index(drop=True)

    # Review duplicate IDs belong to different orders — not true dupes.
    if table_name == "olist_order_reviews_dataset.csv":
        staging_df = staging_df.reset_index(drop=True)

    return staging_df


def standardize_dates(table_name: str, dataframe: pd.DataFrame) -> pd.DataFrame:
    """Convert designated date/time columns to proper datetime dtype."""
    typed_df = dataframe.copy()
    if table_name in DATE_COLUMNS:
        for column in DATE_COLUMNS[table_name]:
            typed_df[column] = pd.to_datetime(typed_df[column], errors="coerce")
    return typed_df


def build_staging_layer():
    STAGING_DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("LOADING RAW TABLES")
    print("=" * 80)
    olist_tables = load_raw_tables()
    for name, df in olist_tables.items():
        print(f"{name:<45}{len(df):>12,} rows")

    print("\n" + "=" * 80)
    print("APPLYING STAGING TRANSFORMATIONS")
    print("=" * 80)
    staging_tables = {}
    for table_name, dataframe in olist_tables.items():
        cleaned = prepare_staging_table(table_name, dataframe)
        typed = standardize_dates(table_name, cleaned)
        staging_tables[table_name] = typed

        # Audit: flag if date coercion silently created new NaT values
        # beyond what was already missing in the source.
        if table_name in DATE_COLUMNS:
            for column in DATE_COLUMNS[table_name]:
                original_missing = int(dataframe[column].isna().sum())
                converted_missing = int(typed[column].isna().sum())
                newly_invalid = converted_missing - original_missing
                status = "OK" if newly_invalid == 0 else "REVIEW REQUIRED"
                print(f"  {table_name} / {column}: {status} "
                      f"(newly invalid: {newly_invalid})")

        output_path = STAGING_DATA_DIR / table_name
        typed.to_csv(output_path, index=False)

    print("\n" + "=" * 80)
    print("STAGING LAYER BUILD COMPLETE")
    print("=" * 80)
    for name, df in staging_tables.items():
        rows_removed = len(olist_tables[name]) - len(df)
        print(f"{name:<45}{len(df):>12,} rows  "
              f"(removed: {rows_removed})")

    # Confirm raw files are untouched, as in Step 27.5
    print("\n" + "=" * 80)
    print("RAW DATA INTEGRITY CHECK")
    print("=" * 80)
    for table_name in EXPECTED_TABLES:
        disk_df = pd.read_csv(RAW_DATA_DIR / table_name)
        matches = len(disk_df) == len(olist_tables[table_name])
        print(f"{table_name:<45}{'OK' if matches else 'MISMATCH'}")


if __name__ == "__main__":
    build_staging_layer()