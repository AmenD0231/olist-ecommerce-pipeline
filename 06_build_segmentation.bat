@echo off
REM =============================================================================
REM 06_BUILD_SEGMENTATION.BAT
REM Purpose: Run KMeans customer segmentation on the RFM features.
REM =============================================================================

call venv\Scripts\activate.bat
python src\feature_engineering\build_segmentation.py
pause