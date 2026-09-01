# =============================================================================
# VALIDATE_DATABASE.PY
# =============================================================================
# Purpose:
# Run a Great Expectations validation suite against each table in the
# SQLite database, formalizing both the structural checks already proven
# in Step 31 (PK/FK integrity) and new business-rule checks (valid status
# values, review scores in range, non-negative prices) that the raw SQL
# checks never covered.
#
# Uses the Great Expectations 1.x fluent API throughout:
#   context.data_sources.add_pandas()  (NOT the old context.sources.*)
#   gx.expectations.Expect...() objects (NOT the old expect_* dict style)
# =============================================================================

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import sqlite3
import pandas as pd
import great_expectations as gx
from config import DATABASE_DIR, REPORTS_DIR, PROJECT_ROOT

SQLITE_DB_PATH = DATABASE_DIR / "olist.db"

# ---------------------------------------------------------------------------
# One expectation-building function per table. Each returns a list of
# gx.expectations objects. Keeping these as small functions (rather than
# one giant script) makes it easy to add more checks per table later.
# ---------------------------------------------------------------------------

def customers_expectations():
    return [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="customer_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="customer_id"),
        gx.expectations.ExpectColumnValueLengthsToEqual(column="customer_state", value=2),
    ]

def orders_expectations():
    return [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
        gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="order_status",
            value_set=["delivered", "shipped", "canceled", "unavailable",
                       "invoiced", "processing", "created", "approved"],
        ),
    ]

def order_items_expectations():
    return [
        gx.expectations.ExpectColumnValuesToNotBeNull(column="product_id"),
        gx.expectations.ExpectColumnValuesToBeBetween(column="price", min_value=0),
        gx.expectations.ExpectColumnValuesToBeBetween(column="freight_value", min_value=0),
    ]

def payments_expectations():
    return [
        gx.expectations.ExpectColumnValuesToBeBetween(column="payment_value", min_value=0),
        gx.expectations.ExpectColumnValuesToBeBetween(column="payment_installments", min_value=1),
        gx.expectations.ExpectColumnValuesToBeInSet(
            column="payment_type",
            value_set=["credit_card", "boleto", "voucher", "debit_card", "not_defined"],
        ),
    ]

def reviews_expectations():
    return [
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="review_score", min_value=1, max_value=5
        ),
        gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"),
    ]

def products_expectations():
    return [
        gx.expectations.ExpectColumnValuesToBeBetween(
            column="product_weight_g", min_value=0, mostly=0.99
        ),
    ]

# Table name -> (expectation builder function)
TABLE_EXPECTATIONS = {
    "customers": customers_expectations,
    "orders": orders_expectations,
    "order_items": order_items_expectations,
    "payments": payments_expectations,
    "reviews": reviews_expectations,
    "products": products_expectations,
}


def run_validation():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    # File-based context persists suite/config under great_expectations/,
    # so results and configuration survive between runs.
    # Ephemeral context: fully in-memory, nothing persisted to disk between
    # runs. This makes the script safe to re-run repeatedly without hitting
    # "resource already exists" errors — each run starts clean.
    context = gx.get_context(mode="ephemeral")

    connection = sqlite3.connect(SQLITE_DB_PATH)

    data_source = context.data_sources.add_pandas(name="olist_sqlite_tables")

    overall_results = []

    for table_name, expectation_builder in TABLE_EXPECTATIONS.items():
        print("=" * 80)
        print(f"VALIDATING: {table_name}")
        print("=" * 80)

        df = pd.read_sql_query(f"SELECT * FROM {table_name};", connection)

        data_asset = data_source.add_dataframe_asset(name=f"{table_name}_asset")
        batch_definition = data_asset.add_batch_definition_whole_dataframe(
            f"{table_name}_batch_def"
        )
        batch = batch_definition.get_batch(batch_parameters={"dataframe": df})

        suite = gx.ExpectationSuite(name=f"{table_name}_suite")
        suite = context.suites.add(suite)

        for expectation in expectation_builder():
            suite.add_expectation(expectation)

        validation_definition = context.validation_definitions.add(
            gx.core.validation_definition.ValidationDefinition(
                name=f"{table_name}_validation",
                data=batch_definition,
                suite=suite,
            )
        )

        result = validation_definition.run(batch_parameters={"dataframe": df})

        passed = result.success
        n_expectations = len(result.results)
        n_passed = sum(1 for r in result.results if r.success)

        print(f"  Rows checked: {len(df):,}")
        print(f"  Expectations: {n_passed}/{n_expectations} passed")
        print(f"  Overall: {'PASSED' if passed else 'FAILED'}")

        if not passed:
            for r in result.results:
                if not r.success:
                    print(f"    FAILED: {r.expectation_config.type} "
                          f"on column '{r.expectation_config.kwargs.get('column')}'")

            # Document the exact offending rows as a data quality finding,
            # rather than silently loosening the expectation to pass.
            failing_rows = df.copy()
            for r in result.results:
                if not r.success and r.expectation_config.kwargs.get("column"):
                    col = r.expectation_config.kwargs["column"]
                    kwargs = r.expectation_config.kwargs
                    if "min_value" in kwargs and kwargs["min_value"] is not None:
                        failing_rows = failing_rows[failing_rows[col] < kwargs["min_value"]]

            findings_path = REPORTS_DIR / f"{table_name}_data_quality_findings.csv"
            failing_rows.to_csv(findings_path, index=False)
            print(f"    {len(failing_rows)} offending row(s) saved to: {findings_path}")

        overall_results.append({
            "table": table_name,
            "rows_checked": len(df),
            "expectations_passed": n_passed,
            "expectations_total": n_expectations,
            "status": "PASSED" if passed else "FAILED",
        })

    connection.close()

    print("\n" + "=" * 80)
    print("VALIDATION SUMMARY")
    print("=" * 80)
    summary_df = pd.DataFrame(overall_results)
    print(summary_df.to_string(index=False))

    summary_path = REPORTS_DIR / "validation_summary.csv"
    summary_df.to_csv(summary_path, index=False)
    print(f"\nSummary saved to: {summary_path}")


if __name__ == "__main__":
    run_validation()