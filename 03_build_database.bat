@echo off
REM =============================================================================
REM 03_BUILD_DATABASE.BAT
REM Purpose: Build the SQLite database, validate integrity, and index it.
REM =============================================================================

call venv\Scripts\activate.bat
python src\storage\build_database.py
pause