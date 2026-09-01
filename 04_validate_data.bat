@echo off
REM =============================================================================
REM 04_VALIDATE_DATA.BAT
REM Purpose: Run the Great Expectations validation suite against the database.
REM =============================================================================

call venv\Scripts\activate.bat
python src\validation\validate_database.py
pause