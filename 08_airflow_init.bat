@echo off
REM =============================================================================
REM 08_AIRFLOW_INIT.BAT
REM Purpose: One-time setup — point Airflow at a project-local home directory
REM and initialize its metadata database. Uses venv-airflow, not the main venv.
REM =============================================================================

set AIRFLOW_HOME=%~dp0airflow
call venv-airflow\Scripts\activate.bat
airflow db migrate
pause