@echo off
REM =============================================================================
REM RUN_ALL.BAT
REM Purpose: Local orchestrator substitute for Airflow (see
REM docs/orchestration_decision.md). Runs all 7 pipeline stages in
REM dependency order within a single venv session.
REM =============================================================================

call venv\Scripts\activate.bat

echo ============================================================
echo STAGE 1/7: Kaggle ingestion
echo ============================================================
python src\ingestion\download_dataset.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 2/7: Staging and cleaning
echo ============================================================
python src\transformation\build_staging.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 3/7: SQLite database build
echo ============================================================
python src\storage\build_database.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 4/7: Great Expectations validation
echo ============================================================
python src\validation\validate_database.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 5/7: Feature engineering
echo ============================================================
python src\feature_engineering\build_features.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 6/7: KMeans segmentation
echo ============================================================
python src\feature_engineering\build_segmentation.py
if errorlevel 1 goto :error

echo ============================================================
echo STAGE 7/7: BI visualizations
echo ============================================================
python src\visualization\build_charts.py
if errorlevel 1 goto :error

echo ============================================================
echo PIPELINE COMPLETE - ALL 7 STAGES SUCCEEDED
echo ============================================================
goto :end

:error
echo ============================================================
echo PIPELINE FAILED - see error above
echo ============================================================

:end
pause