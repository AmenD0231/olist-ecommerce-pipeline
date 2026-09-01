@echo off
REM =============================================================================
REM 05_BUILD_FEATURES.BAT
REM Purpose: Build customer-level RFM features from the database.
REM =============================================================================

call venv\Scripts\activate.bat
python src\feature_engineering\build_features.py
pause