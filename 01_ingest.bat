@echo off
REM =============================================================================
REM 01_INGEST.BAT
REM Purpose: Activate the venv and run the Kaggle ingestion stage on its own,
REM so it doesn't share memory with any other pipeline stage.
REM =============================================================================

call venv\Scripts\activate.bat
python src\ingestion\download_dataset.py
pause