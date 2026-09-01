@echo off
REM =============================================================================
REM 07_BUILD_CHARTS.BAT
REM Purpose: Generate BI visualizations from the segmentation results.
REM =============================================================================

call venv\Scripts\activate.bat
python src\visualization\build_charts.py
pause