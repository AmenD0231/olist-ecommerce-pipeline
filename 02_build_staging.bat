@echo off
REM =============================================================================
REM 02_BUILD_STAGING.BAT
REM Purpose: Run the staging/cleaning stage on its own.
REM =============================================================================

call venv\Scripts\activate.bat
python src\transformation\build_staging.py
pause